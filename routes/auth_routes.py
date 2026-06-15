from flask import (Blueprint, render_template, request, redirect, url_for, session, flash)
from werkzeug.security import (generate_password_hash, check_password_hash)
from utils.db import query_db
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

# =======================
# INDEX
# =======================

@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


# =======================
# LOGIN
# =======================

@auth_bp.route('/login', methods=['GET', 'POST'])
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

        session.permanent = True

        # =========================
        # CAMBIO OBLIGATORIO DE PASSWORD
        # =========================
        if user['debe_cambiar_password'] == 1:
            return redirect(url_for('auth.perfil'))

        # =========================
        # REDIRECCIÓN POR ROL
        # =========================
        if user['rol'] == 'Administrador':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('operador.dashboard_operador'))

    return render_template('login.html')

# =======================
# PERFIL
# =======================

@auth_bp.route('/perfil', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.perfil'))

        if not check_password_hash(user['password_hash'], old_password):
            flash("Contraseña actual incorrecta")
            return redirect(url_for('auth.perfil'))

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
        return redirect(url_for('auth.perfil'))

    return render_template(
        'shared/perfil.html',
        usuario=user,
        primera_vez=user['debe_cambiar_password']
    )


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))