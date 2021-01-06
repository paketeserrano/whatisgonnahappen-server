from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://adminfan:admin@localhost/happen'
db = SQLAlchemy(app)

login = LoginManager(app)
app.config['SECRET_KEY'] = "asdlasdjalskdjalksdjlaksjdlkasmd"
