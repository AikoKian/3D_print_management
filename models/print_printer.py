from odoo import models, fields

class PrintPrinter(models.Model):
    _name = 'print.printer'
    _description = 'Impresora 3D'

    name = fields.Char(string='Modelo', required=True) # Ej: Ender 3 V3
    brand = fields.Char(string='Marca') # Ej: Creality

    hourly_rate = fields.Float(string='Tarifa Horaria (Gs/h)', default=0.0) # Tarifa horaria
    
    # Estados de disponibilidad
    state = fields.Selection([
        ('free', 'Libre'),
        ('busy', 'En Uso'),
        ('maintenance', 'Mantenimiento'),
        ('broken', 'Averiado')
    ], string='Estado', default='free', required=True)

    # Decisión Arquitectónica: Conectamos a los Tipos (PLA, PETG), no a las bobinas físicas
    supported_type_ids = fields.Many2many(
        'print.material.type',
        string='Materiales Soportados'
    )