import logging
import time

from odoo.tests.common import TransactionCase
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class SupportDeskTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test users
        cls.user_1 = cls.env["res.users"].create(
            {
                "name": "Test User 1",
                "login": "test_user_1",
                "email": "test_user_1@example.com",
                "groups_id": [(4, cls.env.ref("g2p_support_desk.group_support_desk_user").id)],
            }
        )
        cls.user_2 = cls.env["res.users"].create(
            {
                "name": "Test User 2",
                "login": "test_user_2",
                "email": "test_user_2@example.com",
                "groups_id": [(4, cls.env.ref("g2p_support_desk.group_support_desk_manager").id)],
            }
        )

        # Create test team
        cls.team = cls.env["support.team"].create(
            {
                "name": "Test Team",
                "leader_id": cls.user_2.id,
                "member_ids": [(4, cls.user_1.id)],
            }
        )

        # Create test category
        cls.category = cls.env["support.category"].create(
            {
                "name": "Test Category",
                "sequence": 1,
            }
        )

        # Create test tag
        cls.tag = cls.env["support.tag"].create(
            {
                "name": "Test Tag",
                "color": 1,
            }
        )

        # Create test stages
        cls.stage_new = cls.env["support.stage"].create(
            {
                "name": "New",
                "sequence": 1,
                "is_default": True,
            }
        )
        cls.stage_in_progress = cls.env["support.stage"].create(
            {
                "name": "In Progress",
                "sequence": 2,
            }
        )
        cls.stage_done = cls.env["support.stage"].create(
            {
                "name": "Done",
                "sequence": 3,
            }
        )

    def test_01_ticket_creation(self):
        """Test ticket creation and basic fields"""
        # First, ensure we're using the correct stage
        default_stage = self.env["support.stage"].search([("is_default", "=", True)], limit=1)
        if not default_stage:
            default_stage = self.env["support.stage"].search([], limit=1)
        self.assertTrue(default_stage, "No default stage found")

        ticket = self.env["support.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "category_id": self.category.id,
                "tag_ids": [(4, self.tag.id)],
                "priority": "1",  # Medium priority
                "stage_id": default_stage.id,
            }
        )

        self.assertEqual(ticket.name, "Test Ticket")
        self.assertEqual(html2plaintext(ticket.description), "Test Description")
        self.assertEqual(ticket.team_id, self.team)
        self.assertEqual(ticket.category_id, self.category)
        self.assertEqual(ticket.tag_ids, self.tag)
        self.assertEqual(ticket.priority, "1")
        self.assertEqual(ticket.stage_id, default_stage)
        self.assertTrue(ticket.active)

    def test_02_ticket_workflow(self):
        """Test ticket workflow and stage transitions"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Workflow Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Test stage transitions
        ticket.write({"stage_id": self.stage_in_progress.id})
        self.assertEqual(ticket.stage_id, self.stage_in_progress)

        ticket.write({"stage_id": self.stage_done.id})
        self.assertEqual(ticket.stage_id, self.stage_done)
        self.assertIsNotNone(ticket.closed_date)

    def test_03_ticket_assignments(self):
        """Test ticket assignments and reassignments"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Assignment Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Test user assignment
        ticket.write({"user_id": self.user_1.id})
        self.assertEqual(ticket.user_id, self.user_1)

        # Test team reassignment
        new_team = self.env["support.team"].create(
            {
                "name": "New Test Team",
                "leader_id": self.user_2.id,
            }
        )
        ticket.write({"team_id": new_team.id})
        self.assertEqual(ticket.team_id, new_team)

    def test_04_ticket_priority(self):
        """Test ticket priority changes"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Priority Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Test priority changes
        priorities = ["0", "1", "2", "3"]
        for priority in priorities:
            ticket.write({"priority": priority})
            self.assertEqual(ticket.priority, priority)

    def test_05_ticket_tags(self):
        """Test ticket tag management"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Tag Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Create additional tags
        tag2 = self.env["support.tag"].create(
            {
                "name": "Test Tag 2",
                "color": 2,
            }
        )
        tag3 = self.env["support.tag"].create(
            {
                "name": "Test Tag 3",
                "color": 3,
            }
        )

        # Test adding multiple tags
        ticket.write({"tag_ids": [(4, self.tag.id), (4, tag2.id), (4, tag3.id)]})
        self.assertEqual(len(ticket.tag_ids), 3)

        # Test removing tags
        ticket.write({"tag_ids": [(3, self.tag.id)]})
        self.assertEqual(len(ticket.tag_ids), 2)

    def test_06_ticket_search(self):
        """Test ticket search functionality"""
        # Create test tickets
        self.env["support.ticket"].search([]).unlink()
        ticket1 = self.env["support.ticket"].create(
            {
                "name": "Search Test Ticket 1",
                "description": "Test Description 1",
                "team_id": self.team.id,
                "priority": "2",
                "stage_id": self.stage_new.id,
            }
        )
        self.env["support.ticket"].create(
            {
                "name": "Search Test Ticket 2",
                "description": "Test Description 2",
                "team_id": self.team.id,
                "priority": "0",
                "stage_id": self.stage_new.id,
            }
        )

        # Test search by name
        tickets = self.env["support.ticket"].search([("name", "ilike", "Search Test")])
        self.assertEqual(len(tickets), 2)

        # Test search by priority
        tickets = self.env["support.ticket"].search([("priority", "=", "2")])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket1)

    def test_07_ticket_access_rights(self):
        """Test ticket access rights"""
        # Create ticket as user 1
        ticket = (
            self.env["support.ticket"]
            .with_user(self.user_1)
            .create(
                {
                    "name": "Access Test Ticket",
                    "description": "Test Description",
                    "team_id": self.team.id,
                    "stage_id": self.stage_new.id,
                }
            )
        )

        # Test user 1 access (should have access since they created it)
        user1_ticket = self.env["support.ticket"].with_user(self.user_1).search([("id", "=", ticket.id)])
        self.assertEqual(len(user1_ticket), 1)

        # Test user 2 access (should have access as manager)
        user2_ticket = self.env["support.ticket"].with_user(self.user_2).search([("id", "=", ticket.id)])
        self.assertEqual(len(user2_ticket), 1)

        # Create another ticket as user 2
        ticket2 = (
            self.env["support.ticket"]
            .with_user(self.user_2)
            .create(
                {
                    "name": "Access Test Ticket 2",
                    "description": "Test Description",
                    "team_id": self.team.id,
                    "stage_id": self.stage_new.id,
                }
            )
        )

        # Test user 1 access to ticket2 (should not have access)
        user1_ticket2 = self.env["support.ticket"].with_user(self.user_1).search([("id", "=", ticket2.id)])
        self.assertEqual(len(user1_ticket2), 0)

        # Test user 2 access to ticket2 (should have access)
        user2_ticket2 = self.env["support.ticket"].with_user(self.user_2).search([("id", "=", ticket2.id)])
        self.assertEqual(len(user2_ticket2), 1)

    def test_09_ticket_response_time(self):
        """Test ticket response time tracking"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Response Time Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Add a small delay to ensure time difference
        time.sleep(1)

        # Simulate first response by updating the ticket
        ticket.write({"description": "Updated description with response", "user_id": self.user_1.id})

        # Response time should be calculated based on create_date and write_date
        # self.assertIsNotNone(ticket.response_time)
        # self.assertGreater(ticket.response_time, 0)

    def test_10_ticket_resolution_time(self):
        """Test ticket resolution time tracking"""
        ticket = self.env["support.ticket"].create(
            {
                "name": "Resolution Time Test Ticket",
                "description": "Test Description",
                "team_id": self.team.id,
                "stage_id": self.stage_new.id,
            }
        )

        # Simulate resolution
        ticket.write({"stage_id": self.stage_done.id, "closed_date": self.env.cr.now()})
        self.assertIsNotNone(ticket.closed_date)
        self.assertIsNotNone(ticket.resolution_time)
