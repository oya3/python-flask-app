import os
import datetime
from flask import Flask, session, render_template, url_for
from flask import jsonify
from flask import redirect, make_response, abort, request
from flask_wtf import FlaskForm
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, roles_required, roles_accepted
from flask_security.forms import RegisterForm  # ,LoginForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from wtforms import SelectMultipleField  # ,StringField
from wtforms import HiddenField, StringField, DateField
from wtforms import validators
from datetime import timedelta
from flask_cors import CORS
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

# Instantiate the Flask application with configurations
secureApp = Flask(__name__)  # , template_folder='templates' はデフォルト
CORS(secureApp)

secureApp.config['SECRET_KEY'] = 'secretkey'  # セッション情報の暗号化(https://qiita.com/Ryku/items/09f1b9e6a59f7cdceae8)

# secureApp.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = 'username'  # ログイン時のキー指定(デフォルトがemail)
secureApp.config['SECURITY_USERNAME_ENABLE'] = True

secureApp.config['SECURITY_PASSWORD_SALT'] = 'none'  # パスワードのソルト(hash(平文+ソルト))
secureApp.config['SECURITY_POST_LOGIN_VIEW'] = '/'  # ユーザログイン後のリダイレクト先
secureApp.config['SECURITY_POST_LOGOUT_VIEW'] = '/'  # ユーザログアウト後のリダイレクト先
secureApp.config['SECURITY_POST_REGISTER_VIEW'] = '/'  # ユーザ登録後
secureApp.config['SECURITY_REGISTERABLE'] = True

# Configure application to not send an email upon registration
secureApp.config['SECURITY_SEND_REGISTER_EMAIL'] = False  # 登録時にメール送信しない
secureApp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # モデル(sqlalchemy db)上のすべてのinsert、update、およびdelete操作が通知されない
# secureApp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'  # db は sqlite
secureApp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')

# Instantiate the database
db = SQLAlchemy(secureApp)
migrate = Migrate(secureApp, db)

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('users.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(db.UnicodeText)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
                            backref=db.backref('users', lazy='dynamic'))


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.Date())


class BookForm(FlaskForm):
    id = HiddenField('ID')
    title = StringField('Ttitle:',
                        validators=[
                            validators.DataRequired(message='必須です'),
                            validators.Length(max=20, message='20文字以内で入力')
                        ])
    release_date = DateField('Date:',
                             format='%Y-%m-%d',
                             default=datetime.datetime.now(),
                             # render_kw={'class': 'date_pick'},  # datepicker の拡張用（現在未使用）
                             validators=[
                                 validators.DataRequired(message='必須です'),
                             ])


class ExtendedRegisterForm(RegisterForm):
    roles = SelectMultipleField('Roles', validate_choice=False)

    def __init__(self, *args, **kwargs):
        # ここでないとdbオブジェクトが有効でない
        # RuntimeError: Working outside of application contextといわれる
        super().__init__(*args, **kwargs)
        self.roles.choices = [(role.name, role.name) for role in db.session.query(Role).all()]


# Create a datastore and instantiate Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(secureApp, user_datastore, register_form=ExtendedRegisterForm)  # , login_form=ExtendedLoginForm, register_form=ExtendedRegisterForm

# Add the context processor
@security.context_processor
def security_context_processor():
    return dict(
        # admin_base_template=admin.base_template,
        # admin_view=admin.index_view,
        get_url=url_for,
        # h=admin_helpers,
        app_config=secureApp.config,
    )


# Define the index route
@secureApp.route('/', methods=['GET'])
# @login_required
def index():
    return render_template('index.html', app_config=secureApp.config)


@secureApp.route('/help', methods=['GET'])
# @login_required
def help():
    return render_template('help.html', app_config=secureApp.config)


@secureApp.route('/test_admin', methods=['GET'])
@roles_required('admin')  # AND: admin 権限を保持している
def test_admin():
    return render_template('admin_only_page.html', app_config=secureApp.config)


@secureApp.route("/books", methods=['GET'])
def book_index():
    # 一覧
    books = db.session.query(Book).all()
    return render_template('book/index.html', app_config=secureApp.config, books=books)


@secureApp.route("/books/new", methods=['GET', 'POST'])
def book_new():
    # 登録
    form = BookForm()
    if form.validate_on_submit():  # POST 時にバリデーションチェック。POST でない場合、False
        book = Book()
        book.title = form.title.data
        book.release_date = form.release_date.data
        db.session.add(book)
        db.session.commit()
        return redirect("/books/{}".format(book.id))
    return render_template('book/new.html', app_config=secureApp.config, form=form)


@secureApp.route("/books/<int:book_id>", methods=['GET'])
def book_show(book_id):
    book = db.session.query(Book).filter(Book.id == book_id).one_or_none()
    if book:
        return render_template('book/show.html', app_config=secureApp.config, book=book)
    abort(404)


@secureApp.route("/books/<int:book_id>/edit", methods=['GET', 'POST'])
def book_edit(book_id):
    # 更新
    book = db.session.query(Book).filter(Book.id == book_id).one_or_none()
    form = BookForm()
    if form.validate_on_submit():  # POST 時にバリデーションチェック。POST でない場合、False
        book.title = form.title.data
        book.release_date = form.release_date.data
        db.session.commit()
        return redirect("/books/{}".format(book.id))
    elif request.method == 'GET':
        if book is None:
            abort(404)
        form.id.data = book.id
        form.title.data = book.title
        form.release_date.data = book.release_date
    return render_template('book/edit.html', app_config=secureApp.config, form=form)


@secureApp.route("/books/<int:book_id>/delete", methods=['GET'])
def book_delete(book_id):
    try:
        db.session.query(Book).filter(Book.id == book_id).delete()
        db.session.commit()
    except Exception:
        return make_response(code=404)
    return redirect("/books")


@secureApp.route('/test_user', methods=['GET'])
@roles_accepted('admin', 'user')  # OR: admin,userのどちらかの権限を保持している
def test_user():
    return render_template('admin_user_page.html', app_config=secureApp.config)


def model_to_dict(instance):
    mapper = inspect(instance.__class__)
    columns = [c.key for c in mapper.column_attrs]
    relationships = mapper.relationships
    result = {c: getattr(instance, c) for c in columns}
    for rel in relationships:
        if (rel.backref is None):
            continue
        rel_name = rel.key
        rel_value = getattr(instance, rel_name)
        if (rel_value is not None):
            if rel.uselist:
                rel_value = [model_to_dict(item) for item in rel_value]
            else:
                rel_value = model_to_dict(rel_value)
        result[rel_name] = rel_value
    return result

@secureApp.route('/api/<path:name>', methods=['GET'])
def api_get_resources(name):
    # inspector = inspect(db.engine)
    # print(inspector.get_table_names())
    allow_resources = {
        'users': User,
        'roles': Role,
        'roles_users': RolesUsers,
        'books': Book,
    }
    if name not in allow_resources.keys():
        abort(405)
    model = allow_resources[name]
    resources = db.session.query(model).all()
    result = []
    for resource in resources:
        result.append(model_to_dict(resource))
    return make_response(jsonify(result))


@secureApp.before_request
def make_session_permanent():
    # リクエストのたびにセッションの寿命を更新
    session.permanent = True
    secureApp.permanent_session_lifetime = timedelta(minutes=5)

@secureApp.cli.command("seed")  # 追加（cread_dbもあるが、これはテーブル生成も含まれてしまうため、マイグレーション機能を追加した場合は、seed コマンドでDB初期データ設定するようにする）
def seed():
    try:
        user_datastore.create_role(name='admin', description='管理者')
        user_datastore.create_role(name='user', description='一般ユーザ')
        user_datastore.create_user(username='admin', email='admin@test.com', password='admin', roles=['admin'])
        user_datastore.create_user(username='user', email='user@test.com', password='user', roles=['user'])
        user_datastore.create_user(username='user2', email='user2@test.com', password='user2', roles=['admin', 'user'])
        db.session.commit()
    except Exception as e:
        print(e)

# Create the tables for the users and roles and add a user to the user table
@secureApp.cli.command("create_db")
def create_db():
    try:
        db.drop_all()
        db.create_all()
        seed()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    secureApp.run(debug=True)
