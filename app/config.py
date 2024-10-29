from flask import Flask
from flask_login import LoginManager, logout_user, login_user

UPLOAD_FOLDER = 'app/static/uploads'
app = Flask(__name__)
app.config["SECRET_KEY"] = "<KEY>"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login = LoginManager(app)
login.login_view = 'login'