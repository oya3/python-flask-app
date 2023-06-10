# 仮想環境構築
$ python -m venv venv
$ source venv/bin/activate.fish

# パッケージインストール
$ pip install -r requirements.txt

# DB 作成
$ flask create_db

# アプリ起動
$ flask --debug run

# admin 起動(DB管理)
$ python admin.py


# git 登録(https://github.com/oya3/python-flask-app.git のアドレスの場合)
$ git remote add origin git@github.com:oya3/python-flask-app.git
$ git remote -vv
origin  git@github.com:oya3/python-flask-app.git (fetch)
origin  git@github.com:oya3/python-flask-app.git (push)
