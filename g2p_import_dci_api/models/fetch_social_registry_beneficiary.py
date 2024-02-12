import json
import logging
import uuid
from datetime import datetime, timezone

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.queue_job.delay import group

from ..models import constants

_logger = logging.getLogger(__name__)


class G2PFetchSocialRegistryBeneficiary(models.Model):
    _name = "g2p.fetch.social.registry.beneficiary"
    _description = "Fetch Social Registry Beneficiary"

    data_source_id = fields.Many2one("spp.data.source", required=True)

    name = fields.Char("Search Criteria Name", required=True)

    program = fields.Many2one("g2p.program", string="Target Progam", required=True)

    query = fields.Text(
        required=True,
    )

    imported_individual_ids = fields.One2many(
        "g2p.social.registry.imported.individuals",
        "fetch_social_registry_id",
        "Imported Individuals",
        readonly=True,
    )

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

        grant_type = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("social_registry_grant_type")
        )
        client_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("social_registry_client_id")
        )
        client_secret = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("social_registry_client_secret")
        )
        username = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("social_registry_user_name")
        )
        password = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("social_registry_user_password")
        )

        data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
        }

        response = requests.post(
            auth_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=constants.REQUEST_TIMEOUT,
        )

        if response.ok:
            result = response.json()
            return f'{result.get("token_type")} {result.get("access_token")}'
        else:
            raise ValidationError(
                _("{reason}: Unable to connect to API.").format(reason=response.reason)
            )

    def get_headers_for_request(self):
        return {
            "Content-Type": "application/json",
        }

    def get_header_for_body(self, social_registry_version, today_isoformat, message_id):

        sender_id = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        )
        receiver_id = "Social Registry"
        total_count = 10
        return {
            "version": social_registry_version,
            "message_id": message_id,
            "message_ts": today_isoformat,
            "action": "search",
            "sender_id": sender_id,
            "sender_uri": "",
            "receiver_id": receiver_id,
            "total_count": total_count,
            "encryption_algorithm": "",
        }

    def get_graphql_query(self):

        query = []

        graphql_query = self.query[0:-1] + "totalRegistrantCount" + "}"

        query.append({"expression1": graphql_query})
        _logger.warning(query)

        return query

    def get_search_request(self, reference_id, today_isoformat):

        search_requests = {
            "reference_id": reference_id,
            "timestamp": today_isoformat,
            "search_criteria": {
                "reg_type": "G2P:RegistryType:Individual",
                "query_type": constants.GRAPHQL,
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
                id_type = self.env["g2p.id.type"].search(
                    [("name", "=", identifier_type)], limit=1
                )
                if not id_type:
                    id_type = self.env["g2p.id.type"].create({"name": identifier_type})

                clean_identifiers.append(
                    {"id_type": id_type, "value": identifier_value}
                )

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

        name = record.get("name", "")
        family_name = record.get("familyName", "")
        given_name = record.get("givenName", "")
        addl_name = record.get("middleName", "")
        gender = record.get("gender", "")
        birth_date = record.get("birthDate", "")
        is_group = record.get("isGroup", "")

        vals = {
            "name": name,
            "family_name": family_name,
            "given_name": given_name,
            "addl_name": addl_name,
            "gender": gender,
            "birthdate": birth_date,
            "is_registrant": True,
            "is_group": is_group,
        }

        return vals

    def create_or_update_registrant(self, partner_id, partner_data):

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

        if self.program and not program_membership.search(
            [("partner_id", "=", partner_id.id), ("program_id", "=", self.program.id)],
            limit=1,
        ):
            program_membership.create(
                {"partner_id": partner_id.id, "program_id": self.program.id}
            )

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
        social_registry_imported_individuals = self.env[
            "g2p.social.registry.imported.individuals"
        ]
        if not social_registry_imported_individuals.search(
            [
                ("fetch_social_registry_id", "=", self.id),
                ("individual_id", "=", partner_id.id),
            ],
            limit=1,
        ):
            social_registry_imported_individuals.create(
                {
                    "fetch_social_registry_id": self.id,
                    "individual_id": partner_id.id,
                    "is_created": is_created,
                    "is_updated": not is_created,
                }
            )

        else:
            imported_registrant = social_registry_imported_individuals.search(
                [
                    ("fetch_social_registry_id", "=", self.id),
                    ("individual_id", "=", partner_id.id),
                ],
                limit=1,
            )

            imported_registrant.update({"is_updated": True})

        return partner_id

    def process_registrants(self, partners):
        for record in partners:
            identifiers = record.get("regIds", [])
            if identifiers:

                self.process_record(record)

    def process_registrants_async(self, partners, count):
        _logger.warning("Fetching Registrant Asynchronously!")
        jobs = []
        for i in range(0, count, constants.MAX_REGISTRANT):
            jobs.append(
                self.delayable().process_registrants(
                    partners[i : i + constants.MAX_REGISTRANT]
                )
            )
        main_job = group(*jobs)
        main_job.delay()

    def fetch_social_registry_beneficiary(self):

        config_parameters = self.env["ir.config_parameter"].sudo()
        today_isoformat = datetime.now(timezone.utc).isoformat()
        social_registry_version = config_parameters.get_param("social_registry_version")

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

        # Define headers for post request
        headers = self.get_headers_for_request()

        headers.update({"Authorization": auth_token})

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
            headers=headers,
            data=data,
            timeout=constants.REQUEST_TIMEOUT,
        )

        sticky = False

        # Process response
        if response.ok:
            kind = "success"
            message = _("Successfully Imported Social Registry Beneficiaries")

            search_responses = (
                response.json().get("message", {}).get("search_response", [])
            )
            if not search_responses:
                kind = "warning"
                message = _("No imported beneficiary")
            for search_response in search_responses:
                reg_record = search_response.get("data", {}).get("reg_record", [])
                partners = reg_record.get("getRegistrants", [])
                total_partners_count = reg_record.get("totalRegistrantCount", "")

                if total_partners_count:
                    if total_partners_count < constants.MAX_REGISTRANT:
                        self.process_registrants(partners)

                    else:
                        self.process_registrants_async(partners, total_partners_count)
                        kind = "success"
                        message = _(
                            "Fetching from Social Registry Started Asynchronously."
                        )
                        sticky = True

                else:
                    kind = "danger"
                    message = _("Unable to process query.")

        else:
            kind = "danger"
            message = response.json().get("error", {}).get("message", "")
            if not message:
                message = _("{reason}: Unable to connect to API.").format(
                    reason=response.reason
                )

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
