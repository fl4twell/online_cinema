import click
import os
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinema.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
    app.config['GOOGLE_DRIVE_API_KEY'] = os.environ.get('GOOGLE_DRIVE_API_KEY')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    with app.app_context():
        from app.models import User, Movie, Comment, Rating, seed_data
        db.create_all()
        seed_data()

    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        from app.models import seed_data
        db.create_all()
        seed_data()
        click.echo('База данных инициализирована и заполнена тестовыми данными.')

    from app.routes import main
    app.register_blueprint(main)

    return app