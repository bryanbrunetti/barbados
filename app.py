import requests, os, config, sys, validators
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from authentication import login_required
from flask.helpers import flash
from base_converter import BaseConverter
from passlib.hash import sha256_crypt


app = Flask(__name__)
config.load(app)
db = SQLAlchemy(app)

@app.context_processor
def inject_github_auth():
    github_auth_enabled = True if "CLIENT_ID" in os.environ and os.environ["CLIENT_ID"] != "" else False
    return dict(github_auth_enabled=github_auth_enabled)
        
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(39), unique=True,nullable=False,index=True)
    password = db.Column(db.String, unique=False,nullable=True)
    github_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    access_token = db.Column(db.String(63), unique=True, nullable=True)

    def __repr__(self):
        return '<User id:' + str(self.id) + ' name: ' + self.username + '>'


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
        flash("There was an error logging in: %e", e)
        return redirect(url_for('.index'))


@app.route("/login")
def login():
    if session.get("user"):
        return redirect(url_for("urls"))
    else:
        return redirect(f"https://github.com/login/oauth/authorize?scope=&client_id={os.getenv('CLIENT_ID')}")

@app.route("/users/register", methods=["GET", "POST"])
def users_register():
    if request.method == "GET":
        return render_template("users_register.html")
    else:
        errors = False
        if len(request.form['username']) == 0:
            flash("username must not be empty", category="danger")
            errors = True
        if len(request.form['password']) < 8:
            flash("passwords must be 8 characters or more", category="danger")
            errors = True
        if errors:
            return render_template("users_register.html")
        user = db.session.query(User).filter(User.username == request.form['username']).first()
        if user:
            flash("That username is already taken", category="danger")
            return render_template("users_register.html")
        else:
            password = sha256_crypt.hash(request.form['password'])
            user = User(username=request.form['username'],password=password)
            db.session.add(user)
            db.session.commit()
            session["user"] = user.id
            return redirect(url_for("urls"))


@app.route("/users/login", methods=["GET", "POST"])
def users_login():
    if request.method == "GET":
        return render_template("users_login.html")
    else:
        print(request.form['username'])
        print(request.form['password'])
        password = sha256_crypt.hash(request.form['password'])
        print(password)
        user = db.session.query(User).filter(User.username == request.form["username"]).first()
        print("Verifying: %s", user)
        if user and sha256_crypt.verify(request.form['password'], user.password):
            session["user"] = user.id
            return redirect(url_for("urls"))
        else:
            flash("The username or password you entered is incorrect", category="danger")
            return render_template("users_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/urls", methods=["GET", "POST"])
@login_required
def urls():
    if request.method == "POST":
        valid_url = validators.url(request.form['address'])
        if valid_url == True:
            new_url = Url(address=request.form['address'], user_id=session.get("user"))
            db.session.add(new_url)
            db.session.commit()
            flash("New Url added", category="success")
        else:
            flash("That URL is not valid", category="danger")
        return redirect("/urls")
    else:
        urls = []
        for url in Url.query.filter_by(user_id=session.get("user")).all():
            url.shortcode = request.url_root + BaseConverter().int_to_string(url.id)
            urls.append(url)
        return render_template("urls.html", urls=urls)

@app.route("/urls/edit", methods=["POST"])
@login_required
def edit_url():
    id = request.form['url-id']
    valid_url = validators.url(request.form['address'])
    if not valid_url:
        flash("URL is invalid", category="danger")
        return redirect(url_for("urls"))
    
    url = Url.query.filter_by(user_id=session["user"],id=id).first()
    if url:
        url.address = request.form['address']
        db.session.commit()
        return redirect(url_for("urls"))
    else:
        flash("That URL was not found", category="danger")
    
    return redirect(url_for("urls"))

@app.route("/urls/delete", methods=["POST"])
@login_required
def delete_url():
    id = request.form['url-id']
    url = Url.query.filter_by(user_id=session["user"],id=id).first()
    if url:
        db.session.delete(url)
        db.session.commit()
    return redirect(url_for("urls"))


@app.route('/<path:path>')
def catch_all(path):
    url_id = BaseConverter().string_to_int(path)
    url = Url.query.get(url_id) if url_id > 0 else None

    if url:
        url.clicks = Url.clicks + 1
        db.session.commit()
        return redirect(url.address, code=302)
    else:
        return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
