{
    'name': "Stockroom",
    'version': "18.0.1.1",
    'license': "LGPL-3",
    'description': """ Inventory management system for small to medium businesses. Best suited for Cafeterias with multiple outlets. """,
    'summary': "Manage stock across multiple locations and outlets.",
    'category': "Inventory",
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
    'author': "Dhruv Patel"

}
