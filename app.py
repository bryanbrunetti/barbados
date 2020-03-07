import requests, os, config, sys
from flask import Flask, render_template, request, redirect, url_for, g, session
from flask_sqlalchemy import SQLAlchemy
from authentication import login_required
from flask.helpers import flash

app = Flask(__name__)
config.load(app)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    username = db.Column(db.String(39), unique=True, nullable=False)
    github_data = db.Column(db.JSON, unique=False, nullable=False)
    access_token = db.Column(db.String(63), unique=True, nullable=False)

    def __repr__(self):
        return '<User id:' + str(self.id) + ' name: ' + self.name + '>'


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(2048), unique=False, nullable=False)
    clicks = db.Column(db.Integer, unique=False, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref('users', lazy=True))

    def __repr__(self):
        return '<Url id:' + str(self.id) + ' url: ' + self.address + '>'


# db.create_all()
@app.route('/')
def index():
    return render_template('index.html', session=session)


@app.route('/callback')
def callback():
    try:
        response = requests.post('https://github.com/login/oauth/access_token',
                                 json={'client_id': os.getenv("CLIENT_ID"),
                                       'client_secret': os.getenv("CLIENT_SECRET"),
                                       'code': request.args.get('code')},
                                 headers={"Accept": "application/json"})

        access_token = response.json()['access_token']

        response = requests.get('https://api.github.com/user',
                                       params={"access_token": access_token})

        
        user = User(
            name=response.json()['name'],
            username = response.json['username'],
            access_token=access_token,
            github_data=response.json()
        )

        db.session.add(user)
        db.session.commit()
        session["user"] = user.id
        return redirect(url_for("urls"))
    except:
        e = sys.exc_info()[0]
        flash("There was an error logging in: %s", e)
        return redirect(url_for('.index'))


@app.route("/login")
def login():
    if session.get("user"):
        return redirect(url_for("urls"))
    else:
        return redirect(f"https://github.com/login/oauth/authorize?scope=&client_id={os.getenv('CLIENT_ID')}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("/"))

@app.route("/urls")
@login_required
def urls():
    render_template("urls.html")


@app.route('/<path:path>')
def catch_all(path):
    return path


if __name__ == '__main__':
    app.run(debug=True)
