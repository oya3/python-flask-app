import os
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

basedir = os.path.abspath(os.path.dirname(__file__))

# Instantiate the Flask application with configurations
secureApp = Flask(__name__)  # , template_folder='templates'
CORS(secureApp)

# # Configure a specific Bootswatch theme (https://bootswatch.com/sandstone/)
secureApp.config['SECRET_KEY'] = 'secretkey'  # セッション情報の暗号化(https://qiita.com/Ryku/items/09f1b9e6a59f7cdceae8)
secureApp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')

# Instantiate the database
db = SQLAlchemy(secureApp)


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


# Create a datastore and instantiate Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(secureApp, user_datastore)

# Instantiate Flask-Admin
admin = Admin(secureApp, name='admin', url='/')


# Create a ModelView to add to our administrative interface
class UserModelView(ModelView):
    # column_list()でモデル内の全属性を表示するようにしている
    # デフォルトだとid,ForeignKey,relationship属性が表示されない
    column_list = ('id', 'email', 'username', 'password', 'last_login_at', 'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count', 'active', 'fs_uniquifier', 'confirmed_at', 'roles')


class RoleModelView(ModelView):
    column_list = ('id', 'name', 'description', 'permissions')


class RolesUsersModelView(ModelView):
    column_list = ('id', 'user_id', 'role_id')


class BookModelView(ModelView):
    column_list = ('id', 'title', 'release_date')


# Add administrative views to Flask-Admin
admin.add_view(UserModelView(User, db.session))
admin.add_view(RoleModelView(Role, db.session))
admin.add_view(RolesUsersModelView(RolesUsers, db.session))
admin.add_view(BookModelView(Book, db.session))


if __name__ == "__main__":
    secureApp.run(debug=True)
