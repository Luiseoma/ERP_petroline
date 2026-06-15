from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
import os
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.operador_routes import operador_bp

load_dotenv()
app = Flask(__name__)

# =======================
# CONFIGURACIÓN
# =======================

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
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
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")