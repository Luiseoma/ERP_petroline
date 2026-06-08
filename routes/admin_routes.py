from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash

from utils.db import query_db
from utils.decorators import (
    login_required,
    role_required
)
from utils.helpers import generar_password


admin_bp = Blueprint(
    'admin',
    __name__
)


# =======================
# INICIO ADMIN
# =======================

@admin_bp.route('/inicio_admin')
@login_required
@role_required('Administrador')
def inicio_admin():
    return render_template('dashboard_admin.html')


# =======================
# DASHBOARD
# =======================

@admin_bp.route('/dashboard_admin')
@login_required
@role_required('Administrador')
def dashboard():

    total = query_db(
        "SELECT COUNT(*) AS total FROM usuarios",
        fetchone=True
    )['total']

    roles = query_db("""
        SELECT rol, COUNT(*) AS cantidad
        FROM usuarios
        GROUP BY rol
    """)

    ultimos = query_db("""
        SELECT nombre, correo, rol
        FROM usuarios
        ORDER BY id DESC
        LIMIT 5
    """)

    return render_template(
        'dashboard_admin.html',
        total=total,
        roles=roles,
        ultimos=ultimos
    )


# =======================
# USUARIOS
# =======================

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def usuarios():

    editar_id = request.args.get('editar')
    usuario_editar = None

    if editar_id:
        usuario_editar = query_db(
            "SELECT * FROM usuarios WHERE id = %s",
            (editar_id,),
            fetchone=True
        )

    if request.method == 'POST':

        user_id = request.form.get('id')

        nombre = request.form['nombre']
        correo = request.form['correo']
        rol = request.form['rol']

        # EDITAR
        if user_id:

            query_db("""
                UPDATE usuarios
                SET nombre=%s,
                    correo=%s,
                    rol=%s
                WHERE id=%s
            """, (
                nombre,
                correo,
                rol,
                user_id
            ), commit=True)

            flash("Usuario actualizado correctamente")

        # CREAR
        else:

            temp_password = generar_password()

            query_db("""
                INSERT INTO usuarios (
                    nombre,
                    correo,
                    password_hash,
                    rol
                )
                VALUES (%s, %s, %s, %s)
            """, (
                nombre,
                correo,
                generate_password_hash(temp_password),
                rol
            ), commit=True)

            flash(
                f"Usuario creado correctamente. Contraseña temporal: {temp_password}"
            )

        return redirect(url_for('admin.usuarios'))

    users = query_db("""
        SELECT *
        FROM usuarios
        ORDER BY
            CASE
                WHEN rol = 'Administrador' THEN 1
                ELSE 2
            END,
            nombre ASC
    """)

    return render_template(
        'usuarios.html',
        usuarios=users,
        usuario_editar=usuario_editar
    )


@admin_bp.route('/toggle_usuario/<int:id>')
@login_required
@role_required('Administrador')
def toggle_usuario(id):

    user = query_db(
        "SELECT activo FROM usuarios WHERE id = %s",
        (id,),
        fetchone=True
    )

    nuevo_estado = 0 if user['activo'] == 1 else 1

    query_db("""
        UPDATE usuarios
        SET activo = %s
        WHERE id = %s
    """, (
        nuevo_estado,
        id
    ), commit=True)

    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/eliminar_usuario/<int:id>')
@login_required
@role_required('Administrador')
def eliminar_usuario(id):

    query_db(
        "DELETE FROM usuarios WHERE id = %s",
        (id,),
        commit=True
    )

    return redirect(url_for('admin.usuarios'))


# =======================
# ESTACIONES
# =======================

@admin_bp.route('/estaciones', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def estaciones():

    editar_id = request.args.get('editar')

    estacion_editar = None

    if editar_id:
        estacion_editar = query_db(
            "SELECT * FROM bombas WHERE id = %s",
            (editar_id,),
            fetchone=True
        )

    if request.method == 'POST':

        nombre = request.form['nombre']
        ubicacion = request.form['ubicacion']
        operador_id = request.form['operador_id']
        id_estacion = request.form.get('id')

        if id_estacion:

            query_db("""
                UPDATE bombas
                SET nombre=%s,
                    ubicacion=%s,
                    operador_id=%s
                WHERE id=%s
            """, (
                nombre,
                ubicacion,
                operador_id,
                id_estacion
            ), commit=True)

        else:

            query_db("""
                INSERT INTO bombas (
                    nombre,
                    ubicacion,
                    operador_id
                )
                VALUES (%s, %s, %s)
            """, (
                nombre,
                ubicacion,
                operador_id
            ), commit=True)

        return redirect(url_for('admin.estaciones'))

    operadores = query_db("""
        SELECT id, nombre
        FROM usuarios
        WHERE rol = 'Operador'
        ORDER BY nombre
    """)

    estaciones = query_db("""
        SELECT *
        FROM bombas
        ORDER BY nombre
    """)

    return render_template(
        'estaciones.html',
        estaciones=estaciones,
        estacion_editar=estacion_editar,
        operadores=operadores
    )


@admin_bp.route('/eliminar_estacion/<int:id>')
@login_required
@role_required('Administrador')
def eliminar_estacion(id):

    query_db(
        "DELETE FROM bombas WHERE id = %s",
        (id,),
        commit=True
    )

    return redirect(url_for('admin.estaciones'))