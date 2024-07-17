from datetime import datetime

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


from helpers.service import validate_register_form
from helpers.service import validate_login_form
from helpers.service import validate_article_form
from forms.article import ArticleForm


app = Flask(__name__, template_folder="../templates", static_folder="../static")


app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "bico"
app.config["MYSQL_PASSWORD"] = "Betika@254"
app.config["MYSQL_DB"] = "blogs_db"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = pymysql.connect(
    host=app.config["MYSQL_HOST"],
    user=app.config["MYSQL_USER"],
    password=app.config["MYSQL_PASSWORD"],
    database=app.config["MYSQL_DB"],
)


@app.route("/home")
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

        isValid = validate_register_form(
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
    cur = mysql.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s LIMIT 1", [id])
    article = cur.fetchone()
    if result > 0:
        return render_template("article.html", article=article)


@app.route("/login", methods=["GET", "POST"])
def login():
    cur = mysql.cursor()
    if request.method == "POST":
        email = request.form["email"]
        password_candidate = request.form["password"]
        isValid = validate_login_form(email, password_candidate)
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

        isValid = validate_article_form(title=title, body=body)
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
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    form = ArticleForm(request.form)

    # populate article form fields
    form.title.data = article["title"]
    form.body.data = article["body"]

    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.cursor()

        cur.execute(
            "UPDATE articles SET title=%s, body=%s WHERE id = %s AND author = %s",
            (title, body, id, session["userid"]),
        )

        # Commit to DB
        mysql.commit()
        cur.close()

        flash("Article created", "success")

        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)
