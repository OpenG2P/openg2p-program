import json
import logging

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request

from odoo.addons.g2p_agent_portal_base.controllers.main import AgentPortalBase

_logger = logging.getLogger(__name__)


class ReimbursementPortal(AgentPortalBase):
    @http.route(["/portal/reimbursement/voucher"], type="http", auth="user", website=True)
    def portal_new_entitlements(self, **kwargs):
        self.check_roles("Portal")
        partner_id = request.env.user.partner_id
        entitlements = (
            request.env["g2p.entitlement"]
            .sudo()
            .search(
                [
                    ("service_provider_id", "=", partner_id.id),
                    ("state", "=", "approved"),
                ]
            )
        )

        values = []
        for entitlement in entitlements:
            # to check no reimbursement claims are already made against this entitlement
            is_submitted = len(entitlement.reimbursement_entitlement_ids) > 0
            reimbursement_program = entitlement.program_id.reimbursement_program_id
            values.append(
                {
                    "entitlement_id": entitlement.id,
                    "program_name": entitlement.program_id.name,
                    "beneficiary_name": entitlement.partner_id.name,
                    "initial_amount": entitlement.initial_amount,
                    "is_submitted": is_submitted,
                    "status": "New" if not is_submitted else entitlement.reimbursement_entitlement_ids.state,
                    "is_form_mapped": getattr(reimbursement_program, "self_service_portal_form", False)
                    is not None,
                }
            )

        return request.render(
            "g2p_reimbursement_portal.reimbursements_entitlement_view",
            {
                "entitlements": values,
            },
        )

    @http.route(
        ["/portal/reimbursement/voucher/<int:_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_new_submission(self, _id, **kwargs):
        self.check_roles("Portal")

        current_partner = request.env.user.partner_id

        entitlement = request.env["g2p.entitlement"].sudo().browse(_id)
        beneficiary = entitlement.partner_id

        if entitlement.service_provider_id.id != current_partner.id or entitlement.state != "approved":
            raise Forbidden()

        # file_size = entitlement.program_id.reimbursement_program_id.file_size_spp

        # check if already claimed
        if len(entitlement.reimbursement_entitlement_ids) > 0:
            return request.redirect(f"/portal/reimbursement/claim/{_id}")

        # view = entitlement.program_id.reimbursement_program_id.self_service_portal_form.view_id

        return request.render(
            "g2p_reimbursement_portal.reimbursement_form_template_view",
            {
                "entitlement_id": _id,
                "current_partner_name": current_partner.given_name.capitalize()
                + ", "
                + current_partner.family_name.capitalize()
                if current_partner.given_name and current_partner.family_name
                else current_partner.name.capitalize(),
                "beneficiary": beneficiary,
                # "file_size": file_size,
            },
        )

    @http.route(
        ["/portal/reimbursement/submit/<int:_id>"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def portal_claim_submission(self, _id, **kwargs):
        self.check_roles("Portal")

        current_partner = request.env.user.partner_id

        # TODO: get only issued entitlements

        entitlement = request.env["g2p.entitlement"].sudo().browse(_id)
        if entitlement.service_provider_id.id != current_partner.id or entitlement.state != "approved":
            raise Forbidden()

        if request.httprequest.method == "POST":
            form_data = kwargs
            # check if already claimed
            if len(entitlement.reimbursement_entitlement_ids) > 0:
                return request.redirect(f"/portal/reimbursement/claim/{_id}")

            # TODO: allow resubmission

            # TODO: Check if reimbursement program mapped to original program

            current_partner_membership = current_partner.program_membership_ids.filtered(
                lambda x: x.program_id.id == entitlement.program_id.reimbursement_program_id.id
            )
            # TODO: Check current partner not part of prog memberships of
            # reimbursement program.

            supporting_documents_store = (
                entitlement.program_id.reimbursement_program_id.supporting_documents_store
            )

            # TODO: remove all hardcoding in the next lines
            received_code = form_data.get("voucher_code", None)
            actual_amount = form_data.get("initial_amount", None)

            document_details = {}
            for key in kwargs:
                if isinstance(kwargs[key], FileStorage):
                    document_details[key] = request.httprequest.files.getlist(key)

            supporting_document_files = self.process_documents(
                document_details,
                supporting_documents_store,
                membership=current_partner_membership,
            )
            if not supporting_document_files:
                _logger.warning("Empty/No File received for field %s", "Statement of Account")
                supporting_document_file_ids = None
            else:
                supporting_document_file_ids = []

                # saving the multiple document id
                for document_id in supporting_document_files:
                    supporting_document_file_ids.append(document_id.get("document_id", None))

            reimbursement_claim = entitlement.submit_reimbursement_claim(
                current_partner,
                received_code,
                supporting_document_file_ids=supporting_document_file_ids
                if supporting_document_file_ids
                else None,
                amount=actual_amount,
            )
            if reimbursement_claim == (2, None):
                _logger.error("Not a valid Voucher Code")
                return request.redirect(f"/portal/reimbursement/voucher/{_id}")

        else:
            # TODO: search and return currently active claim
            # TODO: Check whether entitlement.reimbursement_entitlement_ids[0].partner_id is same as current
            if len(entitlement.reimbursement_entitlement_ids) == 0:
                return request.redirect(f"/portal/reimbursement/entitlement/{_id}")

        return request.redirect(f"/portal/reimbursement/claim/{_id}")

    @http.route(
        ["/portal/reimbursement/claim/<int:_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_post_submission(self, _id, **kwargs):
        self.check_roles("Portal")

        entitlement = request.env["g2p.entitlement"].sudo().browse(_id)
        current_partner = request.env.user.partner_id

        reimbursement_claim = (
            request.env["g2p.entitlement"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", current_partner.id),
                    ("reimbursement_original_entitlement_id", "=", entitlement.id),
                ]
            )
        )

        if len(reimbursement_claim) < 1:
            return request.redirect(f"/portal/reimbursement/entitlement/{_id}")

        return request.render(
            "g2p_reimbursement_portal.reimbursement_form_submitted",
            {
                "entitlement": entitlement.id,
                "submission_date": reimbursement_claim.create_date.strftime("%d-%b-%Y"),
                "approved_date": reimbursement_claim.date_approved,
                "application_id": reimbursement_claim.id,
                "application_status": reimbursement_claim.state,
                "user": current_partner.given_name.capitalize()
                + " "
                + current_partner.family_name.capitalize()
                if current_partner.given_name and current_partner.family_name
                else current_partner.name.capitalize(),
            },
        )

    @http.route("/portal/reimbursement/get_voucher_codes", type="http", auth="user", website=True)
    def get_voucher_codes(self):
        entitlements = (
            request.env["g2p.entitlement"]
            .sudo()
            .search([("service_provider_id", "=", request.env.user.partner_id.id)])
        )

        voucher_details = []
        for entilement in entitlements:
            voucher_details.append(
                {
                    "beneficiary_name": entilement.partner_id.name,
                    "code": entilement.code,
                }
            )

        return json.dumps(voucher_details)

    @classmethod
    def add_file_to_store(cls, files, store, program_membership=None, tags=None):
        if isinstance(files, FileStorage):
            files = [
                files,
            ]
        file_details = []
        for file in files:
            if store and file.filename:
                if len(file.filename.split(".")) > 1:
                    supporting_document_ext = "." + file.filename.split(".")[-1]
                else:
                    supporting_document_ext = None
                document_file = store.add_file(
                    file.stream.read(),
                    extension=supporting_document_ext,
                    program_membership=program_membership,
                    tags=tags,
                )
                document_uuid = document_file.name.split(".")[0]
                file_details.append(
                    {
                        "document_id": document_file.id,
                        "document_uuid": document_uuid,
                        "document_name": document_file.name,
                        "document_slug": document_file.slug,
                        "document_url": document_file.url,
                    }
                )
        return file_details

    def get_field_to_exclude(self, data):
        current_partner = request.env.user.partner_id
        keys = []
        for key in data:
            if key in current_partner:
                current_partner[key] = data[key]
                keys.append(key)

        return keys

    def process_documents(self, documents, store, membership):
        all_file_details = []
        for tag, document in documents.items():
            all_file_details += self.add_file_to_store(
                document, store, program_membership=membership, tags=tag
            )
        return all_file_details
