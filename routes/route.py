from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from functools import wraps
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt


from forms.register import RegisterForm
from forms.login import LoginForm 


app = Flask(__name__)

#config MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'bico'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'crud_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#cursor is a handler which connects to db
#the class can be all types of data types



mysql = MySQL(app)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor() 

        #Execute query
        cur.execute('INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)',(name, email, username,password))

        #Commit to DB

        mysql.connection.commit()


        #close the connection

        cur.close()

        flash('You are now registered and can log in','success')

        return redirect(url_for('login'))
    return render_template('register.html',form=form)

# Articles
@app.route('/articles')
def articles():
    #making articles appear on the dashboard

    # Create cursor
    cur = mysql.connection.cursor()

    #Getting  articles

    result = cur.execute('SELECT * FROM articles')

    articles = cur.fetchall()


    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)

    #close the connection
    cur.close()
    return render_template('articles.html', articles=Articles)



#single article
@app.route('/article/<string:id>/')
def article(id):
    #Create cursor
    cur = mysql.connection.cursor()


    # Getting article

    result = cur.execute('SELECT * FROM articles WHERE id = %s', [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

#user registration


#user login



@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        #get form fields
        email = request.form['email']
        password_candidate = request.form['password']  #compares with the password in db

        #create cursor

        cur = mysql.connection.cursor()

        #get user by email

        result = cur.execute('SELECT * FROM users WHERE email = %s',[email])

        if result > 0:
            #get stored hash
            data = cur.fetchone()
            password = data['password']


            #compare the passwords
            if sha256_crypt.verify(password_candidate,password):
                #app.logger.info('PASSWORD MATCHED')
                #passed
                session['logged_in'] = True
                session['email'] = email

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            #closing connection
            cur.close()

        else:
            error = 'Email not found'
            return render_template('login.html', error=error)
        
        

    return render_template('login.html',form=form)


#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login','danger')
            return redirect(url_for('login'))
    return wrap


#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #making articles appear on the dashboard

    # Create cursor
    cur = mysql.connection.cursor()

    #Getting  articles

    result = cur.execute('SELECT * FROM articles')

    articles = cur.fetchall()


    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)

    #close the connection
    cur.close()


    return render_template('dashboard.html')


@app.route('/add_article', methods=['GET','POST'])
#@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body= form.body.data

        #Create Cursor
        cur =mysql.connection.cursor()

        # Execute
        cur.execute('INSERT INTO  articles(title, body, author) VALUES(%s, %s, %s)', (title, body,session['email'])) #error

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)


#Edit Article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
   # Create cursor
   cur = mysql.connection.cursor()


   # Get article by id
   result = cur.execute('SELECT * FROM articles WHERE id = %s', [id])


   article = cur.fetchone()

    #Get form
   form = ArticleForm(request.form)

    #populate article form fields
   form.title.data = article['title']
   form.body.data = article['body']

   if request.method == 'POST' and form.validate():
       title = form.title.data
       body= form.body.data

        #Create Cursor
       cur =mysql.connection.cursor()

        #Execute
       cur.execute ('UPDATE articles SET name=%s, body=%s WHERE id = %s', (name, body, id))

        #Commit to DB
       mysql.connection.commit()

        #Close connection
       cur.close()

       flash('Article created', 'success')

       return redirect(url_for('dashboard'))
   return render_template('add_article.html',form=form)