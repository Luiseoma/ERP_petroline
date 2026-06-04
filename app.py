from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import mysql.connector
import random
import string

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'

# =======================
# UTILIDADES
# =======================

def generar_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysql123456',
        database='sistema_admin'
    )


def query_db(query, params=None, fetchone=False, commit=False, dict_cursor=True):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dict_cursor)

    cursor.execute(query, params or ())

    data = None
    if query.strip().lower().startswith("select"):
        data = cursor.fetchone() if fetchone else cursor.fetchall()

    if commit:
        conn.commit()

    cursor.close()
    conn.close()
    return data


# =======================
# AUTH DECORATORS
# =======================

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('rol') != role:
                return "Acceso denegado", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper


# =======================
# LOGIN
# =======================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        correo = request.form['username']
        password = request.form['password']

        user = query_db(
            "SELECT * FROM usuarios WHERE correo = %s",
            (correo,),
            fetchone=True
        )

        # =========================
        # VALIDACIÓN DE USUARIO
        # =========================
        if not user:
            return render_template('login.html', error='Credenciales incorrectas')

        # usuario inactivo
        if user['activo'] == 0:
            return render_template('login.html', error='Usuario desactivado')

        # contraseña incorrecta
        if not check_password_hash(user['password_hash'], password):
            return render_template('login.html', error='Credenciales incorrectas')

        # =========================
        # LOGIN OK
        # =========================
        session['user_id'] = user['id']
        session['user_name'] = user['nombre']
        session['rol'] = user['rol']

        # =========================
        # CAMBIO OBLIGATORIO DE PASSWORD
        # =========================
        if user['debe_cambiar_password'] == 1:
            return redirect(url_for('perfil'))

        # =========================
        # REDIRECCIÓN POR ROL
        # =========================
        if user['rol'] == 'Administrador':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('inicio_operador'))

    return render_template('login.html')

@app.route('/toggle_usuario/<int:id>')
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
    """, (nuevo_estado, id), commit=True)

    return redirect(url_for('usuarios'))


# =======================
# DASHBOARD ADMIN
# =======================

@app.route('/dashboard_admin')
@login_required
def dashboard():

    total = query_db("SELECT COUNT(*) AS total FROM usuarios", fetchone=True)['total']

    roles = query_db("""
        SELECT rol, COUNT(*) as cantidad
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
        'dashboard.html',
        total=total,
        roles=roles,
        ultimos=ultimos
    )


# =======================
# OPERADOR
# =======================

@app.route('/inicio')
@login_required
def inicio_operador():

    user_id = session['user_id']

    bombas = query_db(
        """
        SELECT *
        FROM bombas
        WHERE operador_id = %s
        """,
        (user_id,)
    )

    return render_template(
        "inicio_operador.html",
        bombas=bombas
    )

# =======================
# REGISTRO
# =======================
@app.route('/registro_diario/<int:bomba_id>', methods=['GET', 'POST'])
@login_required
def registro_diario(bomba_id):

    if request.method == 'POST':

        query_db("""
            INSERT INTO registro_diario (
                bomba_id,
                fecha,
                stock_93,
                stock_95,
                stock_pd,
                stock_ks,
                despacho_93,
                despacho_95,
                despacho_pd,
                despacho_ks,
                deposito,
                transbank,
                observaciones
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """, (
            bomba_id,
            date.today(),
            request.form['stock_93'],
            request.form['stock_95'],
            request.form['stock_pd'],
            request.form['stock_ks'],
            request.form['despacho_93'],
            request.form['despacho_95'],
            request.form['despacho_pd'],
            request.form['despacho_ks'],
            request.form['deposito'],
            request.form['transbank'],
            request.form['observaciones']
        ), commit=True)

        flash("Registro guardado correctamente")

        return redirect(
            url_for(
                'registro_diario',
                bomba_id=bomba_id
            )
        )

    bomba = query_db(
        """
        SELECT *
        FROM bombas
        WHERE id = %s
        """,
        (bomba_id,),
        fetchone=True
    )

    registros = query_db("""
        SELECT *
        FROM registro_diario
        WHERE bomba_id = %s
        ORDER BY fecha DESC
        LIMIT 15
    """, (
        bomba_id,
    ))

    return render_template(
        'registro_diario.html',
        bomba=bomba,
        fecha=date.today(),
        registros=registros
    )

# =======================
# ESTACIONES
# =======================

@app.route('/estaciones', methods=['GET', 'POST'])
@login_required
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
                SET nombre=%s, ubicacion=%s, operador_id=%s
                WHERE id=%s
            """, (nombre, ubicacion, operador_id, id_estacion), commit=True)

        else:
            query_db("""
                INSERT INTO bombas (nombre, ubicacion, operador_id)
                VALUES (%s, %s, %s)
            """, (nombre, ubicacion, operador_id), commit=True)

        return redirect(url_for('estaciones'))

    operadores = query_db("""
        SELECT id, nombre
        FROM usuarios
        WHERE rol = 'Operador'
        ORDER BY nombre
    """)

    if session['rol'] == 'Administrador':
        estaciones = query_db("""
            SELECT *
            FROM bombas
            ORDER BY nombre
        """)
    else:
        estaciones = query_db("""
            SELECT *
            FROM bombas
            WHERE operador_id = %s
            ORDER BY nombre
        """, (session['user_id'],))

    return render_template(
        'estaciones.html',
        estaciones=estaciones,
        estacion_editar=estacion_editar,
        operadores=operadores
    )


@app.route('/eliminar_estacion/<int:id>')
@login_required
def eliminar_estacion(id):
    query_db("DELETE FROM bombas WHERE id = %s", (id,), commit=True)
    return redirect(url_for('estaciones'))


# =======================
# USUARIOS
# =======================

@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def usuarios():

    editar_id = request.args.get('editar')
    usuario_editar = None

    # ======================
    # EDITAR (GET)
    # ======================
    if editar_id:
        usuario_editar = query_db(
            "SELECT * FROM usuarios WHERE id = %s",
            (editar_id,),
            fetchone=True
        )

    # ======================
    # CREAR / ACTUALIZAR (POST)
    # ======================
    if request.method == 'POST':

        user_id = request.form.get('id')

        nombre = request.form['nombre']
        correo = request.form['correo']
        rol = request.form['rol']

        # EDITAR
        if user_id:
            query_db("""
                UPDATE usuarios
                SET nombre=%s, correo=%s, rol=%s
                WHERE id=%s
            """, (nombre, correo, rol, user_id), commit=True)
            flash("Usuario actualizado correctamente")
        # CREAR
        else:
            temp_password = generar_password()

            query_db("""
                INSERT INTO usuarios (nombre, correo, password_hash, rol)
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

        return redirect(url_for('usuarios'))

    # ======================
    # LISTAR
    # ======================
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

@app.route('/eliminar_usuario/<int:id>')
@login_required
@role_required('Administrador')
def eliminar_usuario(id):

    query_db(
        "DELETE FROM usuarios WHERE id = %s",
        (id,),
        commit=True
    )

    return redirect(url_for('usuarios'))

# =======================
# PERFIL
# =======================

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():

    user = query_db(
        "SELECT * FROM usuarios WHERE id = %s",
        (session['user_id'],),
        fetchone=True
    )

    if request.method == 'POST':

        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('perfil'))

        if not check_password_hash(user['password_hash'], old_password):
            flash("Contraseña actual incorrecta")
            return redirect(url_for('perfil'))

        query_db("""
            UPDATE usuarios
            SET password_hash = %s,
                debe_cambiar_password = 0
            WHERE id = %s
        """, (
            generate_password_hash(new_password),
            user['id']
        ), commit=True)

        flash("Contraseña actualizada correctamente")
        return redirect(url_for('perfil'))

    return render_template(
        'perfil.html',
        usuario=user,
        primera_vez=user['debe_cambiar_password']
    )


# =======================
# LOGOUT
# =======================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# =======================
# RUN
# =======================

if __name__ == '__main__':
    app.run(debug=True)