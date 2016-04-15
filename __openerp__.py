{
    'name': 'Mage2Odoo - Unigry Gift Card',
    'version': '1.1',
    'author': 'Kyle Waid',
    'category': 'Sales Management',
    'depends': ['mage2odoo'],
    'website': 'https://www.gcotech.com',
    'description': """ 
    """,
    'data': [
		'wizard/card_functions.xml',
		'views/invoice.xml',
		'views/sale.xml', 
		'views/claim.xml',
		'views/mage.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
