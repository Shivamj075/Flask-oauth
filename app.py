import os, json

from flask import Flask, session, redirect, render_template, request, jsonify, flash, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_dance.contrib.github import make_github_blueprint, github
# from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized
from werkzeug.security import check_password_hash, generate_password_hash

import requests

# from helpers import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))

github_blueprint = make_github_blueprint(client_id='272ae4c6200eb46e5df2', client_secret='31eb790efc21a79b3fc7c892c46feaa997762a22')


app.register_blueprint(github_blueprint, url_prefix='/github_login')
# db = SQLAlchemy(app)
# login_manager = LoginManager(app)

@app.route("/")
def index():
    """ Show search box """

    return render_template("index.html")

@app.route('/github')
def github_login():
    if not github.authorized:
        return redirect(url_for('github.login'))

    account_info = github.get('/user')

    if account_info.ok:
        account_info_json = account_info.json()

        return '<h1>Your Github name is {}'.format(account_info_json['login'])

    return '<h1>Request failed!</h1>'


@app.route("/login",methods=["GET","POST"])
def login():

  # Forget any user_id
  session.clear()

  username = request.form.get("username")

  # User reached route via POST(as by submitting a form via POST)
  if request.method=="POST":

      #Ensure username was submiitted
      if not request.form.get("username"):
          return render_template("error.html",message="must provide username")
        
      # Ensure password was submitted
      elif not request.form.get("password"):
          return render_template("error.html",message="must provide password")

      #Query database for username(https://zetcode.com/db/sqlalchemy/rawsql/)
      # https://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.ResultProxy
        
      rows = db.execute("SELECT * FROM users WHERE username=:username",{"username": username})

      result = rows.fetchone()

      # Ensure username exists and password is correct
      if(result==None or not check_password_hash(result[2],request.form.get("password"))):
          return render_template("error.html",message="invalid username and/or password")

      # Remember which user has logged in
      session["user_id"] = result[0]
      session["user_name"] = result[1]

      # Redirect user to home page
      flash('Logged In','username')
      return render_template("error.html",message="Successfully Logged In!!")

  # User reached route via GET (as by clicking a link or via redirec)
  else:
      return render_template("index.html")

@app.route("/logout")
def logout():
    """ Log user out """

    # Forget any user ID
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/Register", methods=["GET", "POST"])
def Register():
    """ register user """
    
    # Forget any user_id
    session.clear()
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="must provide username")

        # Query database for username
        userCheck = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":request.form.get("username")}).fetchone()

        # Check if username already exist
        if userCheck:
            return render_template("error.html", message="username already exist")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="must provide password")

        # Ensure confirmation wass submitted 
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="must confirm password")

        # Check passwords are equal
        elif not request.form.get("password") == request.form.get("confirmation"):
            return render_template("error.html", message="passwords didn't match")
        
        # Hash user's password to store in DB
        # hashedPassword = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        password = request.form.get("password")
        # Insert register into DB
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            {"username":request.form.get("username"), 
                             "password":generate_password_hash(password)})

        # Commit changes to database
        db.commit()

        flash('Account created', 'info')

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

