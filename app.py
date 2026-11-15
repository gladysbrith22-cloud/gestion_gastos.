"""Control de Gastos Personales - Flask + SQLite."""
import csv
import io
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask, Response, abort, flash, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash

import db
from config import Config


def create_app(config_object=Config, test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)

    # ------------------------------------------------------------------ #
    # Seguridad: sesión, CSRF y cabeceras
    # ------------------------------------------------------------------ #
    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Debes iniciar sesión para continuar.", "warning")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def proteger_csrf():
        if request.method == "POST":
            token = session.get("_csrf")
            if not token or token != request.form.get("_csrf"):
                abort(400, "Token CSRF inválido.")

    @app.after_request
    def cabeceras(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        return resp

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    def validar_gasto(form):
        errores, datos = [], {}
        fecha = form.get("fecha", "").strip()
        descripcion = form.get("descripcion", "").strip()
        monto_txt = form.get("monto", "").strip().replace(",", ".")

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            datos["fecha"] = fecha
        except ValueError:
            errores.append("La fecha no es válida.")

        if not descripcion:
            errores.append("La descripción es obligatoria.")
        elif len(descripcion) > 120:
            errores.append("La descripción no puede superar 120 caracteres.")
        datos["descripcion"] = descripcion

        try:
            monto = round(float(monto_txt), 2)
            if monto <= 0:
                raise ValueError
            datos["monto"] = monto
        except ValueError:
            errores.append("El monto debe ser un número mayor que cero.")
        return datos, errores

    def filtrar(args):
        """Construye la cláusula WHERE a partir del rango de fechas."""
        desde, hasta = args.get("desde", ""), args.get("hasta", "")
        where, params = ["usuario_id = ?"], [session["user_id"]]
        if desde:
            where.append("fecha >= ?")
            params.append(desde)
        if hasta:
            where.append("fecha <= ?")
            params.append(hasta)
        return " AND ".join(where), params, desde, hasta

    # ------------------------------------------------------------------ #
    # Autenticación
    # ------------------------------------------------------------------ #
    @app.route("/")
    def index():
        return redirect(url_for("gastos" if "user_id" in session else "login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = db.get_db().execute(
                "SELECT * FROM usuarios WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("gastos"))
            flash("Usuario o contraseña incorrectos.", "danger")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("Sesión cerrada correctamente.", "success")
        return redirect(url_for("login"))

    # ------------------------------------------------------------------ #
    # Gastos (CRUD)
    # ------------------------------------------------------------------ #
    @app.route("/gastos")
    @login_required
    def gastos():
        where, params, desde, hasta = filtrar(request.args)
        filas = db.get_db().execute(
            f"SELECT * FROM gastos WHERE {where} ORDER BY fecha DESC, id DESC", params
        ).fetchall()
        total = sum(f["monto"] for f in filas)
        return render_template(
            "gastos.html", gastos=filas, total=total, desde=desde, hasta=hasta,
            hoy=date.today().isoformat(),
        )

    @app.route("/gastos/nuevo", methods=["POST"])
    @login_required
    def gasto_nuevo():
        datos, errores = validar_gasto(request.form)
        if errores:
            for e in errores:
                flash(e, "danger")
        else:
            conn = db.get_db()
            conn.execute(
                "INSERT INTO gastos (usuario_id, fecha, descripcion, monto) VALUES (?, ?, ?, ?)",
                (session["user_id"], datos["fecha"], datos["descripcion"], datos["monto"]),
            )
            conn.commit()
            flash("Gasto registrado correctamente.", "success")
        return redirect(url_for("gastos"))

    def obtener_gasto(gasto_id):
        fila = db.get_db().execute(
            "SELECT * FROM gastos WHERE id = ? AND usuario_id = ?",
            (gasto_id, session["user_id"]),
        ).fetchone()
        if fila is None:
            abort(404)
        return fila

    @app.route("/gastos/<int:gasto_id>/editar", methods=["GET", "POST"])
    @login_required
    def gasto_editar(gasto_id):
        gasto = obtener_gasto(gasto_id)
        if request.method == "POST":
            datos, errores = validar_gasto(request.form)
            if errores:
                for e in errores:
                    flash(e, "danger")
            else:
                conn = db.get_db()
                conn.execute(
                    "UPDATE gastos SET fecha = ?, descripcion = ?, monto = ? WHERE id = ?",
                    (datos["fecha"], datos["descripcion"], datos["monto"], gasto_id),
                )
                conn.commit()
                flash("Gasto actualizado.", "success")
                return redirect(url_for("gastos"))
        return render_template("editar.html", gasto=gasto)

    @app.route("/gastos/<int:gasto_id>/eliminar", methods=["POST"])
    @login_required
    def gasto_eliminar(gasto_id):
        obtener_gasto(gasto_id)
        conn = db.get_db()
        conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        conn.commit()
        flash("Gasto eliminado.", "success")
        return redirect(url_for("gastos"))

    # ------------------------------------------------------------------ #
    # Reportes
    # ------------------------------------------------------------------ #
    @app.route("/reporte")
    @login_required
    def reporte():
        where, params, desde, hasta = filtrar(request.args)
        conn = db.get_db()
        resumen = conn.execute(
            f"""SELECT COUNT(*) AS n, COALESCE(SUM(monto), 0) AS total,
                       COALESCE(AVG(monto), 0) AS promedio,
                       COALESCE(MAX(monto), 0) AS maximo
                FROM gastos WHERE {where}""", params,
        ).fetchone()
        por_mes = conn.execute(
            f"""SELECT substr(fecha, 1, 7) AS mes, COUNT(*) AS n, SUM(monto) AS total
                FROM gastos WHERE {where} GROUP BY mes ORDER BY mes""", params,
        ).fetchall()
        mayores = conn.execute(
            f"""SELECT * FROM gastos WHERE {where} ORDER BY monto DESC LIMIT 5""", params,
        ).fetchall()
        detalle = conn.execute(
            f"SELECT * FROM gastos WHERE {where} ORDER BY fecha, id", params
        ).fetchall()
        max_mes = max((m["total"] for m in por_mes), default=0)
        return render_template(
            "reporte.html", resumen=resumen, por_mes=por_mes, mayores=mayores,
            detalle=detalle, max_mes=max_mes, desde=desde, hasta=hasta,
            generado=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )

    @app.route("/reporte/exportar.csv")
    @login_required
    def exportar_csv():
        where, params, _, _ = filtrar(request.args)
        filas = db.get_db().execute(
            f"SELECT fecha, descripcion, monto FROM gastos WHERE {where} ORDER BY fecha", params
        ).fetchall()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["fecha", "descripcion", "monto"])
        for f in filas:
            writer.writerow([f["fecha"], f["descripcion"], f"{f['monto']:.2f}"])
        return Response(
            "\ufeff" + buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte_gastos.csv"},
        )

    @app.template_filter("moneda")
    def moneda(valor):
        return f"S/ {valor:,.2f}"

    @app.template_filter("fecha_es")
    def fecha_es(iso):
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
