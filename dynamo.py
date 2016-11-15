from flywheel import Model, Field, Engine
from flask import Flask, redirect, url_for, render_template, flash, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauth import OAuthSignIn


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
    GUID = Field(hash_key=True)

    def __init__(self, GUID):
        self.GUID = GUID


engine.register(RobertBrumatTest)


@lm.user_loader
def load_user(id):
    return engine.query(RobertBrumatTest).filter(GUID=id).first(desc=True)


@app.route('/')
def index():
    me = session['me'] or ''
    return render_template('index.html', me=me)


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


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:  # if logged in
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email, me = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))

    social_id = 'smn::' + provider + '::' + social_id.strip('$')
    user = engine.query(RobertBrumatTest).filter(GUID=social_id).first(desc=True)

    if not user:  # create new user with provider's data and a placeholder for password
        print('creating user ...')
        user = RobertBrumatTest(social_id)
        engine.save(user)
    login_user(user, True)
    session['me'] = me
    return redirect(url_for('index'))


app.run(debug=True)

# Register our model with the engine so it can create the Dynamo table

# engine.create_schema()
# social = RobertBrumatTest('smn::facebook::123456789')
# engine.save(social)


# print(item.GUID)
# item.refresh()
