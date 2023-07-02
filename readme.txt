# 仮想環境構築
$ python -m venv venv
$ source venv/bin/activate.fish

# パッケージインストール
$ pip install -r requirements.txt

# DB 作成
$ flask create_db

# admin 起動(DB管理)
$ python admin.py

# アプリ起動
$ flask --debug run

# 起動後、 http://127.0.0.1:5000 でアクセス可能
#  users:
#   - id: admin, password: admin
#   - id: user, password: user


# git 登録(https://github.com/oya3/python-flask-app.git のアドレスの場合)
$ git remote add origin git@github.com:oya3/python-flask-app.git
$ git remote -vv
origin  git@github.com:oya3/python-flask-app.git (fetch)
origin  git@github.com:oya3/python-flask-app.git (push)
