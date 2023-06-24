import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DefaultEntitlementManagerForDocument(models.Model):
    _inherit = "g2p.program.entitlement.manager.default"

    def prepare_entitlements(self, cycle, beneficiaries):
        ents = super(DefaultEntitlementManagerForDocument, self).prepare_entitlements(
            cycle, beneficiaries
        )
        ents.copy_documents_from_beneficiary()
        return ents
