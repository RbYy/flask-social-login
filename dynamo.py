from flywheel import Model, Field, Engine
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

engine = Engine()
engine.connect_to_region('eu-west-1')


class GUIDUserMixin(UserMixin):
    def get_id(self):
        self.id = self.GUID
        return super(GUIDUserMixin, self).get_id()


class RobertBrumatTest(GUIDUserMixin, Model):
    __dynamoDB = boto3.resource('dynamodb')
    __T = __dynamoDB.Table('RobertBrumatTest')
    GUID = Field(hash_key=True)
    password = Field()

    def saveLogin(self, social_data, provider):
        ts = datetime.now()

        storeArray = social_data
        if provider == 'google':
            storeArray['GUID'] = 'smn::%s::%s' % (provider, social_data['sub'])
        else:
            storeArray['GUID'] = 'smn::%s::%s' % (provider, social_data['id'])

        for key, value in storeArray.items():
            if value == '':
                storeArray[key] = None

        RobertBrumatTest.__T.put_item(Item=storeArray)
        self.post_save_()
        self.executionTime = datetime.now() - ts

    def check_password(self, password):
        return check_password_hash(self.password, password)


engine.register(RobertBrumatTest)


@lm.user_loader
def load_user(id):
    return engine.query(RobertBrumatTest).filter(GUID=id).first(desc=True)


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
    exists = engine.query(RobertBrumatTest).filter(GUID=generate_GUID()).first(desc=True)

    if exists:
        flash('Username already taken')
        return redirect(url_for('index'))

    password = generate_password_hash(request.form['password'])
    u = RobertBrumatTest(GUID=generate_GUID())
    u.email = request.form['email']
    u.password = password
    engine.save(u)
    login_user(u, True)
    session['me'] = {'GUID:': u.GUID}
    flash('User successfully registered')
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    exists = engine.query(RobertBrumatTest).filter(GUID=generate_GUID()).first(desc=True)
    if not exists:
        flash('Username is invalid')
        return redirect(url_for('index'))

    if not check_password_hash(exists.password, password):
        flash('Password is invalid')
        return redirect(url_for('index'))
    session['me'] = {'username:': exists.GUID}
    login_user(exists, remember=remember_me)
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
    user = engine.query(RobertBrumatTest).filter(GUID=social_id).first(desc=True)

    if not user:  # create new user with provider's data and a placeholder for password
        print('creating user ...')
        user = RobertBrumatTest(social_id)
        user.saveLogin(social_data, provider)
    login_user(user, True)
    session['me'] = social_data
    return redirect(url_for('index'))


app.run(debug=True)

# Register our model with the engine so it can create the Dynamo table

# engine.create_schema()
# social = RobertBrumatTest('smn::facebook::123456789')
# engine.save(social)


# print(item.GUID)
# item.refresh()
