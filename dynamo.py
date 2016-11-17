from flask import Flask, redirect, url_for, render_template, flash, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauth import OAuthSignIn
import boto3
from datetime import datetime


app = Flask(__name__)
app.config.from_pyfile('config.ini', silent=True)


lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin):
    __dynamoDB = boto3.resource('dynamodb')
    __T = __dynamoDB.Table('RobertBrumatTest')

    def __init__(self):
        self.item = {}

    def get_id(self):
        self.id = self.item['GUID']
        return super(User, self).get_id()

    def getUser(self, GUID, provider='user'):
        ts = datetime.now()
        # res = self.__T.get_item(Key={'guid': 'smn::%s::%s' % (provider, id)})
        res = self.__T.get_item(Key={'GUID': GUID})
        if 'Item' in res:
            self.item = res['Item']
            return self
        self.executionTime = datetime.now() - ts
        return None

    def save(self, social_data, provider):
        ts = datetime.now()

        storeArray = social_data
        if provider == 'user':
            storeArray['GUID'] = 'smn::%s::%s' % (provider, social_data['username'])
        elif provider == 'google':
            storeArray['GUID'] = 'smn::%s::%s' % (provider, social_data['sub'])
        else:
            storeArray['GUID'] = 'smn::%s::%s' % (provider, social_data['id'])

        for key, value in storeArray.items():
            if value == '':
                storeArray[key] = None

        self.__class__.__T.put_item(Item=storeArray)
        self.item = storeArray
        self.executionTime = datetime.now() - ts

    def check_password(self, password):
        return check_password_hash(self.password, password)


@lm.user_loader
def load_user(id):
    return User().getUser(id)


@app.route('/')
def index():
    me = session['me'] or {}
    return render_template('index.html', me=me)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


def generate_GUID():
    return 'smn::user::' + request.form['username']


@app.route('/register', methods=['POST'])
def register():
    user = User()
    if user.getUser(generate_GUID()):
        flash('Username already taken')
        return redirect(url_for('index'))

    registration_data = {key: value for key, value in request.form.iteritems() if key != 'password'}
    registration_data['password'] = generate_password_hash(request.form['password'])
    user.save(registration_data, 'user')
    session['me'] = registration_data
    login_user(user, True)
    flash('User successfully registered')
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    user = User().getUser(generate_GUID())
    if not user:
        flash('Username is invalid')
        return redirect(url_for('index'))

    if not check_password_hash(user.item['password'], password):
        flash('Password is invalid')
        return redirect(url_for('index'))
    print('email: ', user.item['email'])
    session['me'] = {'username:': user.item['GUID']}
    login_user(user, remember=remember_me)
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
    social_id, username, email, social_data = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))

    social_id = 'smn::' + provider + '::' + str(social_id)
    print('ffffff', social_id, provider)
    # user_data, GUID = db.getUser(social_id, provider)
    # print('blabla', GUID)
    # user = engine.query(RobertBrumatTest).filter(GUID=social_id).first(desc=True)User
    user = User().getUser(social_id)
    if not user:  # create new user with provider's data and a placeholder for password
        print('creating user ...')
        user = User().saveLogin(social_data, provider)
    login_user(user, True)
    session['me'] = social_data
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
