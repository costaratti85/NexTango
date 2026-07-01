# Servidor ERPNext — Datos de acceso

## Acceso SSH

| Campo | Valor |
|---|---|
| Host | 190.190.190.20 |
| Usuario SSH | costa |
| Contraseña SSH | sunshine |

```bash
ssh costa@190.190.190.20
```

## ERPNext

| Campo | Valor |
|---|---|
| URL | http://190.190.190.20 |
| Usuario | administrator |
| Contraseña | ErpAdmin_2026 |

## Base de datos

| Campo | Valor |
|---|---|
| Motor | MariaDB 10.6 |
| Usuario root | root |
| Contraseña root | ErpNextDB_2026 |

## Stack instalado

| Componente | Versión |
|---|---|
| Ubuntu | 22.04.5 LTS |
| Frappe | v16 (version-16) |
| ERPNext | v16 (version-16) |
| Python | 3.14.6 |
| Node.js | 24.18.0 |
| MariaDB | 10.6 |
| nginx | 1.18.0 |
| Supervisor | 4.2.1 |

## Notas

- Instalación virgen — sin configurar aún (empresa, moneda, plan de cuentas, etc.)
- Reemplaza la instalación anterior con Docker (que tenía problemas de rendimiento)
- Este servidor es la base de la rama ERPNext del sistema industrial
