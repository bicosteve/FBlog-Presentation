from routes.route import app

if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(debug=True, host="localhost", port=7500)
