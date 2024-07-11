# from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from flask_mysqldb import MySQL
# from passlib.hash import sha256_crypt
# from functools import wraps

from routes.route import app 


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)