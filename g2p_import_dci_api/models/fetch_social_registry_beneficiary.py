import json
import logging
import uuid
from datetime import datetime, timezone

import requests
from dateutil import parser

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval

from odoo.addons.queue_job.delay import group

from ..models import constants

_logger = logging.getLogger(__name__)


class FetchDomainFilter(models.TransientModel):
    _name = "g2p.fetch.domain.filter"
    _description = "Fetch Domain Filter"

    birthdate = fields.Date("Birth Date")


class G2PFetchSocialRegistryBeneficiary(models.Model):
    _name = "g2p.fetch.social.registry.beneficiary"
    _description = "Fetch Social Registry Beneficiary"

    MAX_PARTNER_FOR_SYNC_SEARCH = 150

    def _get_default_domain(self):
        return (
            f'["&",["birthdate",">","{constants.DEFAULT_YEAR}-{constants.DEFAULT_MONTH}-{constants.DEFAULT_DAY}"]'
            f',["birthdate","<","{constants.DEFAULT_YEAR}-{constants.DEFAULT_MONTH}-{constants.DEFAULT_DAY}"]]'
        )

    data_source_id = fields.Many2one("spp.data.source", required=True)

    name = fields.Char("Search Criteria Name", required=True)

    program = fields.Many2one("g2p.program", string="Target Progam", required=True)

    query = fields.Text(
        required=True,
    )

    done_imported = fields.Boolean()
    imported_individual_ids = fields.One2many(
        "g2p.social.registry.imported.individuals",
        "fetch_social_registry_id",
        "Imported Individuals",
        readonly=True,
    )

    def get_data_source_paths(self):
        """
        The function `get_data_source_paths` returns a dictionary of data source paths, with names as
        keys and paths as values, and raises a validation error if certain paths are not configured.
        :return: a dictionary containing the names and paths of data sources.
        """
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
        """
        The function returns the search URL for a given data source and search path.

        :param paths: The `paths` parameter is a dictionary that contains various paths related to the
        data source. It is assumed that the `paths` dictionary has a key named
        `DATA_SOURCE_SEARCH_PATH_NAME` which represents the search path for the data source
        :return: a URL string that is constructed by concatenating the `url` and `search_path`
        variables.
        """
        url = self.data_source_id.url
        search_path = paths.get(constants.DATA_SOURCE_SEARCH_PATH_NAME)

        return f"{url}{search_path}"

    def get_social_registry_auth_url(self, paths):
        """
        The function `get_social_registry_auth_url` returns the authentication URL for a data source.

        :param paths: The `paths` parameter is a dictionary that contains various paths related to the
        data source. In this code snippet, it is used to retrieve the value of the
        `DATA_SOURCE_AUTH_PATH_NAME` key
        :return: a URL string that includes the base URL, authentication path, and URL parameters.
        """
        url = self.data_source_id.url
        auth_path = paths.get(constants.DATA_SOURCE_AUTH_PATH_NAME)

        return f"{url}{auth_path}"

    def get_auth_token(self, auth_url):
        """
        The function `get_auth_token` sends a POST request to an authentication URL and returns the
        access token if the response is successful, otherwise it raises a validation error.

        :param auth_url: The `auth_url` parameter is the URL endpoint where the authentication request
        should be sent. It is typically provided by the API service you are trying to authenticate with
        :return: an authentication token in the format "{token_type} {access_token}".
        """
        headers = self.get_headers_for_request()

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
        db_name = (
            self.env["ir.config_parameter"].sudo().get_param("social_registry_db_name")
        )

        data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
            "db_name": db_name,
        }
        response = requests.post(
            auth_url,
            headers=headers,
            data=json.dumps(data),
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
        """
        The function returns a dictionary containing header information for a message.

        :param social_registry_version: The version of the Social Registry system
        :param today_isoformat: The `today_isoformat` parameter is a string representing the current
        date and time in ISO 8601 format. It is used to set the value of the "message_ts" field in the
        header
        :param message_id: The `message_id` parameter is a unique identifier for the message. It can be
        any string value that uniquely identifies the message
        :return: a dictionary with the following key-value pairs:
        """
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

    def get_predicate_query(self):
        """
        The function `get_predicate_query` takes a domain as input and generates a query based on the provided
        filters for birthdate and location.
        :return: a list of query expressions.
        """
        query = []
        domain = safe_eval.safe_eval(self.domain)

        birthdate_expressions = {
            "gt": {},
            "condition": "and",
            "lt": {},
        }

        location_expression = {}

        for dom in domain:
            if isinstance(dom, list):
                field_name = constants.FIELD_MAPPING.get(dom[0])
                operator = constants.OPERATION_MAPPING.get(dom[1])
                if field_name and operator:
                    value = dom[2]
                    birthdate_expressions.get(operator, {}).update(
                        {
                            "attribute_name": field_name,
                            "operator": operator,
                            "attribute_value": value,
                        }
                    )

        errors = []

        # Birthdate Range query
        if any([birthdate_expressions.get("gt"), birthdate_expressions.get("lt")]):
            if not birthdate_expressions.get("gt"):
                errors.append(_("Add filter for greater than birthdate!"))
            if not birthdate_expressions.get("lt"):
                errors.append(_("Add filter for less than birthdate!"))

            if not errors:
                query.append(
                    {
                        "expression1": birthdate_expressions["gt"],
                        "condition": birthdate_expressions["condition"],
                        "expression2": birthdate_expressions["lt"],
                    }
                )

        if errors:
            raise ValidationError("\n".join(errors))

        if location_expression:
            query.append({"expression1": location_expression})

        if not query:
            raise ValidationError(
                _(
                    "Add birthdate filter with one greater than and one less than or a location."
                )
            )

    def get_graphql_query(self):
        """
        The function `get_graphql_query` generates a query based on the provided on the provided
        graphql query.
        :return: a list of query expressions.
        """
        query = []

        graphql_query = self.query[0:-1] + "totalRegistrantCount" + "}"

        query.append({"expression1": graphql_query})
        _logger.warning(query)

        return query

    def get_search_request(self, reference_id, today_isoformat):
        """
        The function `get_search_request` returns a dictionary containing search criteria for a birth
        registry based on the given reference ID, timestamp, and query.

        :param reference_id: The reference_id is a unique identifier for the search request. It can be
        any value that helps identify the request, such as a UUID or a database record ID
        :param today_isoformat: The `today_isoformat` parameter is a string representing the current
        date in ISO 8601 format. It is used to set the timestamp in the `search_requests` dictionary
        :return: a dictionary object called "search_requests".
        """
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
        """
        The function `get_message` returns a dictionary containing the transaction ID and a list of
        search requests.

        :param today_isoformat: The parameter "today_isoformat" is a string representing the current
        date in ISO format. For example, "2022-01-01"
        :param transaction_id: The transaction ID is a unique identifier for a specific transaction. It
        is used to track and identify a particular transaction in a system or database
        :param reference_id: The reference_id is a unique identifier for a specific transaction or
        request. It is used to track and identify the transaction or request throughout the system
        :return: a dictionary with two keys: "transaction_id" and "search_request". The value of
        "transaction_id" is the transaction_id parameter passed to the function, and the value of
        "search_request" is a list containing the search_request variable.
        """
        # Define Search Requests
        search_request = self.get_search_request(reference_id, today_isoformat)

        return {
            "transaction_id": transaction_id,
            "search_request": [search_request],
        }

    def get_data(self, signature, header, message):
        """
        The function `get_data` takes in three parameters (signature, header, message) and returns a
        dictionary with the header and message as key-value pairs.

        :param signature: The signature parameter is a string that represents the signature of the data.
        It could be a cryptographic signature or any other type of signature used to verify the
        authenticity or integrity of the data
        :param header: The "header" parameter is a string that represents the header of the data. It
        could be a title or a brief description of the data
        :param message: The `message` parameter is a string that represents the content of the message.
        It could be any text or information that needs to be included in the data
        :return: A dictionary containing the header and message values.
        """
        return {
            # "signature": signature,
            "header": header,
            "message": message,
        }

    def get_partner_and_clean_identifier(self, identifiers):
        """
        The function takes a list of identifiers, creates new identifier types if necessary, and returns
        the partner ID and a list of clean identifiers.

        :param identifiers: The `identifiers` parameter is a list of dictionaries. Each dictionary
        represents an identifier and contains two key-value pairs:
        :return: a tuple containing the partner_id and clean_identifiers.
        """
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

    def get_full_name_format(self, family_name, given_name, middle_name):
        """
        The function takes in a family name, given name, and middle name, and returns the full name in
        uppercase with a comma separating the family name.

        :param family_name: The family name parameter represents the last name or surname of a person
        :param given_name: The parameter "given_name" represents the given or first name of a person
        :param middle_name: The `middle_name` parameter is a string that represents the middle name of a
        person
        :return: the full name in uppercase format.
        """
        name = ""
        if family_name:
            name += family_name + ", "
        if given_name:
            name += given_name + " "
        if middle_name:
            name += middle_name + " "
        name = name.upper()

        return name

    def get_individual_data(self, record):
        """
        The function `get_individual_data` retrieves individual data from a record and returns it in a
        dictionary format.

        :param record: The `record` parameter is a dictionary that contains various data related to an
        individual. It may have the following keys:
        :return: a dictionary containing various data related to an individual. The dictionary includes
        the individual's name, family name, given name, middle name, gender, birth date, whether the
        individual is a registrant or not, whether the individual is a group or not, and the location
        ID. If the individual is a mother and has a home location identifier, the dictionary also
        includes the home location
        """

        name = record.get("name", "")
        family_name = record.get("familyName", "")
        given_name = record.get("givenName", "")
        addl_name = record.get("middleName", "")
        gender = record.get("gender", "")
        birth_date = record.get("birthDate", "")
        is_group = record.get("isGroup", "")

        try:
            birth_date = parser.parse(birth_date)
        except Exception:
            birth_date = False

        # name = self.get_full_name_format(family_name, given_name, middle_name)

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

    def create_or_update_individual(self, partner_id, partner_data):
        """
        The function creates or updates a partner record in the res.partner model based on the provided
        partner_id and partner_data.

        :param partner_id: The partner_id parameter is the ID of the partner record that you want to
        create or update. If the partner_id is provided, it means that you want to update an existing
        partner record. If the partner_id is not provided, it means that you want to create a new
        partner record
        :param partner_data: A dictionary containing the data for the partner. This data will be used to
        create or update the partner record
        :return: the partner_id, which is either the updated partner record or the newly created partner
        record.
        """
        if partner_id:
            partner_id.write(partner_data)
        else:
            partner_id = self.env["res.partner"].create(partner_data)

        return partner_id

    def create_registrant_id(self, clean_identifiers, partner_id):
        """
        The function creates a registrant ID for a partner using clean identifiers.

        :param clean_identifiers: The parameter "clean_identifiers" is a list of dictionaries. Each
        dictionary represents a clean identifier and contains the following keys:
        :param partner_id: partner_id is an object representing the partner for whom the registrant ID
        is being created
        :return: The function does not explicitly return anything.
        """
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

    def create_and_process_group(self, partner_id, relation_partner_id):
        """
        The function creates and processes a group membership for a partner and their relation partner.

        :param partner_id: The `partner_id` parameter represents the ID of the individual partner
        (child) that needs to be added to the group
        :param relation_partner_id: The parameter "relation_partner_id" represents the partner
        (individual) with whom the group is related. It is used to check if the partner already has
        group membership and to add the partner to the group if necessary
        :return: The function does not explicitly return anything. It ends with a return statement
        without any value, so it effectively returns None.
        """
        group = None

        # Check if parent have group membership then get and update group
        if relation_partner_id.individual_membership_ids:
            membership = None
            for ind_membership in relation_partner_id.individual_membership_ids:
                if ind_membership.is_created_from_social_registry:
                    membership = ind_membership
                    break
            if membership:
                group = membership.group
                group.write(
                    {
                        "data_source_id": self.data_source_id.id,
                    }
                )

        # Create group membership
        if not group:
            group = self.env["res.partner"].create(
                {
                    "name": str(relation_partner_id.family_name).title(),
                    "is_registrant": True,
                    "is_group": True,
                    "grp_is_created_from_social_registry": True,
                    "data_source_id": self.data_source_id.id,
                    "kind": self.env.ref("g2p_registry_group.group_kind_family").id,
                }
            )

        # If child not in group
        if not self.env["g2p.group.membership"].search(
            [
                ("group", "=", group.id),
                ("individual", "=", partner_id.id),
            ]
        ):
            # Add child to group
            self.env["g2p.group.membership"].create(
                {
                    "group": group.id,
                    "individual": partner_id.id,
                }
            )

        # if parent not in a group
        if not self.env["g2p.group.membership"].search(
            [
                ("group", "=", group.id),
                ("individual", "=", relation_partner_id.id),
            ]
        ):
            # Add parent to group
            self.env["g2p.group.membership"].create(
                {
                    "group": group.id,
                    "individual": relation_partner_id.id,
                    "kind": [
                        (
                            4,
                            self.env.ref(
                                "g2p_registry_membership.group_membership_kind_head"
                            ).id,
                        )
                    ],
                }
            )

        group._compute_child_under_no_of_months()

        return

    def assign_individual_to_program(self, partner_id):
        """
        The function add partner into the program.

        :param partner_id: The `partner_id` parameter represents the ID of the individual partner
        (child) that needs to be added to the program
        :return: The function does not explicitly return anything. It ends with a return statement
        without any value, so it effectively returns None.
        """

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
        """
        The function processes records by extracting identifiers, getting partner and clean identifiers,
        creating or updating individual data, creating a registrant ID, and creating Social Registry imported
        individuals.

        :param record: The "record" parameter is a dictionary that contains information about a
        particular record. It may have the following keys:
        :return: the variable "partner_id".
        """
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

        # Create or Update individual
        partner_id = self.create_or_update_individual(partner_id, partner_data)

        # Check and Create Registrant ID
        self.create_registrant_id(clean_identifiers, partner_id)

        # Assign individual into program
        self.assign_individual_to_program(partner_id)

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

    def process_partners(self, partners):
        for record in partners:
            identifiers = record.get("regIds", [])
            if identifiers:

                self.process_record(record)

                # Process Relation
                # relation_partner_id = None
                # relations = record.get("relations", [])
                # for relation in relations:
                #     relation_identifiers = relation.get("identifier", [])
                #     is_mother = "Mother" in relation.get("@type", "")
                #     if relation_identifiers and is_mother:
                #         relation_partner_id = self.process_record(relation)
                #         break

                # if relation_partner_id:
                #     self.create_and_process_group(
                #         partner_id, relation_partner_id
                #     )

    def process_partners_async(self, partners, count):
        _logger.warning("Fetching Registrant Asynchronously!")
        jobs = []
        for i in range(0, count, self.MAX_PARTNER_FOR_SYNC_SEARCH):
            jobs.append(
                self.delayable().process_partners(
                    partners[i : i + self.MAX_PARTNER_FOR_SYNC_SEARCH]
                )
            )
        main_job = group(*jobs)
        main_job.delay()

    def fetch_social_registry_beneficiary(self):
        """
        This function is used to fetch beneficiary data from a Social Registry system and
        process it in the current system.
        :return: an action object.
        """

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

        # Define signature / Signature is not being used right now hence commented
        # signature = calculate_signature(header=header, payload=message)
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

        # Process response
        if response.ok:
            kind = "success"
            message = _("Successfully Imported Social Registry Beneficiaries")
            sticky = False

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
                    if total_partners_count < self.MAX_PARTNER_FOR_SYNC_SEARCH:
                        self.process_partners(partners)

                    else:
                        self.process_partners_async(partners, total_partners_count)
                        kind = "success"
                        message = _(
                            "Fetching from Social Registry Started Asynchronously."
                        )
                        sticky = True

                else:
                    kind = "danger"
                    message = _("Unable to process query.")

            self.done_imported = True
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

    def enable_fetch(self):
        """
        The function enables the "Fetch" button and displays a success notification.
        :return: an action dictionary.
        """
        self.ensure_one()

        self.done_imported = False

        action = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Enabled Fetch button"),
                "message": _("Fetch on this criteria is now enabled."),
                "sticky": False,
                "type": "success",
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }
        return action
