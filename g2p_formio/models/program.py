import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    portal_form_builder_id = fields.Many2one(
        "formio.builder",
        string="Program Form",
        domain="[('is_form_mapped_with_program', '=', False)]",
    )

    is_multiple_form_submission = fields.Boolean(default=False)

    def _update_form_JS_options(self, formio_builder, upload_url):
        try:
            js_options = json.loads(formio_builder.formio_js_options)

            if js_options:
                formio_builder.write({"is_form_mapped_with_program": True})

            if not js_options.get("editForm", {}).get("file"):
                return False

            file_components = js_options["editForm"]["file"][0]["components"]

            for component in file_components:
                if component.get("key") == "url":
                    component["defaultValue"] = upload_url

            formio_builder.write({"formio_js_options": json.dumps(js_options, indent=1)})
            return True

        except Exception as e:
            _logger.error("Error updating form JSON schema: %s", str(e))
            return False

    def _update_form_json_schema(self, formio_builder, upload_url):
        try:
            if not formio_builder.schema:
                return

            schema_dict = json.loads(formio_builder.schema)
            updated = False

            for component in schema_dict.get("components", []):
                if component.get("type") == "file" and component.get("storage") == "url":
                    component["url"] = upload_url
                    updated = True

            if updated:
                formio_builder.write({"schema": json.dumps(schema_dict, indent=1)})

        except Exception as e:
            _logger.error("Error updating form JSON schema: %s", str(e))

    @api.constrains("portal_form_builder_id")
    def _constrain_portal_form_mapping(self):
        self.ensure_one()
        formio_builder = self.portal_form_builder_id
        if not formio_builder:
            return

        upload_url = f"/v1/selfservice/uploadDocument/{self.id}"

        # Update Form JS Options
        success = self._update_form_JS_options(formio_builder, upload_url)

        # Update the Form JSON schema; if the update fails, unmap the form
        if success:
            self._update_form_json_schema(formio_builder, upload_url)
        else:
            formio_builder.write({"is_form_mapped_with_program": False})

    @api.onchange("portal_form_builder_id")
    def _onchange_portal_form_unmapping(self):
        # Check if there was a previous form that is now being removed
        previous_form = self._origin.portal_form_builder_id
        current_form = self.portal_form_builder_id

        if previous_form and not current_form:
            previous_form.write({"is_form_mapped_with_program": False})

    # Before deleting the program, unmap its form
    def unlink(self):
        if self.portal_form_builder_id:
            self.portal_form_builder_id.write({"is_form_mapped_with_program": False})
        return super().unlink()


class G2PProgramFomio(models.Model):
    _inherit = "formio.builder"

    is_form_mapped_with_program = fields.Boolean(string="Is Form Mapped", default=False)
