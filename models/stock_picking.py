from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_view_related_purchase(self):
        """Navega de vuelta al Pedido de Compra."""
        self.ensure_one()
        # Odoo guarda la relación en el campo purchase_id si viene de compras
        if self.purchase_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'res_id': self.purchase_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_related_invoices(self):
        """Navega a las facturas vinculadas al pedido de origen."""
        self.ensure_one()
        if self.purchase_id and self.purchase_id.invoice_ids:
            return {
                'name': 'Facturas del Proveedor',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.purchase_id.invoice_ids.ids)],
                'target': 'current',
            }
    
    def action_view_related_invoices(self):
        """Navega a las facturas o muestra un mensaje flotante si no existen."""
        self.ensure_one()
        
        # 1. Verificamos si existen facturas vinculadas al pedido de origen
        if self.purchase_id and self.purchase_id.invoice_ids:
            return {
                'name': 'Facturas del Proveedor',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.purchase_id.invoice_ids.ids)],
                'target': 'current',
            }
        # 2. Si no hay facturas, devolvemos una notificación en pantalla
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Información de Facturación',
                    'message': 'Aún no se han generado facturas para este pedido de compra.',
                    'sticky': True, # El mensaje desaparece solo después de unos segundos
                    'type': 'warning', # Color amarillo/naranja para advertencia
                }
            }