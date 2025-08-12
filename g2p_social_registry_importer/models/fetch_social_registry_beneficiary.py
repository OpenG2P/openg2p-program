import json
import logging
import uuid
from datetime import datetime, timezone

import jq
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.queue_job.delay import group

from ..models import constants

_logger = logging.getLogger(__name__)


class G2PFetchSocialRegistryBeneficiary(models.Model):
    _name = "g2p.fetch.social.registry.beneficiary"
    _description = "Fetch Social Registry Beneficiary"

    data_source_id = fields.Many2one("spp.data.source", required=True)

    name = fields.Char(required=True)

    import_registrant_without_id = fields.Boolean("Import Registrant without ID", default=False)

    target_registry = fields.Selection(
        [("group", "Group"), ("individual", "Individual")],
        required=True,
    )

    target_program = fields.Many2one(
        "g2p.program",
        domain=("[('target_type', '=', target_registry)]"),
    )
    query_params = fields.Text(default="""{}""")
    query = fields.Text(required=True, default="""{}""")
    output_mapping = fields.Text(required=True, default="""{}""")

    last_sync_date = fields.Datetime(string="Last synced on", required=False)

    imported_registrant_ids = fields.One2many(
        "g2p.social.registry.imported.registrants",
        "fetch_social_registry_id",
        "Imported Registrants",
        readonly=True,
    )

    job_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("started", "Started"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="draft",
    )

    start_datetime = fields.Datetime("Start Time")
    end_datetime = fields.Datetime("End Time")
    cron_id = fields.Many2one("ir.cron", string="Cron Job")

    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection(
        [
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        string="Interval Unit",
        default="hours",
    )
    cron_running = fields.Boolean(compute="_compute_cron_running")

    def test_connection(self):
        """Test the connection to the Social Registry API by validating:
        1. Data source configuration
        2. Authentication endpoints
        3. Authentication credentials
        4. Successful token retrieval
        """
        self.ensure_one()
        try:
            # Step 1: Validate data source configuration
            if not self.data_source_id:
                raise Exception(_("Data source is not configured"))

            if not self.data_source_id.url:
                raise Exception(_("Data source URL is not configured"))

            # Step 2: Get and validate paths
            paths = self.get_data_source_paths()
            auth_url = self.get_social_registry_auth_url(paths)

            # Step 3: Validate required credentials
            client_id = (
                self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_id")
            )
            client_secret = (
                self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_password")
            )
            grant_type = (
                self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.grant_type")
            )

            if not all([client_id, client_secret, grant_type]):
                raise Exception(_("Missing credentials: Please configure client ID, secret and grant type"))

            # Step 4: Test authentication
            auth_token = self.get_auth_token(auth_url)
            if not auth_token:
                raise Exception(_("Authentication failed: No token received"))

            # If we get here, all checks passed
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Connection Test"),
                    "message": _("Successfully connected to Social Registry API and authenticated"),
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as e:
            _logger.error("Error during connection test: %s", str(e), exc_info=True)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Connection Test Failed"),
                    "message": str(e),
                    "type": "danger",
                    "sticky": True,
                },
            }

    @api.onchange("registry")
    def onchange_target_registry(self):
        for rec in self:
            rec.target_program = None

    @api.constrains("query_params")
    def _validate_query_params(self):
        for rec in self:
            if rec.query_params:
                try:
                    json.loads(rec.query_params)
                except json.JSONDecodeError as e:
                    raise ValidationError(_("Query Parameters must be valid JSON. Error: %s") % str(e)) from e

    def get_parsed_query_params(self):
        """Parse query_params JSON and return as dict"""
        self.ensure_one()
        try:
            return json.loads(self.query_params) if self.query_params else {}
        except json.JSONDecodeError:
            _logger.error("Invalid JSON in query_params for record %s", self.id)
            return {}

    @api.constrains("output_mapping")
    def constraint_json_fields(self):
        for rec in self:
            if rec.output_mapping:
                try:
                    # Validate the JSON Query (jq expression)
                    jq.compile(rec.output_mapping)
                except ValueError as ve:
                    raise ValidationError(
                        _("The provided value for 'Output Mapping' is not a valid jq expression.")
                    ) from ve

    def get_data_source_paths(self):
        self.ensure_one()

        paths = {}

        for path_id in self.data_source_id.data_source_path_ids:
            paths[path_id.key] = path_id.value

        if constants.DATA_SOURCE_SEARCH_PATH_NAME not in paths:
            raise ValidationError(
                _("No path in data source named {path} is configured!").format(
                    path=constants.DATA_SOURCE_SEARCH_PATH_NAME
                )
            )

        if constants.DATA_SOURCE_AUTH_PATH_NAME not in paths:
            raise ValidationError(
                _("No path in data source named {path} is configured!").format(
                    path=constants.DATA_SOURCE_AUTH_PATH_NAME
                )
            )

        return paths

    def get_social_registry_search_url(self, paths):
        url = self.data_source_id.url
        search_path = paths.get(constants.DATA_SOURCE_SEARCH_PATH_NAME)

        return f"{url}{search_path}"

    def get_social_registry_auth_url(self, paths):
        url = self.data_source_id.url
        auth_path = paths.get(constants.DATA_SOURCE_AUTH_PATH_NAME)

        if auth_path.lstrip().startswith("/"):
            return f"{url}{auth_path}"

        else:
            return auth_path

    def get_auth_token(self, auth_url):
        client_id = self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_id")
        client_secret = (
            self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_password")
        )
        grant_type = self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.grant_type")

        data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        response = requests.post(
            auth_url,
            data=data,
            timeout=constants.REQUEST_TIMEOUT,
        )

        _logger.debug("Authentication API response: %s", response.text)

        if response.ok:
            result = response.json()
            return f'{result.get("token_type")} {result.get("access_token")}'

        else:
            raise ValidationError(_("{reason}: Unable to connect to API.").format(reason=response.reason))

    def build_request_body(self, today_isoformat, message_id, transaction_id, reference_id, query):
        """Build the request body for API call"""
        sender_id = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        receiver_id = "Social Registry"

        header = {
            "version": "1.0.0",
            "message_id": message_id,
            "message_ts": today_isoformat,
            "action": "search",
            "sender_id": sender_id,
            "sender_uri": "",
            "receiver_id": receiver_id,
            "total_count": 0,
            "is_msg_encrypted": False,
            "meta": {},
        }

        search_request = {
            "reference_id": reference_id,
            "timestamp": today_isoformat,
            "search_criteria": {
                "version": "1.0.0",
                "reg_type": "G2P:RegistryType:Individual",
                "reg_sub_type": "Individual",
                "query_type": "graphql",
                "query": query,
            },
            "locale": "en",
        }

        message = {
            "transaction_id": transaction_id,
            "search_request": [search_request],
        }

        return {
            "signature": "",
            "header": header,
            "message": message,
        }

    def get_graphql_query(self, limit=None, offset=None, order=None):
        query = self.query.strip()

        graphql_query = query[0:-1] + "totalRegistrantCount }"
        _logger.debug(query)

        if self.target_registry:
            index = graphql_query.find("(") + 1
            is_group = str(self.target_registry == "group").lower()
            if not index:
                get_registrants_index = graphql_query.find("getRegistrants") + 14
                graphql_query = (
                    graphql_query[:get_registrants_index] + "()" + graphql_query[get_registrants_index:]
                )
                index = graphql_query.find("(") + 1

                graphql_query = graphql_query[:index] + f"isGroup: {is_group}" + graphql_query[index:]

            else:
                graphql_query = graphql_query[:index] + f"isGroup: {is_group}," + graphql_query[index:]

        if self.last_sync_date:
            index = graphql_query.find("(") + 1
            if not index:
                get_registrants_index = graphql_query.find("getRegistrants") + 14
                graphql_query = (
                    graphql_query[:get_registrants_index] + "()" + graphql_query[get_registrants_index:]
                )
                index = graphql_query.find("(") + 1
                graphql_query = (
                    graphql_query[:index]
                    + f'lastSyncDate: "{self.last_sync_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")}"'
                    + graphql_query[index:]
                )

            else:
                graphql_query = (
                    graphql_query[:index]
                    + f'lastSyncDate: "{self.last_sync_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")}",'
                    + graphql_query[index:]
                )
        # Add pagination parameters
        if limit is not None or offset is not None:
            index = graphql_query.find("(") + 1
            pagination_params = []

            if limit is not None:
                pagination_params.append(f"limit: {limit}")
            if offset is not None:
                pagination_params.append(f"offset: {offset}")
            if order is not None:
                pagination_params.append(f'order: "{order}"')

            pagination_str = ", ".join(pagination_params)

            if index == 0:
                get_registrants_index = graphql_query.find("getRegistrants") + 14
                graphql_query = (
                    graphql_query[:get_registrants_index] + "()" + graphql_query[get_registrants_index:]
                )
                index = graphql_query.find("(") + 1
                graphql_query = graphql_query[:index] + pagination_str + graphql_query[index:]
            else:
                graphql_query = graphql_query[:index] + pagination_str + "," + graphql_query[index:]

        _logger.debug("updated graphql query", graphql_query)
        return graphql_query.strip()

    def get_total_registrant_count(self):
        self.ensure_one()

        try:
            # Get paths and auth
            paths = self.get_data_source_paths()
            auth_url = self.get_social_registry_auth_url(paths)
            auth_token = self.get_auth_token(auth_url)
            search_url = self.get_social_registry_search_url(paths)

            # Prepare count query
            today_isoformat = datetime.now(timezone.utc).isoformat()
            message_id = str(uuid.uuid4())
            transaction_id = str(uuid.uuid4())
            reference_id = str(uuid.uuid4())

            # Build count-only query
            count_query = "{totalRegistrantCount}"

            # Create request body for count
            data = self.build_request_body(
                today_isoformat, message_id, transaction_id, reference_id, count_query
            )

            # Make request
            response = requests.post(
                search_url,
                data=json.dumps(data),
                headers={"Authorization": auth_token},
                timeout=constants.REQUEST_TIMEOUT,
            )

            if response.ok:
                search_responses = response.json().get("message", {}).get("search_response", [])
                if search_responses:
                    reg_record = search_responses[0].get("data", {}).get("reg_records", {})
                    return reg_record.get("totalRegistrantCount", 0)

            return 0

        except Exception as e:
            _logger.error("Error getting total registrant count: %s", str(e))
            return 0

    def fetch_registrants_batch(self, paginated_query):
        """Fetch a batch of registrants with pagination"""
        self.ensure_one()

        try:
            # Get paths and auth
            paths = self.get_data_source_paths()
            auth_url = self.get_social_registry_auth_url(paths)
            auth_token = self.get_auth_token(auth_url)
            search_url = self.get_social_registry_search_url(paths)

            # Prepare paginated query
            today_isoformat = datetime.now(timezone.utc).isoformat()
            message_id = str(uuid.uuid4())
            transaction_id = str(uuid.uuid4())
            reference_id = str(uuid.uuid4())

            data = self.build_request_body(
                today_isoformat, message_id, transaction_id, reference_id, paginated_query
            )

            response = requests.post(
                search_url,
                data=json.dumps(data),
                headers={"Authorization": auth_token},
                timeout=constants.REQUEST_TIMEOUT,
            )
            if not response.ok:
                _logger.error("Social Registry Search API response: %s", response.text)
                response.raise_for_status()

            # Process response
            search_responses = response.json().get("message", {}).get("search_response", [])
            if search_responses:
                reg_record = search_responses[0].get("data", {}).get("reg_records", {})
                registrants = reg_record.get("getRegistrants", [])

                return registrants

            return []

        except Exception as e:
            _logger.error("Error fetching registrant batch: %s", str(e))
            raise

    def get_partner_and_clean_identifier(self, identifiers):
        clean_identifiers = []
        partner_id = None

        # get existing record if there's any
        for identifier in identifiers:
            identifier_type = identifier.get("idTypeAsStr", "")
            identifier_value = identifier.get("value", "")
            if identifier_type and identifier_value:
                # Check if identifier type is already created. Create record if no existing identifier type
                id_type = self.env["g2p.id.type"].search([("name", "=", identifier_type)], limit=1)
                if not id_type:
                    id_type = self.env["g2p.id.type"].create({"name": identifier_type})

                clean_identifiers.append({"id_type": id_type, "value": identifier_value})

                if not partner_id:
                    reg_id = self.env["g2p.reg.id"].search(
                        [
                            ("id_type", "=", id_type.id),
                            ("value", "=", identifier_value),
                        ],
                        limit=1,
                    )
                    if reg_id:
                        partner_id = reg_id.partner_id

        return partner_id, clean_identifiers

    def get_individual_data(self, record):
        mapped_json = jq.first(self.output_mapping, record)
        return mapped_json

    def get_member_kind(self, data):
        # TODO: Kind will be in List
        kind_str = data.get("kind").get("name") if data.get("kind") else None

        kind = self.env["g2p.group.membership.kind"].search([("name", "=", kind_str)], limit=1)

        if not kind:
            return None

        return kind

    def get_member_relationship(self, individual, data):
        # TODO: Add relationship logic
        res = None
        return res

    def update_reg_id(self, partner_data):
        if "reg_ids" in partner_data:
            partner_data["reg_ids"] = [
                (
                    0,
                    0,
                    {
                        "id_type": self.env["g2p.id.type"]
                        .sudo()
                        .search([("name", "=", reg_id.get("id_type").get("name"))], limit=1)
                        .id,
                        "value": reg_id.get("value"),
                        "expiry_date": reg_id.get("expiry_date"),
                        "status": reg_id.get("status"),
                        "description": reg_id.get("description"),
                    },
                )
                for reg_id in partner_data["reg_ids"]
            ]

        return partner_data

    def create_or_update_registrant(self, partner_id, partner_data):
        partner_data.update({"is_registrant": True})

        # TODO: Check whether phone number already exist
        if "phone_number_ids" in partner_data:
            partner_data["phone_number_ids"] = [
                (
                    0,
                    0,
                    {
                        "phone_no": phone.get("phone_no", None),
                        "date_collected": phone.get("date_collected", None),
                        "disabled": phone.get("disabled", None),
                    },
                )
                for phone in partner_data["phone_number_ids"]
            ]

        if "reg_ids" in partner_data:
            partner_data["reg_ids"] = []

        if "group_membership_ids" in partner_data and self.target_registry == "group":
            individual_ids = []
            relationships_ids = []
            for individual_mem in partner_data.get("group_membership_ids"):
                individual_data = individual_mem.get("individual")
                # TODO: Handle the phone number logic for group members
                individual_data.update({"is_registrant": True, "phone_number_ids": []})

                update_individual_data = self.update_reg_id(individual_data)

                individual = self.env["res.partner"].sudo().create(update_individual_data)
                if individual:
                    kind = self.get_member_kind(individual_mem)
                    individual_data = {"individual": individual.id}
                    if kind:
                        individual_data["kind"] = [(4, kind.id)]

                    relationship = self.get_member_relationship(individual.id, individual_mem)

                    if relationship:
                        relationships_ids.append((0, 0, relationship))

                    individual_ids.append((0, 0, individual_data))

                partner_data["related_1_ids"] = relationships_ids
                partner_data["group_membership_ids"] = individual_ids

        if partner_id:
            partner_id.write(partner_data)
        else:
            partner_id = self.env["res.partner"].create(partner_data)

        return partner_id

    def create_registrant_id(self, clean_identifiers, partner_id):
        for clean_identifier in clean_identifiers:
            partner_reg_id = self.env["g2p.reg.id"].search(
                [
                    ("id_type", "=", clean_identifier["id_type"].id),
                    ("partner_id", "=", partner_id.id),
                ]
            )
            if not partner_reg_id:
                reg_data = {
                    "id_type": clean_identifier["id_type"].id,
                    "partner_id": partner_id.id,
                    "value": clean_identifier["value"],
                }
                self.env["g2p.reg.id"].create(reg_data)
        return

    def assign_registrant_to_program(self, partner_id):
        program_membership = self.env["g2p.program_membership"]

        if self.target_program and not program_membership.search(
            [("partner_id", "=", partner_id.id), ("program_id", "=", self.target_program.id)],
            limit=1,
        ):
            program_membership.create({"partner_id": partner_id.id, "program_id": self.target_program.id})

        return

    def process_record(self, record):
        identifiers = record.get("regIds", [])
        (
            partner_id,
            clean_identifiers,
        ) = self.get_partner_and_clean_identifier(identifiers)

        if partner_id:
            is_created = False
        else:
            is_created = True

        # Instantiate individual data
        partner_data = self.get_individual_data(record)

        partner_data.update({"data_source_id": self.data_source_id.id})

        # Create or Update registrant
        partner_id = self.create_or_update_registrant(partner_id, partner_data)

        # Check and Create Registrant ID
        self.create_registrant_id(clean_identifiers, partner_id)

        # Assign registrant into program
        self.assign_registrant_to_program(partner_id)

        # Create Social Registry Imported Individuals
        social_registry_imported_individuals = self.env["g2p.social.registry.imported.registrants"]
        if not social_registry_imported_individuals.search(
            [
                ("fetch_social_registry_id", "=", self.id),
                ("registrant_id", "=", partner_id.id),
            ],
            limit=1,
        ):
            social_registry_imported_individuals.create(
                {
                    "fetch_social_registry_id": self.id,
                    "registrant_id": partner_id.id,
                    "is_group": partner_id.is_group,
                    "is_created": is_created,
                    "is_updated": not is_created,
                }
            )

        else:
            imported_registrant = social_registry_imported_individuals.search(
                [
                    ("fetch_social_registry_id", "=", self.id),
                    ("registrant_id", "=", partner_id.id),
                ],
                limit=1,
            )

            imported_registrant.update({"is_updated": True})

        return partner_id

    def process_registrants(self, registrants):
        for record in registrants:
            identifiers = record.get("regIds", [])

            if self.import_registrant_without_id or identifiers:
                self.process_record(record)

    def process_registrants_async(self, registrants, count):
        """Queue registrants for asynchronous processing in batches."""

        max_registrant = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_import_social_registry.max_registrants_count_job_queue")
        )
        actual_count = min(len(registrants), count)

        total_batches = -(-actual_count // max_registrant)

        jobs = []
        for i in range(0, count, max_registrant):
            batch = registrants[i : i + max_registrant]
            batch_num = i // max_registrant + 1

            description = f"{self.name} - Batch {batch_num}/{total_batches} ({len(batch)} registrants)"
            jobs.append(self.delayable(description=description).process_registrants(batch))

        # Queue all batch jobs
        main_job = group(*jobs)
        main_job.delay()

    def fetch_social_registry_beneficiary(self):
        """
        Main method to fetch beneficiaries from Social Registry.

        Supports both synchronous and asynchronous processing based on batch size.
        Uses pagination to handle large datasets efficiently.

        Returns:
            dict: Action dictionary for UI notification
        """
        sticky = False
        kind = "info"
        message = _("No registrants were processed.")

        try:
            self.write({"job_status": "running", "start_datetime": fields.Datetime.now()})
            query_params = self.get_parsed_query_params()
            limit = query_params.get("limit")
            offset = query_params.get("offset", 0)
            order = query_params.get("order", "id asc")

            current_offset = offset or 0
            total_processed_records = 0

            # If the limit is not specified in query_params, use the total count as the limit
            if not limit:
                total_count = self.get_total_registrant_count()
                if total_count == 0:
                    message = _("No registrants found in the Social Registry.")
                    kind = "warning"
                    raise ValueError("Empty Social Registry")
                limit = total_count

            # max_registrant is the batch size for pagination and queue
            max_registrant_per_batch = int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("g2p_import_social_registry.max_registrants_count_job_queue", 100)
            )

            _logger.info(
                "Starting Social Registry fetch - Limit: %s, Offset: %s, Batch size: %s",
                limit,
                current_offset,
                max_registrant_per_batch,
            )

            if max_registrant_per_batch >= limit:
                # Fetch Records synchronously
                paginated_query = self.get_graphql_query(limit, current_offset, order)
                registrants = self.fetch_registrants_batch(paginated_query)

                if registrants:
                    sticky = True
                    message = _("Successfully processed %s registrants synchronously.") % len(registrants)
                    kind = "success"
                    self.process_registrants(registrants)
                    total_processed_records += len(registrants)
                else:
                    message = _(
                        "No registrants found. "
                        "Verify last sync date or "
                        "check if Social Registry contains data."
                    )
                    kind = "warning"
            else:
                # Process asynchronously in batches
                while total_processed_records < limit:
                    # Calculate the number of records to fetch in this batch
                    batch_size = min(max_registrant_per_batch, limit - total_processed_records)

                    # Use batch_size as the limit in the paginated GraphQL query
                    paginated_query = self.get_graphql_query(batch_size, current_offset, order)

                    # Fetch the registrants from the Social Registry
                    registrants = self.fetch_registrants_batch(paginated_query)

                    if not registrants:
                        message = (
                            _("No more registrants to process. Processed %s total.") % total_processed_records
                        )
                        kind = "warning" if total_processed_records == 0 else "success"
                        break

                    # Process Records asynchronously
                    sticky = True
                    self.process_registrants_async(registrants, len(registrants))

                    total_processed_records += len(registrants)
                    current_offset += len(registrants)

                    _logger.info(
                        "Processed batch: %s registrants (total: %s/%s)",
                        len(registrants),
                        total_processed_records,
                        limit,
                    )

                if total_processed_records > 0 and kind != "warning":
                    message = (
                        _("Successfully queued %s registrants for asynchronous processing.")
                        % total_processed_records
                    )
                    kind = "success"

            _logger.info("Completed Social Registry fetch. Processed %s registrants", total_processed_records)

            self.last_sync_date = fields.Datetime.now()
            end_time = fields.Datetime.now()
            self.write({"job_status": "completed", "end_datetime": end_time})

        except Exception as e:
            _logger.exception("Failed to fetch registrants from Social Registry: %s", e)
            end_time = fields.Datetime.now()
            self.write({"job_status": "failed", "end_datetime": end_time})
            message = _("Failed to fetch registrants: %s") % str(e)
            kind = "danger"
            sticky = True

        action = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Social Registry"),
                "message": message,
                "sticky": sticky,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }
        return action

    def social_registry_import_action_trigger(self):
        """
        Trigger the social registry import action based on scheduled_import configuration
        """

        for rec in self:
            if rec.job_status in ["draft", "completed", "failed"]:
                # Start the scheduled import
                rec.write({"job_status": "started", "start_datetime": fields.Datetime.now()})
                # Create or update cron job
                cron_vals = {
                    "name": f"Social Registry Import - {rec.name} #{rec.id}",
                    "active": True,
                    "interval_number": rec.interval_number,
                    "interval_type": rec.interval_type,
                    "model_id": self.env["ir.model"]
                    .search([("model", "=", "g2p.fetch.social.registry.beneficiary")])
                    .id,
                    "state": "code",
                    "code": f"model.browse({rec.id}).fetch_social_registry_beneficiary()",
                    "doall": False,
                    "numbercall": -1,
                }

                if rec.cron_id:
                    rec.cron_id.write(cron_vals)
                else:
                    rec.cron_id = self.env["ir.cron"].sudo().create(cron_vals)

                message = _(
                    "Scheduled import started - will run every %(interval_number)s %(interval_type)s"
                ) % {
                    "interval_number": rec.interval_number,
                    "interval_type": rec.interval_type,
                }

            elif rec.job_status in ["started", "running"]:
                # Stop the scheduled import
                rec.write({"job_status": "completed", "end_datetime": fields.Datetime.now()})
                if rec.cron_id:
                    rec.cron_id.unlink()
                    rec.cron_id = None
                message = _("Scheduled import stopped")

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Social Registry Import"),
                    "message": message,
                    "type": "success",
                    "sticky": False,
                },
            }

    def _compute_cron_running(self):
        """Compute whether the cron job is currently running for this import"""
        for rec in self:
            rec.cron_running = bool(
                rec.cron_id and rec.cron_id.active and rec.job_status in ["started", "running"]
            )
