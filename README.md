# LibreInventory

## Autenticación

Configurar `backend/.env` desde `backend/.env.example`, instalar dependencias y
correr desde `backend/`:

```sh
python manage.py migrate
python manage.py createsuperuser
```

En `/admin/`, el superusuario crea usuarios, empresas y membresías. El rol se
asigna en la membresía: puede cambiar entre empresas. Los usuarios del negocio
no necesitan `is_staff`; el superusuario usa `is_superuser` de Django.

| Rol | Permisos para las vistas |
| --- | --- |
| Administrador (`ADMIN`) | `IsCompanyAdmin`, `CanSell`, `CanManageInventory` |
| Vendedor (`SELLER`) | `CanSell`: ventas y cotizaciones |
| Bodeguero (`WAREHOUSE`) | `CanManageInventory`: compras e inventario |
| Superusuario | Acceso global sin membresía |

Los permisos están en `accounts/permissions.py`. Las vistas de negocio reciben
`company_id` en la URL y filtran sus registros por esa empresa.
Las empresas y membresías inactivas bloquean a los usuarios normales.

- `POST /api/accounts/login/`: enviar `username` y `password`; devuelve `access` y `refresh`.
- `POST /api/accounts/token/refresh/`: enviar `refresh`; devuelve un nuevo `access`.
- `GET /api/accounts/me/`: devuelve el usuario y sus membresías activas.

Enviar `Authorization: Bearer <access>`. El acceso dura 30 minutos y la
renovación un día. Los permisos consultan el rol actual en la base de datos.
No hay registro público ni edición de roles por API.

La migración convierte `OWNER` en `ADMIN` y `OPERATOR` en `SELLER`.

Para probar autenticación sin necesitar PostgreSQL:

```sh
DATABASE_URL=sqlite:///:memory: python manage.py test accounts
```

## API de negocio

Cada módulo tiene `serializers.py`, `views.py` y `urls.py`, con rutas explícitas
y viewsets como LibreDrop. El prefijo es `/api/companies/<company_id>/`.

| Recurso | Operaciones y acceso |
| --- | --- |
| `contacts/` | CRUD para los tres roles |
| `products/`, `warehouses/` | Consulta para todos; escritura para administrador y bodeguero |
| `quotations/`, `quotation-items/` | CRUD de borradores para administrador y vendedor |
| `sales/`, `sale-items/` | CRUD de borradores para administrador y vendedor |
| `purchases/`, `purchase-items/` | CRUD de borradores para administrador y bodeguero |
| `stock-balances/`, `stock-reservations/`, `stock-movements/` | Solo consulta para los tres roles |
| `payments/` | Consulta y registro: vendedor ve ventas, bodeguero ve compras, administrador ve ambos |
| `memberships/` | Solo consulta para administrador |

Los recursos CRUD admiten GET/POST en la colección y GET/PUT/PATCH/DELETE en
`<id>/`. Las empresas se consultan en `/api/companies/` y `/api/companies/<id>/`.
La creación de empresas, usuarios y membresías continúa en `/admin/`.

Para crear una venta y sus líneas:

```json
POST /api/companies/1/sales/
{"number": "V-001", "warehouse": 1, "customer": 1}

POST /api/companies/1/sale-items/
{"sale": 1, "product": 1, "quantity": "2.000", "unit_price": "25.00"}
```

Las compras usan `purchase-items/` con `purchase` y `unit_cost`;
las cotizaciones usan `quotation-items/` con `quotation` y `unit_price`.
Se puede filtrar una colección de líneas con `?sale=1`, `?purchase=1` o
`?quotation=1`. Los encabezados incluyen sus líneas como `items` de solo lectura.
El nombre del producto se copia a `description`; en ventas y cotizaciones,
omitir `unit_price` usa el precio del catálogo. Cada línea redondea a dos
decimales y actualiza el total del documento dentro de una transacción.
`company`, `created_by`, `line_total`, `total` y los estados son de solo lectura.

Esta etapa permite preparar documentos en borrador. Confirmar, entregar,
reservar, devolver mercadería y convertir cotizaciones quedan pendientes;
el CRUD no modifica existencias ni permite escribir el historial manualmente.
Los pagos requieren un documento confirmado y un importe dentro del saldo.
Solo el administrador registra reembolsos o anula un pago mediante
`POST payments/<id>/void/` con `{"reason": "Motivo"}`. Los pagos no se editan ni borran.

Los helpers de `common/serializers.py` y `common/views.py` concentran la
validación de empresa, el bloqueo de documentos y el recálculo de totales.

Para ejecutar las pruebas del auth y de la API en una base temporal:

```sh
DATABASE_URL=sqlite:///:memory: python manage.py test accounts common
```
