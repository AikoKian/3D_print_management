
# Gestion de Proyectos de Impresion 3D (Odoo 16)

Este modulo transforma Odoo en una central de operaciones para gestionar proyectos de impresion 3D o servicios de fabricacion por encargo. Permite centralizar desde el diseño tecnico hasta el despacho final, integrando de forma nativa los flujos comerciales y logisticos.

---

## Caracteristicas Principales

El modulo actua como el nucleo de comunicacion entre los departamentos clave de la empresa:

* **Ventas y Facturacion**: Permite la generacion automatica de Pedidos de Venta (SO) a partir de los Proyectos de Impresion. Automatiza el flujo de facturacion una vez que el proyecto ha sido aprobado.
* **Gestion de Compras**: Provee control sobre materiales y filamentos. Incluye alertas y gestion de reabastecimiento mediante Solicitudes de Presupuesto (SP) antes de iniciar nuevos proyectos para evitar interrupciones por falta de insumos.
* **Inventario Estrategico**: Logra la integracion total de materiales consumibles (gramos de filamento) y servicios de impresion. Facilita la comunicacion organica entre los modulos de compras, ventas y almacen.

---

## Requisitos Tecnicos

| Framework | Odoo 16.0 (Community o Enterprise) |
| Lenguaje | Python 3.12 |
| Base de Datos | PostgreSQL |

---

## Instrucciones de Instalacion

1. Descargue o clone este repositorio en su directorio de add-ons personalizados:
   `git clone [https://github.com/TU_USUARIO/3D_print_management.git](https://github.com/TU_USUARIO/3D_print_management.git)`
2. Verifique que las dependencias nativas de Odoo esten instaladas: `product`, `stock`, `purchase` y `sale`.
3. Reinicie el servicio de Odoo o su contenedor de Docker.
4. Active el Modo Desarrollador en Odoo.
5. Dirijase al menu de Aplicaciones, haga clic en "Actualizar lista de aplicaciones" e instale el modulo "Gestion de Impresion 3D".

---

## Notas del Desarrollador

> Este modulo esta diseñado para ser ligero y escalable. Si se planea utilizar en un entorno de produccion con una carga elevada de archivos adjuntos (como archivos STL o modelos 3D), se recomienda configurar un almacenamiento de archivos (filestore) externo o un servicio compatible con S3 para optimizar el rendimiento de la base de datos.

---

## Licencia

Este proyecto se distribuye bajo la licencia **LGPL-3**. Es posible utilizar, modificar y distribuir el codigo manteniendo los creditos del autor original.
