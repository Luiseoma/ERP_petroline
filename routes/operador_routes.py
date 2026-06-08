from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from datetime import date

from utils.db import query_db
from utils.decorators import (
    login_required,
    role_required
)


operador_bp = Blueprint(
    'operador',
    __name__
)


# =======================
# INICIO OPERADOR
# =======================

@operador_bp.route('/dashboard_operador')
@login_required
@role_required('Operador')
def dashboard_operador():

    user_id = session['user_id']

    bombas = query_db("""
        SELECT *
        FROM bombas
        WHERE operador_id = %s
    """, (
        user_id,
    ))

    return render_template(
        'operador/dashboard_operador.html',
        bombas=bombas
    )


# =======================
# REGISTRO DIARIO
# =======================

@operador_bp.route(
    '/registro_diario/<int:bomba_id>',
    methods=['GET', 'POST']
)
@login_required
@role_required('Operador')
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
                'operador/registro_diario.html',
                bomba_id=bomba_id
            )
        )

    bomba = query_db("""
        SELECT *
        FROM bombas
        WHERE id = %s
    """, (
        bomba_id,
    ), fetchone=True)

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
        'operador/registro_diario.html',
        bomba=bomba,
        fecha=date.today(),
        registros=registros
    )