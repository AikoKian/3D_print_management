from odoo import models, fields, api
from odoo.exceptions import UserError

class PrintProject(models.Model):
    _name = 'print.project'
    _description = 'Proyecto de Impresión 3D'

    # --- Campos Básicos ---
    name = fields.Char(string='Referencia del Proyecto', required=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    date_order = fields.Date(string='Fecha del Pedido', default=fields.Date.context_today)
    date_expected = fields.Date(string='Fecha Aprox. Finalización')
    printer_id = fields.Many2one('print.printer', string='Impresora Asignada')
    date_finished = fields.Datetime(string='Fecha Final', readonly=True)
    
    line_ids = fields.One2many('print.project.line', 'project_id', string='Materiales a Consumir')
    sale_order_id = fields.Many2one('sale.order', string='Venta Generada', readonly=True)

    # --- Estados ---
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Impresión'),
        ('review', 'En Revisión'),
        ('done', 'Finalizado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    # --- Campos de Costeo y Tiempo ---
    estimated_hours = fields.Float(string='Horas Estimadas (Máquina)')
    real_hours = fields.Float(
        string='Horas Reales (Máquina)',
        states={'in_progress': [('readonly', False)]},
        readonly=True
    )
    labor_hours = fields.Float(string='Mano de Obra (h)')
    labor_rate = fields.Float(string='Tarifa Laboral/h', default=0.0)
    
    price_notes = fields.Text(string='Notas de Ajuste de Precio')
    
    total_calculated_price = fields.Float(
        string='Precio Sugerido (Calculado)', 
        compute='_compute_total_price', 
        store=True,
        readonly=True,
        help="Monto sugerido calculado automaticamente."
    )

    final_price = fields.Float(
        string='Precio Final Real', 
        digits=(16, 2),
        help="Monto definitivo que se enviará al presupuesto de venta."
    )

    # --- Gestión de Archivos ---
    stl_file = fields.Binary(string='Archivo STL / Diseño')
    stl_filename = fields.Char(string='Nombre del Archivo STL')
    
    # --- Campo de detalles tecnicos ---
    technical_notes = fields.Text(string='Notas Técnicas de Impresión')

    # --- Lógica de Precios ---
    @api.depends('real_hours', 'estimated_hours', 'labor_hours', 'labor_rate', 'line_ids.weight_needed', 'printer_id.hourly_rate')
    def _compute_total_price(self):
        """Calcula el precio técnico. Usa horas reales si existen, sino usa estimadas."""
        for rec in self:
            # Si estamos en impresión o revisión usamos las reales, en borrador las estimadas
            horas_calculo = rec.real_hours if rec.real_hours > 0 else rec.estimated_hours
            mquina = horas_calculo * (rec.printer_id.hourly_rate or 0.0)
            laboral = rec.labor_hours * rec.labor_rate
            material = sum(l.weight_needed * l.material_id.price_per_gram for l in rec.line_ids)
            rec.total_calculated_price = mquina + laboral + material

    @api.onchange('real_hours', 'estimated_hours', 'labor_hours', 'labor_rate', 'line_ids', 'printer_id')
    def _onchange_price_inputs(self):
        """Sincroniza el precio final real con el sugerido al cambiar cualquier parámetro."""
        if self.state in ['draft', 'in_progress']:
            self._compute_total_price() # Forzamos el cálculo previo
            self.final_price = self.total_calculated_price

    # --- Funciones de Transición y Utilidad ---
    def action_check_availability(self):
        self.ensure_one()
        mensajes = []
        if not self.printer_id and not self.line_ids:
            raise UserError("Debe seleccionar impresora y materiales para el análisis.")
        if self.printer_id and self.printer_id.state != 'free':
            estado_label = dict(self.printer_id._fields['state'].selection).get(self.printer_id.state)
            mensajes.append(f"⚠️ La impresora '{self.printer_id.name}' está {estado_label}.")
        if not self.line_ids:
            mensajes.append("❓ No has añadido materiales.")
        else:
            for line in self.line_ids:
                diferencia = line.stock_available - line.weight_needed
                if diferencia < 0:
                    mensajes.append(f"❌ CRÍTICO: {line.material_id.name} insuficiente. Faltan {abs(diferencia)}g.")
        if mensajes:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Análisis de Viabilidad',
                    'cancelado': "\n".join(mensajes),
                    'sticky': True,
                    'type': 'danger' if any("❌" in m for m in mensajes) else 'warning',
                }
            }
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Proyecto Viable', 'message': 'Todo en orden.', 'type': 'success'}}

    def action_start_printing(self):
        for rec in self:
            if not rec.printer_id: raise UserError("Debe asignar una impresora.")
            if rec.printer_id.state != 'free': raise UserError(f"La impresora {rec.printer_id.name} no está disponible.")
            rec.printer_id.write({'state': 'busy'})
            rec.state = 'in_progress'

    def action_submit_for_review(self):
        for rec in self:
            if rec.real_hours <= 0: raise UserError("Debe ingresar las horas reales de máquina.")
            if rec.final_price <= 0: raise UserError("El Precio Final Real debe ser mayor a cero.")
            if rec.printer_id: rec.printer_id.write({'state': 'free'})
            
            # Lógica de Consumo de Inventario
            loc_origen = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
            loc_destino = self.env['stock.location'].search([('usage', '=', 'production')], limit=1) or \
                          self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            for line in rec.line_ids:
                if line.weight_needed > 0 and line.material_id.product_id:
                    variante = line.material_id.product_id.product_variant_id
                    move = self.env['stock.move'].create({
                        'name': f'Consumo 3D: {rec.name}',
                        'product_id': variante.id,
                        'product_uom_qty': line.weight_needed,
                        'product_uom': variante.uom_id.id,
                        'location_id': loc_origen.id,
                        'location_dest_id': loc_destino.id,
                    })
                    move._action_confirm()
                    move._action_assign()
                    move.write({'quantity_done': line.weight_needed})
                    move._action_done()

            # Creación del Presupuesto
            if not rec.sale_order_id:
                Product = self.env['product.product']
                service = Product.search([('name', '=', 'Servicio de Impresión 3D')], limit=1) or \
                          Product.create({'name': 'Servicio de Impresión 3D', 'type': 'service'})
                sale_order = self.env['sale.order'].create({'partner_id': rec.partner_id.id, 'origin': rec.name, 'note': rec.price_notes})
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id, 'product_id': service.id, 'product_uom_qty': 1,
                    'name': f'Servicio de Impresión: {rec.name}', 'price_unit': rec.final_price
                })
                rec.sale_order_id = sale_order.id
            rec.state = 'review'

    def action_confirm_done(self):
        self.write({'state': 'done', 'date_finished': fields.Datetime.now()})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'in_progress' and rec.printer_id: rec.printer_id.write({'state': 'free'})
            rec.state = 'cancel'

    def action_view_sale_order(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Presupuesto Generado', 'res_model': 'sale.order', 'res_id': self.sale_order_id.id, 'view_mode': 'form', 'target': 'current'}

class PrintProjectLine(models.Model):
    _name = 'print.project.line'
    _description = 'Línea de Consumo'
    project_id = fields.Many2one('print.project', ondelete='cascade')
    material_id = fields.Many2one('print.material', required=True)
    stock_available = fields.Float(related='material_id.weight_available', readonly=True)
    weight_needed = fields.Float(string='Cantidad (g)', required=True)
    inventory_status = fields.Selection([('ok', 'Ok'), ('low', 'Bajo'), ('insufficient', 'Falta')], compute='_compute_inventory_status')

    @api.depends('weight_needed', 'stock_available')
    def _compute_inventory_status(self):
        for rec in self:
            diff = rec.stock_available - rec.weight_needed
            if diff < 0: rec.inventory_status = 'insufficient'
            elif diff < 500: rec.inventory_status = 'low'
            else: rec.inventory_status = 'ok'