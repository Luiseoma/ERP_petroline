from flask import Flask
from datetime import timedelta

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.operador_routes import operador_bp

app = Flask(__name__)

# =======================
# CONFIGURACIÓN
# =======================

app.config["SECRET_KEY"] = "mi_clave_secreta"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)

# =======================
# REGISTRO DE BLUEPRINTS
# =======================

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(operador_bp)

# =======================
# RUN
# =======================

if __name__ == "__main__":
    app.run(debug=True)