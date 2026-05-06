{
    'name': 'Gestión Integral de Impresión 3D',
    'version': '2.0',
    'category': 'Manufacturing',
    'depends': ['base', 'contacts', 'purchase', 'stock', 'sale_management'], 
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/print_material_view.xml',
        'views/print_printer_view.xml',
        'views/print_project_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': True,
}