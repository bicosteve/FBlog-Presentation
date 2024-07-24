from datetime import datetime
from os import environ as env

from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    session,
    request,
)
from functools import wraps
from passlib.hash import sha256_crypt
import pymysql
from dotenv import load_dotenv


from helpers.service import Helpers


app = Flask(__name__, template_folder="../templates", static_folder="../static")
load_dotenv()  # loading the environment variables


app.config["MYSQL_HOST"] = env["MYSQL_HOST"]
app.config["MYSQL_USER"] = env["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = env["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = env["MYSQL_DB"]
app.config["MYSQL_CURSORCLASS"] = env["MYSQL_CURSORCLASS"]


mysql = pymysql.connect(
    host=app.config["MYSQL_HOST"],
    user=app.config["MYSQL_USER"],
    password=app.config["MYSQL_PASSWORD"],
    database=app.config["MYSQL_DB"],
)


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    cur = mysql.cursor()
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        isValid = Helpers.validate_register_form(
            name, email, username, password, confirm_password
        )

        if isValid == False:
            error = "Form is invalid"
            return render_template("register.html", error=error)

        hashed_password = sha256_crypt.encrypt(str(password))

        cur.execute(
            "INSERT INTO users(name,email,username,password, created_at, updated_at) VALUES(%s, %s, %s, %s,%s,%s)",
            (name, email, username, hashed_password, datetime.now(), datetime.now()),
        )

        mysql.commit()
        cur.close()

        flash("You are successfully registered. Login", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


# Articles
@app.route("/articles")
def articles():
    cur = mysql.cursor()
    result = cur.execute("SELECT * FROM articles LIMIT 100")
    articles = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template("articles.html", articles=articles)
    msg = "No articles found"
    return render_template("articles.html", msg=msg)


# single article
@app.route("/article/<string:id>/")
def article(id):
    q = """
            SELECT articles.title, articles.body, articles.created_at, users.name FROM articles INNER JOIN users ON users.userid = articles.author WHERE articles.id = %s LIMIT 1
        """
    cur = mysql.cursor()
    result = cur.execute(q, [id])
    article = cur.fetchone()
    if result > 0:
        return render_template("article.html", article=article)


@app.route("/login", methods=["GET", "POST"])
def login():
    cur = mysql.cursor()
    if request.method == "POST":
        email = request.form["email"]
        password_candidate = request.form["password"]
        isValid = Helpers.validate_login_form(email, password_candidate)
        if not isValid:
            error = "Email and password do not match"
            return render_template("login.html", error=error)
        result = cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1", [email])

        if result > 0:
            data = cur.fetchone()
            password = data[4]
            user_id = data[0]
            cur.close()
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('PASSWORD MATCHED')
                session["logged_in"] = True
                session["email"] = email
                session["userid"] = user_id
                flash("You are now logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid login"
                return render_template("login.html", error=error)
        else:
            error = "Email not found"
            return render_template("login.html", error=error)
    cur.close()
    return render_template("login.html")


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorised, please login", "danger")
            return redirect(url_for("login"))

    return wrap


# Logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for("login"))


# Dashboard
@app.route("/dashboard")
@is_logged_in
def dashboard():
    cur = mysql.cursor()

    q = """
            SELECT articles.id, articles.title, articles.body, articles.created_at,users.name FROM articles INNER JOIN users ON users.userid = articles.author LIMIT 100
        """
    result = cur.execute(q)
    articles = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template("dashboard.html", articles=articles)
    else:
        msg = "No articles found"
        return render_template("dashboard.html", msg=msg)


@app.route("/add_article", methods=["GET", "POST"])
@is_logged_in
def add_article():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]

        isValid = Helpers.validate_article_form(title=title, body=body)
        if not isValid:
            return render_template("add_article.html", error="All fields required")

        cur = mysql.cursor()
        cur.execute(
            "INSERT INTO  articles(title, body, author, created_at, updated_at) VALUES(%s, %s, %s,%s,%s)",
            (title, body, session["userid"], datetime.now(), datetime.now()),
        )

        mysql.commit()
        cur.close()
        flash("Article created", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_article.html")


# Edit Article
@app.route("/edit_article/<string:id>", methods=["GET", "POST"])
@is_logged_in
def edit_article(id):
    cur = mysql.cursor()
    if request.method == "GET":
        q = """
            SELECT id, title, body FROM  articles WHERE id = %s AND author = %s LIMIT 1
        """
        result = cur.execute(q, (id, session["userid"]))
        row = cur.fetchone()
        if result > 0:
            cur.close()
            return render_template("edit_article.html", row=row)
        return render_template("edit_article.html")

    article_id = int(request.form["article_id"])
    title = request.form["title"]
    body = request.form["body"]

    isValid = Helpers.validate_article_form(title=title, body=body)
    if not isValid:
        flash("Form is invalid", "danger")
        return render_template("edit_article.html", row=row)
    q = """
            UPDATE articles SET title = %s, body = %s, updated_at = %s WHERE id = %s AND author = %s
        """
    cur.execute(q, (title, body, datetime.now(), article_id, session["userid"]))
    mysql.commit()
    cur.close()
    flash("Article updated", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete_article/<string:id>", methods=["GET"])
@is_logged_in
def delete_article(id):
    cur = mysql.cursor()
    q = "DELETE FROM articles WHERE articles.id = %s AND articles.author = %s"
    result = cur.execute(q, (id, session["userid"]))
    mysql.commit()
    cur.close()

    if result > 0:
        flash("Article successfully deleted", "success")
        return redirect(url_for("dashboard"))

    flash("Article not deleted", "danger")
    return redirect(url_for("dashboard"))
