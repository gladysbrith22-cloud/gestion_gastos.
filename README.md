# 💼 Control de Gastos

Aplicación web para **registrar gastos personales** (fecha, descripción y monto) y **generar reportes**, desarrollada con **Python, Flask y SQLite**. El acceso está protegido mediante inicio de sesión.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-black) ![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

---

## 📌 Características

- **Autenticación** con usuario y contraseña (contraseña almacenada como *hash*, nunca en texto plano).
- **CRUD de gastos**: registrar, listar, editar y eliminar.
- **Filtro por rango de fechas** en el historial y en el reporte.
- **Reporte** con total, número de gastos, promedio, gasto máximo, gasto por mes, Top 5 y detalle completo.
- **Exportación a CSV** (compatible con Excel) e **impresión / PDF** del reporte.
- **Seguridad**: protección CSRF, consultas SQL parametrizadas (previene inyección SQL), sesiones con cookies `HttpOnly`, validación de datos en servidor y aislamiento de datos por usuario.
- **Pruebas automáticas** con `unittest`.

## 🔐 Credenciales de acceso

| Usuario | Contraseña |
|---------|------------|
| `admin` | `123`      |

> Son credenciales de demostración definidas por el enunciado. En un entorno real deben cambiarse y la variable `SECRET_KEY` debe configurarse mediante entorno.

---

## 🖼️ Capturas y funcionamiento

### 1. Inicio de sesión
La aplicación exige autenticación: cualquier ruta protegida redirige al login.

![Login](docs/01-login.png)

Si las credenciales son incorrectas, se muestra un mensaje de error y no se concede el acceso.

![Login con error](docs/02-login-error.png)

### 2. Registro de gastos
Tras ingresar con `admin / 123` se accede al módulo de gastos. Desde el formulario **Nuevo gasto** se registran la **fecha**, la **descripción** y el **monto**.

![Gastos vacío](docs/03-gastos-vacio.png)

### 3. Historial de gastos
Cada registro se guarda en SQLite y aparece en el historial, ordenado del más reciente al más antiguo, con el **total acumulado**. Permite filtrar por fechas, **editar** y **eliminar** (con confirmación).

![Listado de gastos](docs/04-gastos-listado.png)

### 4. Edición de un gasto

![Editar gasto](docs/05-editar.png)

### 5. Reporte de gastos
El módulo **Reporte** resume la información: indicadores principales, gasto mensual, los 5 gastos más altos y el detalle completo. Incluye los botones **Exportar CSV** e **Imprimir / PDF**.

![Reporte](docs/06-reporte.png)

   ### 6. Reporte filtrado por periodo
   Con el filtro *Desde / Hasta* el reporte se recalcula solo para el periodo elegido (ejemplo: noviembre de 2026).

   ![Reporte filtrado](docs/07-reporte-filtrado.png)


---

## 🧱 Arquitectura y estructura del proyecto

```
control-gastos/
├── app.py              # Aplicación Flask: rutas, validaciones, seguridad y reportes
├── config.py           # Configuración (clave secreta, BD, credenciales iniciales)
├── db.py               # Acceso a datos SQLite: esquema, conexión y usuario inicial
├── requirements.txt    # Dependencias
├── templates/          # Plantillas Jinja2 (base, login, gastos, editar, reporte)
├── static/style.css    # Estilos (incluye estilos de impresión)
├── tests/test_app.py   # Pruebas automáticas
└── docs/               # Capturas de pantalla usadas en este README
```

### Modelo de datos

```sql
usuarios (id PK, username UNIQUE, password_hash)
gastos   (id PK, usuario_id FK -> usuarios, fecha TEXT ISO, descripcion TEXT,
          monto REAL CHECK (monto > 0), creado_en TIMESTAMP)
```

### Rutas principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/login` | Inicio de sesión |
| POST | `/logout` | Cierre de sesión |
| GET | `/gastos` | Historial con filtro por fechas |
| POST | `/gastos/nuevo` | Registrar gasto |
| GET/POST | `/gastos/<id>/editar` | Editar gasto |
| POST | `/gastos/<id>/eliminar` | Eliminar gasto |
| GET | `/reporte` | Reporte con indicadores |
| GET | `/reporte/exportar.csv` | Descarga del reporte en CSV |

---

## ▶️ Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/control-gastos.git
cd control-gastos

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Abrir en el navegador: **http://127.0.0.1:5000** e ingresar con `admin` / `123`.

La base de datos `instance/gastos.db` y el usuario administrador se crean automáticamente en la primera ejecución.

## ✅ Pruebas

```bash
python -m unittest discover -s tests -v
```

Cubren: login correcto/incorrecto, protección de rutas, rechazo de peticiones sin token CSRF, flujo completo (crear → editar → reporte → CSV → eliminar), validaciones y filtro por fechas.

## 🛠️ Tecnologías

Python 3 · Flask · SQLite · Jinja2 · HTML5 · CSS3

## 👤 Autora

**Gladys Beatriz Sacaca Machaca**
