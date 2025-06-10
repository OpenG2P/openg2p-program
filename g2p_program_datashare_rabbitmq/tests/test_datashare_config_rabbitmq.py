# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.tests import TransactionCase


class TestG2PProgramMembership(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Registrant", "is_registrant": True})
        self.program = self.env["g2p.program"].create({"name": "Test Program", "target_type": "individual"})
        self.config = self.env["g2p.datashare.config.rabbitmq"].create(
            {
                "name": "RabbitMQ Test Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "vhost": "/",
                "exchange": "test_exchange",
                "routing_key": "test_routing_key",
                "transform_data_jq": """{"id": .id, "name": .name}""",
                "active": True,
                "data_source": "beneficiary_registry",
                "program_id": self.program.id,
            }
        )
        # Ensure clean state by deleting any pre-existing membership for this partner/program combo
        self.env["g2p.program_membership"].search(
            [("partner_id", "=", self.partner.id), ("program_id", "=", self.program.id)]
        ).unlink()

        self.membership = self.env["g2p.program_membership"].create(
            {
                "program_id": self.program.id,
                "partner_id": self.partner.id,
            }
        )

    def test_push_to_rabbitmq(self):
        """Test that _push_to_rabbitmq sends data via RabbitMQ publish"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            self.membership._push_to_rabbitmq()

            # Allow multiple publish calls
            self.assertGreaterEqual(mock_publish.call_count, 1)

            # Check at least one call has the expected ID key
            found_valid = any("id" in call.args[0] for call in mock_publish.call_args_list)
            self.assertTrue(found_valid)

    def test_create_push_to_rabbitmq(self):
        """Test that create method pushes new record to RabbitMQ"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            # Use a new partner to avoid unique constraint violation
            new_partner = self.env["res.partner"].create(
                {
                    "name": "Unique Registrant",
                    "is_registrant": True,
                }
            )
            self.env["g2p.program_membership"].create(
                {"program_id": self.program.id, "partner_id": new_partner.id}
            )

            self.assertGreaterEqual(mock_publish.call_count, 1)

            found_valid = any("id" in call.args[0] for call in mock_publish.call_args_list)
            self.assertTrue(found_valid)

    def test_write_push_to_rabbitmq(self):
        """Test that write method pushes updated record to RabbitMQ"""
        with patch(
            "odoo.addons.g2p_registry_datashare_rabbitmq.models.datashare_config_rabbitmq.G2PDatashareConfigRabbitMQ.publish"
        ) as mock_publish:
            self.membership.write({"state": "enrolled"})

            self.assertGreaterEqual(mock_publish.call_count, 1)

            found_valid = any("id" in call.args[0] for call in mock_publish.call_args_list)
            self.assertTrue(found_valid)
