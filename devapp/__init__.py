from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from devapp import config
from flask_mail import Mail

csrf = CSRFProtect()
mail = Mail()


def create_app():
    """keep all imports that may cause conflict within this function so that anytime we write from
    devapp... import... none of these statements will be executed."""

    from devapp.models import db
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)
    app.config.from_object(config.DevelopmentConfig)
    mail.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    migrate = Migrate(app, db)
    return app


app = create_app()
from devapp import user_routes, admin_routes, forms

