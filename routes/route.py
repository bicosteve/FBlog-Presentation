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

from forms.register import RegisterForm
from forms.login import LoginForm
from forms.article import ArticleForm


app = Flask(__name__)


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
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.cursor()
        cur.execute(
            "INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)",
            (name, email, username, password),
        )

        mysql.commit()
        cur.close()

        flash("You are now registered and can log in", "success")

        return redirect(url_for("login"))
    return render_template("register.html", form=form)


# Articles
@app.route("/articles")
def articles():
    cur = mysql.cursor()
    result = cur.execute("SELECT * FROM articles")
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
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    if result > 0:
        return render_template("article.html", article=article)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        email = request.form["email"]
        password_candidate = request.form["password"]

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1", [email])

        if result > 0:
            data = cur.fetchone()
            password = data["password"]
            cur.close()
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('PASSWORD MATCHED')
                session["logged_in"] = True
                session["email"] = email
                flash("You are now logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid login"
                return render_template("login.html", error=error)
        else:
            error = "Email not found"
            return render_template("login.html", error=error)
    cur.close()
    return render_template("login.html", form=form)


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
    result = cur.execute("SELECT * FROM articles")
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
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.cursor()

        cur.execute(
            "INSERT INTO  articles(title, body, author) VALUES(%s, %s, %s)",
            (title, body, session["email"]),
        )

        mysql.commit()
        cur.close()
        flash("Article created", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)


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
            "UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id)
        )

        # Commit to DB
        mysql.commit()
        cur.close()

        flash("Article created", "success")

        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)
