from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create-home")
def create_home():
    return render_template("create_home.html")


@app.route("/keys")
def keys():
    return render_template("keys.html")


@app.route("/energy")
def energy():
    return render_template("energy.html")


@app.route("/status")
def status():
    return render_template("status.html")


@app.route("/users")
def users():
    return render_template("users.html")


@app.route("/mobile")
def mobile():
    return render_template("mobile.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
