import os
import logging
import traceback

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from logging.config import dictConfig

from .helpers.generic import EnvVarParser

force_new_db = EnvVarParser.get_boolean_from_env("FORCE_NEW_DB", False)

permanent_storage_path = '/mnt/mounted_volume/permanentstorage/'

logFilename = os.path.join(permanent_storage_path, "logs", "server.log")
os.makedirs(os.path.dirname(logFilename), exist_ok=True)

dictConfig({
    'version': 1,
    'disable_existing_loggers' : False,
    'formatters': {
        'default': {
            'format': '{0} {1} in {2}: {3}'.format('[%(asctime)s]', '%(levelname)s', '%(module)s', '%(message)s')
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        },
        'file': {
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': logFilename,
            'formatter': 'default',
            'level': 'INFO',
            'when': 'midnight',
            'interval': 1
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console','file']
    }
})

rootLogger = logging.getLogger()
allLoggers = ["gunicorn.access", "gunicorn.error"]

for loggo in allLoggers:
    logging.getLogger(loggo).handlers = rootLogger.handlers

logging.info("Logging is initialised to {0}".format(logFilename))

db = SQLAlchemy()

class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    # SECRET_KEY = os.urandom(24)
    SECRET_KEY = os.getenv("SERVER_SECRET_KEY")

    # Flask-SQLAlchemy settings
    is_sqlite_db = True
    if is_sqlite_db:
        # db_base_dir = permanent_storage_path
        db_base_dir = "/app/"
        db_name = os.getenv("SQLITE_DB_NAME", "my_app")
        db_path = os.path.join(db_base_dir, db_name + ".db")

        SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(db_path)

        # SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {'timeout': 45}}
    else:
        postgres_dict = {}
        postgres_dict["user"] =     None
        postgres_dict["password"] = None
        postgres_dict["host"] =     None
        postgres_dict["name"] =     None
        if postgres_dict['user'] and postgres_dict['password']:
            SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}/{}'.format(
                postgres_dict['user'],
                postgres_dict['password'],
                postgres_dict['host'],
                postgres_dict['name']
            )
        else:
            SQLALCHEMY_DATABASE_URI = 'postgresql://{}/{}'.format(postgres_dict['host'], postgres_dict['name'])

        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {'sslmode': "require"}}

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-User settings
    USER_APP_NAME = "My App" 
    USER_ENABLE_EMAIL = True    
    USER_ENABLE_USERNAME = False
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

def create_app():
    app = Flask(__name__, static_url_path='')

    conf_obj = ConfigClass()
    app.config.from_object(conf_obj)
    # app.config.from_object(__name__+'.ConfigClass')

    if conf_obj.is_sqlite_db:
        exist_previous_db = False
        if os.path.isfile(conf_obj.db_path):
            exist_previous_db = True
            if force_new_db:
                os.remove(conf_obj.db_path)
                exist_previous_db = False
    else:
        exist_previous_db = False

    from .models import User, Role, UserRoles

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    user_manager = UserManager(app, db, User)

    # blueprint for auth routes in our app
    from .server_auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .server_main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    if not exist_previous_db:
        with app.app_context():
            db.create_all()        
            # db.create_all(app=app)
            create_admin(user_manager)

    return app
def create_admin(input_user_manager):
    from .models import User, Role, UserRoles

    admin_email = 'admin@example.com'
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not User.query.filter(User.email == admin_email).first():
        user = User(
            email=admin_email,
            email_confirmed_at=datetime.utcnow(),
            name="One And Only Admin",
            password=generate_password_hash(admin_password)
            # password=input_user_manager.hash_password(admin_password)
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()

app = create_app()

def api_error(typ = "", msg = "", traceback = ""):
    error = {}
    error["type"] = typ
    error["message"] = msg
    error["traceback"] = traceback

    return error
def api_response(success, result, main_message = "", error = {}):
    status = {
        'success': success,
        'message': main_message,
        'error': error
    }

    response = {"Result": result, "Status": status}

    return response

@app.errorhandler(Exception)
def handle_error(error):

    tb_message = 'Error traceback ->\n' + ''.join(traceback.format_tb(error.__traceback__))
    logging.error(tb_message)
        
    logging.error(error)
    message = "\n".join([str(x) for x in error.args])
    status_code = 500
    if hasattr(error, 'status_code'):
        status_code = error.status_code
    
    response = api_response(False, {}, "", api_error(error.__class__.__name__, message, tb_message))

    return jsonify(response), status_code


if __name__ == "__main__":
    app.run(host='0.0.0.0')
