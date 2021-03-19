#
#  This script is the entry point to the flask application. The mod_wsgi inside apache will execute this script
#  to start the PTP flask application. We only start the virtual environment, set some python paths so libraries are in scope
#  and get the handler to the application. wsgi module always expect the a handler with the name 'application' 
#

activate_this = '/home/paco/AndroidStudioProjects/whatisgonnahappenserver/venv/bin/activate_this.py'
with open(activate_this) as f:
	exec(f.read(), {'__file__': activate_this})

import os
import sys

sys.path.append("/home/paco/AndroidStudioProjects/whatisgonnahappenserver/venv/lib64/python3.8/site-packages")
sys.path.append("/home/paco/AndroidStudioProjects/whatisgonnahappenserver")
sys.path.append("/home/paco/AndroidStudioProjects/whatisgonnahappenserver/app")

    
from main import app as application
