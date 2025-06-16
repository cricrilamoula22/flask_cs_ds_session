from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import Config
import uuid

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Session(app)

    from app.selection.routes import selection_bp
    app.register_blueprint(selection_bp)

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

    return app
