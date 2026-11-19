from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database import (
    HORARIOS_DESCANSO,
    asignar_servicio_a_peluquero,
    cambiar_estado_horario,
    cambiar_estado_peluquero,
    cambiar_estado_servicio,
    cancelar_turno,
    crear_horario,
    crear_peluquero,
    crear_servicio,
    crear_turno,
    editar_peluquero,
    editar_servicio,
    editar_turno,
    eliminar_horario,
    eliminar_peluquero,
    eliminar_peluquero_definitivo,
    eliminar_servicio,
    eliminar_servicio_definitivo,
    formatear_fecha,
    inicializar_base_de_datos,
    obtener_fecha_hoy_argentina,
    obtener_fechas_para_reserva,
    obtener_historial_turnos,
    obtener_horarios_disponibles,
    obtener_opciones_de_reserva,
    obtener_peluquero_por_id,
    obtener_peluqueros,
    obtener_peluqueros_activos,
    obtener_peluqueros_admin,
    obtener_peluqueros_con_servicios,
    obtener_servicio_por_id,
    obtener_servicios,
    obtener_servicios_admin,
    obtener_servicios_agrupados_por_peluquero_admin,
    obtener_todos_los_horarios_admin,
    obtener_turno_para_confirmacion,
    obtener_turno_por_id,
    obtener_turnos_admin,
    obtener_turnos_ocupados,
)
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["SECRET_KEY"] = "clave-solo-para-desarrollo"
ADMIN_PASSWORD = "LastMondayBarber2026"

UPLOAD_FOLDER = Path(__file__).parent / "static" / "uploads" / "peluqueros"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}


def archivo_permitido(nombre_archivo):
    """Comprueba si el archivo tiene una extensión de imagen permitida."""
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_foto_subida(archivo):
    """Guarda una foto subida y devuelve la ruta relativa para static."""
    if not archivo or not archivo.filename:
        return None
    if archivo_permitido(archivo.filename):
        nombre_seguro = secure_filename(archivo.filename)
        timestamp = int(datetime.now().timestamp())
        nombre_final = f"{timestamp}_{nombre_seguro}"
        destino = UPLOAD_FOLDER / nombre_final
        archivo.save(str(destino))
        return f"uploads/peluqueros/{nombre_final}"
    raise ValueError("El formato de la imagen no es válido. Usá PNG, JPG, JPEG, WEBP o SVG.")


inicializar_base_de_datos()


def requiere_admin(f):
    """Protege rutas administrativas requiriendo autenticación con contraseña."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("admin_autenticado"):
            flash("Debés iniciar sesión para acceder al panel de administración.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorada


def agrupar_servicios_por_peluquero(relaciones):
    """Agrupa los servicios para mostrarlos ordenados por peluquero."""
    peluqueros = {}

    for relacion in relaciones:
        nombre = relacion["peluquero"]
        peluqueros.setdefault(nombre, []).append(
            {
                "nombre": relacion["servicio"],
                "precio": relacion["precio"],
                "duracion": relacion["duracion"],
                "descripcion": relacion["descripcion"],
            }
        )

    return peluqueros


def contexto_de_turnos(datos=None, paso=1, error=None):
    """Prepara los datos que necesita la interfaz de reserva."""
    opciones = [dict(opcion) for opcion in obtener_opciones_de_reserva()]
    ocupados = [dict(turno) for turno in obtener_turnos_ocupados()]

    return {
        "peluqueros": obtener_peluqueros(),
        "fechas": obtener_fechas_para_reserva(),
        "horarios": obtener_horarios_disponibles(),
        "descanso": HORARIOS_DESCANSO,
        "opciones": opciones,
        "ocupados": ocupados,
        "datos": datos or {},
        "paso": paso,
        "error": error,
    }


# ==============================================================================
# RUTAS PÚBLICAS
# ==============================================================================

@app.route("/")
def inicio():
    """Muestra los servicios disponibles para cada peluquero."""
    relaciones = obtener_peluqueros_con_servicios()
    peluqueros = agrupar_servicios_por_peluquero(relaciones)
    return render_template("index.html", peluqueros=peluqueros)


@app.route("/peluqueros", methods=["GET", "POST"])
def administrar_peluqueros():
    """Permite asignar un servicio y un precio a un peluquero."""
    if request.method == "POST":
        try:
            peluquero_id = int(request.form["peluquero_id"])
            servicio_id = int(request.form["servicio_id"])
            precio = int(request.form["precio"])
            asignar_servicio_a_peluquero(peluquero_id, servicio_id, precio)
            flash("El servicio y su precio fueron guardados.", "success")
            return redirect(url_for("administrar_peluqueros"))
        except (KeyError, ValueError):
            flash("Elegí un peluquero, un servicio y un precio mayor que cero.", "error")

    return render_template(
        "peluqueros.html",
        peluqueros=obtener_peluqueros(),
        servicios=obtener_servicios(),
        relaciones=obtener_peluqueros_con_servicios(),
    )


@app.route("/turnos", methods=["GET", "POST"])
def administrar_turnos():
    """Muestra el flujo de reserva y guarda el turno solo al confirmarlo."""
    if request.method == "POST":
        datos = request.form.to_dict()
        try:
            turno_id = crear_turno(
                int(datos.get("peluquero_id", "")),
                int(datos.get("servicio_id", "")),
                datos.get("fecha", ""),
                datos.get("hora", ""),
                datos.get("nombre", ""),
                datos.get("apellido", ""),
                datos.get("telefono", ""),
            )
            return redirect(url_for("confirmacion_turno", turno_id=turno_id))
        except ValueError as error:
            paso = 2 if "horario" in str(error).lower() or "fecha" in str(error).lower() or "lunes" in str(error).lower() else 3
            return render_template(
                "turnos.html", **contexto_de_turnos(datos, paso, str(error))
            ), 400

    return render_template("turnos.html", **contexto_de_turnos())


@app.route("/turnos/confirmacion/<int:turno_id>")
def confirmacion_turno(turno_id):
    """Muestra la confirmación sin exponer los datos personales del cliente."""
    turno = obtener_turno_para_confirmacion(turno_id)
    if turno is None:
        abort(404)

    return render_template(
        "confirmacion_turno.html",
        turno=turno,
        fecha_formateada=formatear_fecha(turno["fecha"]),
    )


# ==============================================================================
# AUTENTICACIÓN ADMINISTRATIVA
# ==============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Inicio de sesión protegido para administración."""
    if session.get("admin_autenticado"):
        return redirect(url_for("admin_turnos"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_autenticado"] = True
            flash("Sesión iniciada con éxito.", "success")
            return redirect(url_for("admin_turnos"))
        flash("Contraseña incorrecta.", "error")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    """Cierra la sesión del administrador."""
    session.pop("admin_autenticado", None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@requiere_admin
def admin_inicio():
    """Redirige al panel principal de agenda."""
    return redirect(url_for("admin_turnos"))


# ==============================================================================
# PANEL DE ADMINISTRACIÓN: AGENDA Y TURNOS
# ==============================================================================

@app.route("/admin/turnos")
@requiere_admin
def admin_turnos():
    """Muestra la agenda de turnos con filtro opcional por fecha (hoy y futuros)."""
    filtro_fecha = request.args.get("fecha", "").strip() or None
    turnos = obtener_turnos_admin(filtro_fecha)
    hoy = obtener_fecha_hoy_argentina()
    return render_template(
        "admin/turnos.html",
        turnos=turnos,
        filtro_fecha=filtro_fecha or "",
        hoy=hoy,
    )


@app.route("/admin/historial")
@requiere_admin
def admin_historial():
    """Muestra la sección independiente con el historial de turnos pasados."""
    filtro_fecha = request.args.get("fecha", "").strip() or None
    turnos = obtener_historial_turnos(filtro_fecha)
    hoy = obtener_fecha_hoy_argentina()
    return render_template(
        "admin/historial.html",
        turnos=turnos,
        filtro_fecha=filtro_fecha or "",
        hoy=hoy,
    )


@app.route("/admin/turnos/cancelar/<int:turno_id>", methods=["POST"])
@requiere_admin
def admin_cancelar_turno(turno_id):
    """Cancela un turno liberando el horario."""
    cancelar_turno(turno_id)
    flash(f"El turno fue cancelado exitosamente.", "success")
    filtro_fecha = request.args.get("fecha", "")
    return redirect(url_for("admin_turnos", fecha=filtro_fecha))


@app.route("/admin/turnos/editar/<int:turno_id>", methods=["GET", "POST"])
@requiere_admin
def admin_editar_turno(turno_id):
    """Permite corregir la fecha y la hora de un turno."""
    turno = obtener_turno_por_id(turno_id)
    if turno is None:
        abort(404)

    if request.method == "POST":
        nueva_fecha = request.form.get("fecha", "").strip()
        nueva_hora = request.form.get("hora", "").strip()
        try:
            editar_turno(turno_id, nueva_fecha, nueva_hora)
            flash("El turno fue modificado con éxito.", "success")
            return redirect(url_for("admin_turnos"))
        except ValueError as error:
            flash(str(error), "error")

    horarios = obtener_horarios_disponibles()
    return render_template("admin/editar_turno.html", turno=turno, horarios=horarios)


# ==============================================================================
# PANEL DE ADMINISTRACIÓN: HORARIOS DISPONIBLES
# ==============================================================================

@app.route("/admin/horarios", methods=["GET", "POST"])
@requiere_admin
def admin_horarios():
    """Permite ver, agregar y administrar horarios disponibles."""
    if request.method == "POST":
        hora = request.form.get("hora", "").strip()
        dia = request.form.get("dia", "general").strip()
        try:
            crear_horario(hora, dia)
            flash(f"El horario {hora} fue agregado exitosamente.", "success")
            return redirect(url_for("admin_horarios"))
        except ValueError as error:
            flash(str(error), "error")

    horarios = obtener_todos_los_horarios_admin()
    return render_template("admin/horarios.html", horarios=horarios)


@app.route("/admin/horarios/estado/<int:horario_id>", methods=["POST"])
@requiere_admin
def admin_cambiar_estado_horario(horario_id):
    """Activa o desactiva un horario."""
    activo = request.form.get("activo") == "1"
    cambiar_estado_horario(horario_id, activo)
    flash("El estado del horario fue actualizado.", "success")
    return redirect(url_for("admin_horarios"))


@app.route("/admin/horarios/eliminar/<int:horario_id>", methods=["POST"])
@requiere_admin
def admin_eliminar_horario(horario_id):
    """Desactiva o elimina un horario disponible."""
    eliminar_horario(horario_id)
    flash("El horario fue desactivado del sistema.", "success")
    return redirect(url_for("admin_horarios"))


# ==============================================================================
# PANEL DE ADMINISTRACIÓN: SERVICIOS
# ==============================================================================

@app.route("/admin/servicios", methods=["GET", "POST"])
@requiere_admin
def admin_servicios():
    """Permite listar y agregar nuevos servicios asignando obligatoriamente un peluquero."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        try:
            precio = int(request.form.get("precio", ""))
            duracion = int(request.form.get("duracion", "30"))
            peluquero_id = int(request.form.get("peluquero_id", ""))
            descripcion = request.form.get("descripcion", "").strip()
            crear_servicio(nombre, precio, duracion, peluquero_id, descripcion)
            flash(f"El servicio '{nombre}' fue creado y ya está disponible para reservas.", "success")
            return redirect(url_for("admin_servicios"))
        except (TypeError, ValueError) as error:
            mensaje = str(error) if "El" in str(error) or "Ya" in str(error) or "Debés" in str(error) else "Completá valores válidos para el servicio y seleccioná un peluquero."
            flash(mensaje, "error")

    servicios = obtener_servicios_admin()
    peluqueros = obtener_peluqueros_activos()
    peluqueros_con_servicios = obtener_servicios_agrupados_por_peluquero_admin()
    return render_template(
        "admin/servicios.html",
        servicios=servicios,
        peluqueros=peluqueros,
        peluqueros_con_servicios=peluqueros_con_servicios,
    )


@app.route("/admin/servicios/eliminar-definitivo/<int:servicio_id>", methods=["POST"])
@requiere_admin
def admin_eliminar_servicio_definitivo(servicio_id):
    """Elimina definitivamente un servicio de la base de datos conservando sus turnos históricos intactos."""
    servicio = obtener_servicio_por_id(servicio_id)
    nombre = servicio["nombre"] if servicio else "Servicio"
    try:
        eliminar_servicio_definitivo(servicio_id)
        flash(f"El servicio '{nombre}' fue eliminado definitivamente. Los turnos históricos se conservan intactos.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin_servicios"))


@app.route("/admin/servicios/editar/<int:servicio_id>", methods=["GET", "POST"])
@requiere_admin
def admin_editar_servicio(servicio_id):
    """Permite editar nombre, precio, duración, peluquero asignado y descripción de un servicio."""
    servicio = obtener_servicio_por_id(servicio_id)
    if servicio is None:
        abort(404)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        try:
            precio = int(request.form.get("precio", ""))
            duracion = int(request.form.get("duracion", "30"))
            peluquero_id = int(request.form.get("peluquero_id", ""))
            descripcion = request.form.get("descripcion", "").strip()
            activo = request.form.get("activo") == "1"
            editar_servicio(servicio_id, nombre, precio, duracion, peluquero_id, descripcion, activo)
            flash(f"El servicio '{nombre}' fue actualizado correctamente.", "success")
            return redirect(url_for("admin_servicios"))
        except (TypeError, ValueError) as error:
            mensaje = str(error) if "El" in str(error) or "Ya" in str(error) or "Debés" in str(error) else "Completá valores válidos para el servicio."
            flash(mensaje, "error")

    peluqueros = obtener_peluqueros_activos()
    return render_template("admin/editar_servicio.html", servicio=servicio, peluqueros=peluqueros)


@app.route("/admin/servicios/estado/<int:servicio_id>", methods=["POST"])
@requiere_admin
def admin_cambiar_estado_servicio(servicio_id):
    """Activa o desactiva un servicio."""
    activo = request.form.get("activo") == "1"
    cambiar_estado_servicio(servicio_id, activo)
    flash("El estado del servicio fue actualizado.", "success")
    return redirect(url_for("admin_servicios"))


@app.route("/admin/servicios/eliminar/<int:servicio_id>", methods=["POST"])
@requiere_admin
def admin_eliminar_servicio(servicio_id):
    """Desactiva un servicio de forma segura (conservando turnos históricos)."""
    eliminar_servicio(servicio_id)
    flash("El servicio fue desactivado (los turnos históricos se conservan).", "success")
    return redirect(url_for("admin_servicios"))


# ==============================================================================
# PANEL DE ADMINISTRACIÓN: GESTIÓN DE PELUQUEROS
# ==============================================================================

@app.route("/admin/peluqueros", methods=["GET", "POST"])
@requiere_admin
def admin_peluqueros():
    """Permite ver, agregar y administrar a los peluqueros con foto opcional."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        foto_archivo = request.files.get("foto")
        try:
            foto_ruta = guardar_foto_subida(foto_archivo) if foto_archivo and foto_archivo.filename else None
            crear_peluquero(nombre, descripcion, foto=foto_ruta)
            flash(f"El peluquero '{nombre}' fue agregado exitosamente.", "success")
            return redirect(url_for("admin_peluqueros"))
        except ValueError as error:
            flash(str(error), "error")

    peluqueros = obtener_peluqueros_admin()
    return render_template("admin/peluqueros.html", peluqueros=peluqueros)


@app.route("/admin/peluqueros/editar/<int:peluquero_id>", methods=["GET", "POST"])
@requiere_admin
def admin_editar_peluquero(peluquero_id):
    """Permite editar el nombre, foto e información de un peluquero."""
    peluquero = obtener_peluquero_por_id(peluquero_id)
    if peluquero is None:
        abort(404)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        activo = request.form.get("activo") == "1"
        eliminar_foto = request.form.get("eliminar_foto") == "1"
        foto_archivo = request.files.get("foto")

        try:
            foto_ruta = None
            if not eliminar_foto and foto_archivo and foto_archivo.filename:
                foto_ruta = guardar_foto_subida(foto_archivo)

            editar_peluquero(
                peluquero_id,
                nombre,
                descripcion,
                foto=foto_ruta,
                activo=activo,
                eliminar_foto=eliminar_foto,
            )
            flash(f"El peluquero '{nombre}' fue actualizado correctamente.", "success")
            return redirect(url_for("admin_peluqueros"))
        except ValueError as error:
            flash(str(error), "error")

    return render_template("admin/editar_peluquero.html", peluquero=peluquero)


@app.route("/admin/peluqueros/estado/<int:peluquero_id>", methods=["POST"])
@requiere_admin
def admin_cambiar_estado_peluquero(peluquero_id):
    """Activa o desactiva un peluquero."""
    activo = request.form.get("activo") == "1"
    cambiar_estado_peluquero(peluquero_id, activo)
    flash("El estado del peluquero fue actualizado.", "success")
    return redirect(url_for("admin_peluqueros"))


@app.route("/admin/peluqueros/eliminar/<int:peluquero_id>", methods=["POST"])
@requiere_admin
def admin_eliminar_peluquero(peluquero_id):
    """Desactiva un peluquero de forma segura (los turnos históricos se conservan)."""
    peluquero = obtener_peluquero_por_id(peluquero_id)
    nombre = peluquero["nombre"] if peluquero else "Peluquero"
    eliminar_peluquero(peluquero_id)
    flash(f"El peluquero '{nombre}' fue desactivado del sistema (su historial de turnos se conserva intacto).", "success")
    return redirect(url_for("admin_peluqueros"))


@app.route("/admin/peluqueros/eliminar-definitivo/<int:peluquero_id>", methods=["POST"])
@requiere_admin
def admin_eliminar_peluquero_definitivo(peluquero_id):
    """Elimina definitivamente un peluquero de la base de datos conservando sus turnos históricos intactos."""
    peluquero = obtener_peluquero_por_id(peluquero_id)
    nombre = peluquero["nombre"] if peluquero else "Peluquero"
    try:
        eliminar_peluquero_definitivo(peluquero_id)
        flash(f"El peluquero '{nombre}' y sus servicios fueron eliminados definitivamente. El historial de turnos se conserva intacto.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin_peluqueros"))


if __name__ == "__main__":
    app.run(debug=True)
