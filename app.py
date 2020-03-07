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
    github_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
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
    if session.get("user"):
        return redirect(url_for("urls"))
    try:
        response = requests.post('https://github.com/login/oauth/access_token',
                                 json={'client_id': os.getenv("CLIENT_ID"),
                                       'client_secret': os.getenv("CLIENT_SECRET"),
                                       'code': request.args.get('code')},
                                 headers={"Accept": "application/json"})

        access_token = response.json()['access_token']

        github_data = requests.get('https://api.github.com/user', params={"access_token": access_token}).json()

        user = db.session.query(User).filter(User.github_id == github_data['id']).first()
        if user:
            session["user"] = user.id
            return redirect(url_for("urls"))

        user = User(github_id=github_data['id'])
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
    return redirect(url_for("index"))


@app.route("/urls")
@login_required
def urls():
    return render_template("urls.html")


@app.route('/<path:path>')
def catch_all(path):
    return path


if __name__ == '__main__':
    app.run(debug=True)
