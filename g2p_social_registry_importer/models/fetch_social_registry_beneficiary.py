import json
import logging
import uuid
from datetime import datetime, timezone

import requests
from camel_converter import dict_to_snake

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

    query = fields.Text(
        required=True,
    )

    last_sync_date = fields.Datetime(string="Last synced on", required=False)

    imported_registrant_ids = fields.One2many(
        "g2p.social.registry.imported.registrants",
        "fetch_social_registry_id",
        "Imported Regsitrants",
        readonly=True,
    )

    @api.onchange("registry")
    def onchange_target_registry(self):
        for rec in self:
            rec.target_program = None

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

    def get_header_for_body(self, social_registry_version, today_isoformat, message_id):
        sender_id = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        receiver_id = "Social Registry"
        return {
            "version": "1.0.0",
            "message_id": message_id,
            "message_ts": today_isoformat,
            "action": "search",
            "sender_id": sender_id,
            "sender_uri": "",
            "receiver_id": receiver_id,
            "total_count": 0,
        }

    def get_graphql_query(self):
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

        _logger.debug("updated graphql query", graphql_query)
        return graphql_query.strip()

    def get_search_request(self, reference_id, today_isoformat):
        search_requests = {
            "reference_id": reference_id,
            "timestamp": today_isoformat,
            "search_criteria": {
                "reg_type": "G2P:RegistryType:Individual",
                "query_type": "graphql",
                "query": self.get_graphql_query(),
            },
        }

        return search_requests

    def get_message(self, today_isoformat, transaction_id, reference_id):
        # Define Search Requests
        search_request = self.get_search_request(reference_id, today_isoformat)

        return {
            "transaction_id": transaction_id,
            "search_request": [search_request],
        }

    def get_data(self, signature, header, message):
        return {
            "sinature": signature,
            "header": header,
            "message": message,
        }

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
        vals = dict_to_snake(record)
        return vals

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
        max_registrant = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_import_social_registry.max_registrants_count_job_queue")
        )
        _logger.warning("Fetching Registrant Asynchronously!")
        jobs = []
        for i in range(0, count, max_registrant):
            jobs.append(self.delayable().process_registrants(registrants[i : i + max_registrant]))
        main_job = group(*jobs)
        main_job.delay()

    def fetch_social_registry_beneficiary(self):
        config_parameters = self.env["ir.config_parameter"].sudo()
        today_isoformat = datetime.now(timezone.utc).isoformat()
        social_registry_version = config_parameters.get_param("social_registry_version")
        max_registrant = int(
            config_parameters.get_param("g2p_import_social_registry.max_registrants_count_job_queue")
        )

        message_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())
        reference_id = str(uuid.uuid4())

        # Define Data Source
        paths = self.get_data_source_paths()

        # Define Social Registry auth url

        full_social_registry_auth_url = self.get_social_registry_auth_url(paths)

        # Retrieve auth token

        auth_token = self.get_auth_token(full_social_registry_auth_url)

        # Define Social Registry search url
        full_social_registry_search_url = self.get_social_registry_search_url(paths)

        # Define header
        header = self.get_header_for_body(
            social_registry_version,
            today_isoformat,
            message_id,
        )

        # Define message
        message = self.get_message(
            today_isoformat,
            transaction_id=transaction_id,
            reference_id=reference_id,
        )

        signature = ""

        # Define data
        data = self.get_data(
            signature,
            header,
            message,
        )

        data = json.dumps(data)

        # POST Request
        response = requests.post(
            full_social_registry_search_url,
            data=data,
            headers={"Authorization": auth_token},
            timeout=constants.REQUEST_TIMEOUT,
        )

        if not response.ok:
            _logger.error("Social Registry Search API response: %s", response.text)
        response.raise_for_status()

        sticky = False

        # Process response
        if response.ok:
            kind = "success"
            message = _("Successfully Imported Social Registry Beneficiaries")

            search_responses = response.json().get("message", {}).get("search_response", [])
            if not search_responses:
                kind = "warning"
                message = _("No imported beneficiary")

            for search_response in search_responses:
                reg_record = search_response.get("data", {}).get("reg_records", [])
                registrants = reg_record.get("getRegistrants", [])
                total_partners_count = reg_record.get("totalRegistrantCount", "")

                if total_partners_count:
                    if total_partners_count < max_registrant:
                        self.process_registrants(registrants)

                    else:
                        self.process_registrants_async(registrants, total_partners_count)
                        kind = "success"
                        message = _("Fetching from Social Registry Started Asynchronously.")
                        sticky = True

                else:
                    kind = "success"
                    message = _("No matching records found.")

            self.last_sync_date = fields.Datetime.now()

        else:
            kind = "danger"
            message = response.json().get("error", {}).get("message", "")
            if not message:
                message = _("{reason}: Unable to connect to API.").format(reason=response.reason)

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
