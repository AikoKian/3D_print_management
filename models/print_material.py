from odoo import models, fields, api
from odoo.exceptions import UserError

# ==========================================
# 1. TIPOS DE MATERIAL
# ==========================================
class PrintMaterialType(models.Model):
    _name = 'print.material.type'
    _description = 'Tipo de Filamento'

    name = fields.Char(string='Nombre (Ej. PLA, ABS, PETG)', required=True)
    description = fields.Char(string='Descripcion del material', help='Nombre tecnico completo del material...')

# ==========================================
# 2. BOBINAS DE FILAMENTO
# ==========================================
class PrintMaterial(models.Model):
    _name = 'print.material'
    _description = 'Bobina de Filamento'

    # Sincronización Bidireccional del Nombre
    name = fields.Char(
        related='product_id.name', 
        string='Nombre / Etiqueta', 
        readonly=False, 
        store=True
    )
    
    brand = fields.Char(string='Marca')
    color_name = fields.Char(string='Color')
    
    material_type_id = fields.Many2one(
        'print.material.type', 
        string='Tipo de Material', 
        required=True
    )
    
    product_id = fields.Many2one(
        'product.template', 
        string='Producto en Almacén', 
        required=True, 
        ondelete='cascade'
    )

    # 1. EL PUENTE: Trae el costo en tiempo real desde el inventario
    base_cost = fields.Float(
        related='product_id.standard_price', 
        string='Costo Base (Almacén)', 
        readonly=True
    )

    # 2. EL CAMPO EDITABLE
    price_per_gram = fields.Float(
        string='Precio por Gramo',
        digits=(16, 2),
        compute='_compute_price_per_gram',
        inverse='_inverse_price_per_gram',
        store=True,
        readonly=False
    )

    # 3. LA LÓGICA: Ahora depende del puente, no del producto directamente
    @api.depends('base_cost')
    def _compute_price_per_gram(self):
        for rec in self:
            if rec.base_cost:
                rec.price_per_gram = rec.base_cost + 2
            else:
                rec.price_per_gram = 2.0

    def _inverse_price_per_gram(self):
        pass

    weight_available = fields.Float(
        related='product_id.qty_available',
        string='Stock Disponible (g)',
        readonly=True
    )

    # --- Contador de Compras ---
    purchase_count = fields.Integer(
        string='Compras / SP', 
        compute='_compute_purchase_count'
    )

    def _compute_purchase_count(self):
        """Calcula en cuántas órdenes de compra o SP aparece este material."""
        for rec in self:
            if rec.product_id:
                # Busca las líneas de compra que contengan la variante de este producto
                lines = self.env['purchase.order.line'].search([
                    ('product_id', '=', rec.product_id.product_variant_id.id)
                ])
                # Cuenta las órdenes únicas (cabeceras) a las que pertenecen esas líneas
                rec.purchase_count = len(lines.mapped('order_id'))
            else:
                rec.purchase_count = 0

    # ==========================================
    # BOTONES INTELIGENTES (NAVEGACIÓN)
    # ==========================================
    def action_view_inventory_product(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError("Este material no tiene un producto vinculado.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producto de Inventario',
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_product(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError("Este material no tiene un producto vinculado.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajustes de Producto',
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_update_stock(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError("Este material no tiene un producto vinculado.")
        variant = self.product_id.product_variant_id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajuste de Stock',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', variant.id)],
            'context': {'default_product_id': variant.id},
            'target': 'current',
        }
    
    def action_view_purchases(self):
        """Abre la vista de Compras filtrada por las SP de este material."""
        self.ensure_one()
        
        # Obtenemos los IDs de las compras relacionadas
        lines = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_id.product_variant_id.id)
        ])
        order_ids = lines.mapped('order_id').ids
        
        return {
            'name': f'Compras de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', order_ids)],
            'context': {'create': True}, # Permite crear una nueva SP desde ahí
            'target': 'current',
        }
