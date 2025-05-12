{
    'name': 'G2P Support Desk',
    'category': 'G2P',
    'version': '17.0.1.3.0',
    'sequence': 1,
    'author': 'OpenG2P',
    'website': 'https://openg2p.org',
    'license': 'LGPL-3',
    'summary': 'OpenG2P Support Desk Management System',
    'description': """
        This module provides a comprehensive support desk management system with:
        * Ticket Management
        * Team Management
        * SLA Tracking
        * Knowledge Base
        * Beneficiary Portal Access
    """,
    'depends': [
        'base',
        'mail',
        'portal',
        'web',
        'g2p_programs',
        'g2p_registry_base',
    ],
    'data': [
        'security/support_desk_security.xml',
        'security/ir.model.access.csv',
        'views/support_ticket_views.xml',
        'views/support_team_views.xml',
        'views/support_category_views.xml',
        'views/support_tag_views.xml',
        'views/support_stage_views.xml',
        'views/menu_views.xml',
        'data/support_desk_data.xml',
    ],
    'demo': [
        'data/support_desk_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
