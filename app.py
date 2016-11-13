from flask import Flask, redirect, url_for, render_template, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauth import OAuthSignIn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '572089576315607',
        'secret': '8ebad8172119c99e78780cbee4b36416'
    },
    'twitter': {
        'id': 'FvMJymvGvzzByEhxDXYMGvsff',
        'secret': 'c1iw9wpMrYuMpjjTJROYUxbAYlRpO4E36WlxHyVf6hqnyo9ZSH'
    },
    'github': {
        'id': 'cde938d195e8d4bcd203',
        'secret': '3516444e41ed967780033b91d9672bfb3fc1f466'
    },
    'google': {
        'id': '646103695922-b1djk9c1ksh7732au8dmleq7juiee7s7.apps.googleusercontent.com',
        'secret': 'Pf1wCMcPrs8Yq8Mi95rbbeRp'
    },
}

db = SQLAlchemy(app)
db.create_all()
lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(64), nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    not_social = 'not_social' + request.form['username']
    password = generate_password_hash(request.form['password'])
    user = User(
        social_id=not_social,
        username=request.form['username'],
        password=password,
        email=request.form['email']
    )
    db.session.add(user)
    db.session.commit()
    login_user(user, True)
    flash('User successfully registered')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username).first()
    if registered_user is None:
        flash('Username is invalid')
        return redirect(url_for('index'))
    if not registered_user.check_password(password):
        flash('Password is invalid')
        return redirect(url_for('index'))
    login_user(registered_user, remember=remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:  # if logged in
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:  # create new user with provider's data and a placeholder for password
        user = User(social_id=social_id, username=username, password='secret', email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
