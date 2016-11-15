from flask import Flask, redirect, url_for, render_template, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauth import OAuthSignIn


app = Flask(__name__)
app.config.from_pyfile('config.ini', silent=True)

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    social_user = db.Column(db.Boolean, default=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    me = session['me'] or ''
    return render_template('index.html', me=me)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def register():
    existing = User.query.filter_by(username=request.form['username'], social_user=False).first()
    print('exist:', existing)
    if existing:
        print('exist:', existing)
        flash('Username already taken')
        return redirect(url_for('index'))
    not_social = 'not_social' + request.form['username']
    password = generate_password_hash(request.form['password'])
    user = User(
        social_id=not_social,
        username=request.form['username'],
        password=password,
        email=request.form['email'],
        social_user=False
    )
    db.session.add(user)
    db.session.commit()
    login_user(user, True)
    flash('User successfully registered')
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username, social_user=False).first()
    if registered_user is None:
        flash('Username is invalid')
        return redirect(url_for('index'))
    if not registered_user.check_password(password):
        flash('Password is invalid')
        return redirect(url_for('index'))
    login_user(registered_user, remember=remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:  # if logged in
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email, me = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:  # create new user with provider's data and a placeholder for password
        user = User(social_id=social_id, username=username, password='secret', email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    session['me'] = me
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
