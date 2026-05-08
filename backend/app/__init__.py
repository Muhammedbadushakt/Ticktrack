from flask import Flask
from .config import Config
from .routes.base import base_bp
from .routes.auth import auth_bp
from .routes.student import student_bp
from .routes.classrep import classrep_bp
from .routes.admin import admin_bp
from .extension import db,mail

def create_app():
    app  = Flask(__name__,template_folder='../../frontend/templates')
    app.config.from_object(Config)
    db.init_app(app)
    mail.init_app(app)
    app.register_blueprint(base_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(classrep_bp)
    app.register_blueprint(admin_bp)  
    with app.app_context():
        db.create_all()


    return app