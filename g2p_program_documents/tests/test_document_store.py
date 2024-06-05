from datetime import datetime, timedelta

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStore(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.program = self.env["g2p.program"].create({"name": "Test Program"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.backend = self.env["storage.backend"].create(
            {
                "name": "Test Document Store",
            }
        )
        self.cycle = self.env["g2p.cycle"].create(
            {
                "name": "Test Cycle",
                "program_id": self.program.id,
                "sequence": 1,
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            }
        )

        self.ent_manager = self.env["g2p.program.entitlement.manager.default"].create(
            {
                "program_id": self.program.id,
                "name": "Test Manager",
            }
        )

    def test_add_file_with_program_membership(self):
        """Test adding a file with program membership association."""
        # triggering entitlement preparation with out membership
        self.ent_manager.prepare_entitlements(self.cycle, self.env["g2p.program_membership"])

        membership = self.env["g2p.program_membership"].create(
            {
                "name": "Test Membership",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
            }
        )
        data = b"Test data1"
        document1 = self.backend.add_file(data, name="test.txt", program_membership=membership)
        self.ent_manager.prepare_entitlements(self.cycle, membership)
        self.assertTrue(document1.program_membership_id)

        # Retesting with existing document
        data = b"Test data2"
        self.backend.add_file(data, name="test.txt", program_membership=membership)

        # TODO: will revisit this assert.
        # cycle2 = self.env["g2p.cycle"].create(
        #     {
        #         "name": "Test Cycle2",
        #         "program_id": self.program.id,
        #         "sequence": 1,
        #         "start_date": datetime.now().strftime("%Y-%m-%d"),
        #         "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        #     }
        # )
        # entitlement2 = self.ent_manager.prepare_entitlements(cycle2, membership)
        # self.assertEqual(entitlement2.document_count, len(entitlement2.supporting_document_ids))

    def test_entitlement_supporting_documents(self):
        # creating document with out membership
        entitlement = self.env["g2p.entitlement"].create(
            {
                "name": "Test Entitlement",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
                "cycle_id": self.cycle.id,
                "initial_amount": 100,
                "supporting_document_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Document 1",
                            "backend_id": self.backend.id,
                        },
                    )
                ],
            }
        )
        membership = self.env["g2p.program_membership"].create(
            {
                "name": "Test Membership",
                "partner_id": self.partner.id,
                "program_id": self.program.id,
            }
        )
        entitlement.supporting_document_ids = [
            (
                0,
                0,
                {
                    "name": "Document 2",
                    "backend_id": self.backend.id,
                },
            )
        ]

        self.assertEqual(entitlement.supporting_document_ids[1].program_membership_id, membership)

        entitlement.supporting_document_ids = [
            (
                0,
                0,
                {"name": "Document 3", "backend_id": self.backend.id, "program_membership_id": membership.id},
            )
        ]

        self.assertEqual(entitlement.supporting_document_ids[2].program_membership_id, membership)
