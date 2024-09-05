import json
import logging
from argparse import _AppendAction

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Forbidden, Unauthorized

from odoo import _, http
from odoo.http import request

from odoo.addons.g2p_self_service_portal.controllers.main import SelfServiceController
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)


class ServiceProviderContorller(http.Controller):
    @http.route(["/serviceprovider"], type="http", auth="public", website=True)
    def portal_root(self, **kwargs):
        if request.session and request.session.uid:
            return request.redirect("/serviceprovider/home")
        else:
            return request.redirect("/serviceprovider/login")

    @http.route(["/serviceprovider/login"], type="http", auth="public", website=True)
    def service_provider_login(self, **kwargs):
        redirect_uri = request.params.get("redirect") or "/serviceprovider/home"
        if request.session and request.session.uid:
            return request.redirect(redirect_uri)

        context = {}

        if request.httprequest.method == "POST":
            res = Home().web_login(**kwargs)
            if request.params["login_success"]:
                return res
            else:
                context["error"] = "Invalid Credentials"

        providers = (
            request.env["auth.oauth.provider"]
            .sudo()
            .list_providers(
                domain=(("g2p_service_provider_allowed", "=", True),),
                redirect=redirect_uri,
            )
            or []
        )

        context.update(dict(providers=providers))
        return request.render("g2p_service_provider_portal.login_page", qcontext=context)

    @http.route(["/serviceprovider/home"], type="http", auth="user", website=True)
    def portal_home(self, **kwargs):
        self.check_roles("SERVICEPROVIDER")
        return request.redirect("/serviceprovider/voucher")

    @http.route(["/serviceprovider/myprofile"], type="http", auth="public", website=True)
    def portal_profile(self, **kwargs):
        if request.session and request.session.uid:
            current_partner = request.env.user.partner_id
            return request.render(
                "g2p_service_provider_portal.profile_page",
                {
                    "current_partner": current_partner,
                },
            )

    @http.route(["/serviceprovider/aboutus"], type="http", auth="public", website=True)
    def portal_about_us(self, **kwargs):
        return request.render("g2p_service_provider_portal.aboutus_page")

    @http.route(["/serviceprovider/contactus"], type="http", auth="public", website=True)
    def portal_contact_us(self, **kwargs):
        return request.render("g2p_service_provider_portal.contact_us")

    @http.route(["/serviceprovider/otherpage"], type="http", auth="public", website=True)
    def portal_other_page(self, **kwargs):
        return request.render("g2p_service_provider_portal.other_page")

    @http.route(["/serviceprovider/help"], type="http", auth="public", website=True)
    def portal_help_page(self, **kwargs):
        return request.render("g2p_service_provider_portal.help_page")

    @http.route(["/serviceprovider/voucher"], type="http", auth="user", website=True)
    def portal_new_entitlements(self, **kwargs):
        self.check_roles("SERVICEPROVIDER")
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
                    "is_form_mapped": True
                    if reimbursement_program and reimbursement_program.self_service_portal_form
                    else False,
                }
            )

        return request.render(
            "g2p_service_provider_portal.reimbursements",
            {
                "entitlements": values,
            },
        )

    @http.route(
        ["/serviceprovider/voucher/<int:_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_new_submission(self, _id, **kwargs):
        self.check_roles("SERVICEPROVIDER")

        current_partner = request.env.user.partner_id

        entitlement = request.env["g2p.entitlement"].sudo().browse(_id)
        beneficiary = entitlement.partner_id

        if entitlement.service_provider_id.id != current_partner.id or entitlement.state != "approved":
            raise Forbidden()

        file_size = entitlement.program_id.reimbursement_program_id.file_size_spp

        # check if already claimed
        if len(entitlement.reimbursement_entitlement_ids) > 0:
            return request.redirect(f"/serviceprovider/claim/{_id}")

        view = entitlement.program_id.reimbursement_program_id.self_service_portal_form.view_id

        return request.render(
            view.id,
            {
                "entitlement_id": _id,
                "current_partner_name": current_partner.given_name.capitalize()
                + ", "
                + current_partner.family_name.capitalize()
                if current_partner.given_name and current_partner.family_name
                else current_partner.name.capitalize(),
                "beneficiary": beneficiary,
                "file_size": file_size,
            },
        )

    @http.route(
        ["/serviceprovider/submit/<int:_id>"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def portal_claim_submission(self, _id, **kwargs):
        self.check_roles("SERVICEPROVIDER")

        current_partner = request.env.user.partner_id

        # TODO: get only issued entitlements

        entitlement = request.env["g2p.entitlement"].sudo().browse(_id)
        if entitlement.service_provider_id.id != current_partner.id or entitlement.state != "approved":
            raise Forbidden()

        if request.httprequest.method == "POST":
            form_data = kwargs
            # check if already claimed
            if len(entitlement.reimbursement_entitlement_ids) > 0:
                return request.redirect(f"/serviceprovider/claim/{_id}")

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
            received_code = form_data.get("code", None)
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
                return request.redirect(f"/serviceprovider/voucher/{_id}")

        else:
            # TODO: search and return currently active claim
            # TODO: Check whether entitlement.reimbursement_entitlement_ids[0].partner_id is same as current
            if len(entitlement.reimbursement_entitlement_ids) == 0:
                return request.redirect(f"/serviceprovider/entitlement/{_id}")

        return request.redirect(f"/serviceprovider/claim/{_id}")

    @http.route(
        ["/serviceprovider/claim/<int:_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_post_submission(self, _id, **kwargs):
        self.check_roles("SERVICEPROVIDER")

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
            return request.redirect(f"/serviceprovider/entitlement/{_id}")

        return request.render(
            "g2p_service_provider_portal.reimbursement_form_submitted",
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

    def check_roles(self, role_to_check):
        if role_to_check == "SERVICEPROVIDER":
            if not request.session or not request.env.user:
                raise Unauthorized(_("User is not logged in"))
            if not request.env.user.partner_id.supplier_rank > 0:
                raise Forbidden(_AppendAction("User is not allowed to access the portal"))

    @http.route("/get_voucher_codes", type="http", auth="user", website=True)
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

    def process_documents(self, documents, store, membership):
        all_file_details = []
        for tag, document in documents.items():
            all_file_details += SelfServiceController.add_file_to_store(
                document, store, program_membership=membership, tags=tag
            )
        return all_file_details
