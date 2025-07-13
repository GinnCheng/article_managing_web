"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import session, request, redirect, url_for, render_template, flash
import msal
import uuid
from FlaskTemplate import app, logger

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app.config["CLIENT_ID"],
        authority=authority or app.config["AUTHORITY"],
        client_credential=app.config["CLIENT_SECRET"],
        token_cache=cache,
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("authorized", _external=True)
    )

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=app.config["SCOPE"], state=session["state"])
    return redirect(auth_url)


@app.route('/')
@app.route('/home')
def home():
    user = session.get("user")
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
        user=user
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )


@app.route(app.config["REDIRECT_PATH"])
def authorized():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("home"))  # state mismatch, potential CSRF

    if "error" in request.args:  # login failure
        error = request.args.get("error")
        error_description = request.args.get("error_description")
        logger.warning(f"Login failed: {error} - {error_description}")
        flash("Login failed. Please try again.", "danger")
        return redirect(url_for("home"))

    if "code" in request.args:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args["code"],
            scopes=app.config["SCOPE"],
            redirect_uri=url_for("authorized", _external=True),
        )
        if "access_token" in result:
            session["user"] = result.get("id_token_claims")
            _save_cache(cache)
            logger.info(f"User {session['user'].get('preferred_username')} logged in successfully")
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            logger.warning(f"Failed to acquire token: {result.get('error_description')}")
            flash("Login failed during token acquisition.", "danger")
            return redirect(url_for("home"))
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://login.microsoftonline.com/common/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("home", _external=True)
    )