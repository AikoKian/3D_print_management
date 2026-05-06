from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Crea automáticamente un registro en el módulo de Impresión 3D 
        si el producto pertenece a la categoría 'Filamentos'.
        """
        products = super(ProductTemplate, self).create(vals_list)
        
        for product in products:
            # Sincronización: De Producto a Material
            if product.categ_id.name == 'Filamentos':
                # Buscamos un tipo de material por defecto (PLA por ejemplo)
                default_type = self.env['print.material.type'].search([], limit=1)
                
                self.env['print.material'].create({
                    'product_id': product.id,
                    'material_type_id': default_type.id if default_type else False,
                    'brand': 'Genérica',
                    'color_name': 'A definir',
                })
        return products

    # Al heredar 'product.template', cualquier cambio en 'standard_price'
    # o 'name' desde Inventario/Compras disparará automáticamente los 
    # campos 'related' y 'depends' definidos en print.material.