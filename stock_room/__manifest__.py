{
    'name': "Stockroom",
    'version': "18.0.1.2",
    'license': "LGPL-3",
    'description': """ Inventory management system for small to medium businesses. Best suited for Cafeterias with multiple outlets. """,
    'summary': "Inventory system for Cafe with multiple outlets",
    'category': "Warehouse",
    'website': 'https://myportfolio-kappa-ivory.vercel.app',
    'depends':[
        'mail',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/location_views.xml",
        "views/outlet_views.xml",
        "views/product_views.xml",
        "views/inventory_views.xml",
        "views/usage_views.xml",
        "views/delivery_views.xml",
        "views/vendor_views.xml",
        "views/menu.xml"
    ],
    'author': "Dhruv Patel",
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False

}
