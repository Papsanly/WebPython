from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from .models import db, User

login_manager = LoginManager()
login_manager.login_view = "main.login_view"


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(f"config.{config_name.capitalize()}Config")

    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

        # Example user creation
        try:
            user = User(username="user", email="user@example.com")
            user.set_password("userpassword")
            db.session.add(user)

            admin = User(username="admin", email="admin@example.com", is_staff=True)
            admin.set_password("adminpassword")
            db.session.add(admin)

            db.session.commit()
        except Exception as e:
            pass

    from .views import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app
