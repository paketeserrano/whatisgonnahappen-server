from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://adminfan:admin@localhost/happen'
#app.config['SQLALCHEMY_ECHO'] = True
#app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)

login = LoginManager(app)
app.config['SECRET_KEY'] = "asdlasdjalskdjalksdjlaksjdlkasmd"

# CORS app configuration - Commented out until web is ready 
app.config['CORS_HEADERS'] = 'Content-Type'
#app.config['CORS_ORIGINS'] = 'http://localhost:46845'  #NOTE: Running in web from android studio changes this url in every run. There is a way to lunch from command line in chrome with a fixed port

