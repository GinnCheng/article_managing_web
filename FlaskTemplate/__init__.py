"""
The flask application package.
"""

import os
from flask import Flask
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.config["CLIENT_ID"] = os.environ.get("CLIENT_ID")
app.config["CLIENT_SECRET"] = os.environ.get("CLIENT_SECRET")
app.config["AUTHORITY"] = "https://login.microsoftonline.com/ae350ee1-7809-4ba5-bfb3-3fa9408e9a88"
app.config["REDIRECT_PATH"] = "/getAToken"  # Redirect URI you registered in Azure AD
app.config["SCOPE"] = ["User.Read"]  # permission scopes you want to request
app.config["SESSION_TYPE"] = "filesystem"  # for flask session persistence

import FlaskTemplate.views
