# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import base64
import logging
from io import BytesIO

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2pProgramRegistrantInfo(models.TransientModel):
    _name = "g2p.program.registrantinfo.wizard"
    _description = "G2P Program Registrant Info Wizard"

    reason_for_app = fields.Char(string="Reason for Application")
    upload_doc1 = fields.Binary(string="Medical Prescription", attachment=True)
    upload_doc2 = fields.Binary(string="Medical Diagnosis", attachment=True)
    upload_doc3 = fields.Binary(
        string="Additional Supporting Document", attachment=True
    )
    additional_info = fields.Char(string="Additional Information")

    def jsonize_form_data(self, data, program, membership=None):
        try:
            for key in data:
                if isinstance(data.get(key), bytes):
                    value = data[key]
                    if value:
                        if not program.supporting_documents_store:
                            _logger.error(
                                "Supporting Documents Store is not set in Program Configuration"
                            )
                            data[key] = None
                            continue
                        data[key] = self.add_files_to_store(
                            value,
                            program.supporting_documents_store,
                            program_membership=membership,
                        )
                        if not data[key]:
                            _logger.warning("Empty/No File received for field %s", key)
                            continue
        except Exception as e:
            _logger.exception("An error occurred while jsonizing form data: %s", str(e))
        return data

    @staticmethod
    def add_files_to_store(files, store, program_membership=None):
        file_details = []
        try:
            binary_data = base64.b64decode(files)
            filestream = BytesIO(binary_data)
            if files and store:
                document_file = store.add_file(
                    filestream.read(),
                    extension=None,
                    program_membership=program_membership,
                )
                if document_file:
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
        except Exception as e:
            _logger.exception(
                "An error occurred while adding files to the store: %s", str(e)
            )
        return file_details

    def create_registrantinfo(self):
        membership = (
            self.env["g2p.program_membership"]
            .sudo()
            .search([("id", "=", self._context.get("active_id"))])
        )
        partners = membership.partner_id
        program = membership.program_id

        if not partners or not program:
            return

        try:
            data = {
                "Reason for Application": self.reason_for_app or None,
                "Document1": self.upload_doc1 or None,
                "Document2": self.upload_doc2 or None,
                "Document3": self.upload_doc3 or None,
                "Additional Information": self.additional_info or None,
            }

            processed_data = self.jsonize_form_data(data, program, membership[0])

            self.env["g2p.program.registrant_info"].sudo().create(
                {
                    "state": "active",
                    "program_registrant_info": processed_data,
                    "program_id": program.id,
                    "registrant_id": partners.id,
                }
            )

        except Exception as e:
            _logger.exception(
                "An error occurred while creating registrant info: %s", str(e)
            )
