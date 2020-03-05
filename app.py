import requests, os, config
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from authentication import login_required

app = Flask(__name__)
config.load(app)
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html', client_id=os.getenv('CLIENT_ID'))


@app.route('/callback')
def callback():
    github_response = requests.post('https://github.com/login/oauth/access_token',
                                    json={'client_id': os.getenv("CLIENT_ID"),
                                          'client_secret': os.getenv("CLIENT_SECRET"),
                                          'code': request.args.get('code')},
                                    headers={"Accept": "application/json"})

    github_response = requests.get('https://api.github.com/user',
                                   params={"access_token": github_response.json()['access_token']})
    github_response
    # github_response.json()["name"]
    return redirect(url_for("urls"))

@app.route("/login")
def login():
    return redirect("https://github.com/login/oauth/authorize?scope=&client_id={os.getenv('CLIENT_ID')}")

@app.route("/urls")
@login_required
def urls():
    return "Your URLs will be here"


if __name__ == '__main__':
    app.run(debug=True)
