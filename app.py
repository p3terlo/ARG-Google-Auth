import os
import sys
import secrets
from datetime import date
from dotenv import load_dotenv, find_dotenv
from flask import Flask, flash, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound


app = Flask(__name__)
# Load env variables
load_dotenv(find_dotenv())

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

# Setup database
database_uri = 'mysql+pymysql://sql3346815:bxFXU9syFN@sql3.freemysqlhosting.net/sql3346815'
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Taken from example https://github.com/singingwolfboy/flask-dance-google-sqla
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    join_date = db.Column(db.DateTime)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

google_bp = make_google_blueprint(
    scope = ["profile","email"],
    redirect_to = 'login',
    storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)
)
app.register_blueprint(google_bp, url_prefix="/login")

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return "<a href='/google'> <h1> Log In </h1> </a>"

@app.route('/google')
def login():
    if not current_user.is_authenticated:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v1/userinfo")
    google_info = resp.json()
    # See https://blog.miguelgrinberg.com/post/the-new-way-to-generate-secure-tokens-in-python for generating secure tokens
    api_key = secrets.token_urlsafe()
    return "<h1> You are logged in as {}. Here's your API key: {} </h1>" .format(google_info["email"], api_key)

# Return False to let Flask-Dance know we're manually creating OAuth model in database (to store token), so it doesn't automatically do it
# Helpful read https://flask-dance.readthedocs.io/en/latest/multi-user.html
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        print("Token not good :(")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        print("Failed to fetch user info from Google")
        return False

    google_info = resp.json()
    google_id = google_info["id"]

    query = OAuth.query.filter_by(
        provider = blueprint.name,
        provider_user_id = google_id
    )
    # Find token in database. Else, create OAuth model with token and associate with local account
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider = blueprint.name,
            provider_user_id = google_id,
            token = token
        )

    if oauth.user:
        login_user(oauth.user)
        print("Successfully signed in with Google")
    else:
        print("Creating user in database")
        user = User(
            username = google_id,
            email = google_info["email"],
            join_date = date.today(),
        )

        oauth.user = user
        db.session.add_all([user,oauth])
        db.session.commit()

        login_user(user)
        print("Successfully signed in with Google")

    return False

@app.route('/logout')
@login_required
def logout():
    logout_user()
    print("You have successfully logged out! Redirecting you to homepage")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run 'python app.py --setup' to initialize database
    if '--setup' in sys.argv:
        with app.app_context():
                db.create_all()
                print("Database tables created")
    else:
        app.run(debug=True)