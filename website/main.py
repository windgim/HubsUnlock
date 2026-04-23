from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import timedelta
from xray import Handler
from dotenv import load_dotenv
import sqlite3
import uuid
import json
import secrets
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

handler = Handler()
admin = os.environ.get('ADMIN_PASSWORD')

@app.route('/')
def index():
    if 'login' in session:
        return redirect('/profile')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def registration():
    if request.method == 'GET':
        return render_template('register.html')

    login = request.form['login']
    password = request.form['password']
    email = request.form['email']
    admin_password = request.form['admin-password']
    user_uuid = str(uuid.uuid4())

    if admin_password != admin:
        return render_template('register.html', error='Неправильный админ-пароль')
    
    db = sqlite3.connect('users.db')
    try:
        handler.add_user(login, user_uuid)

        db.execute(
            'INSERT INTO users (login, password, email, uuid) VALUES (?, ?, ?, ?)',
            (login, password, email, user_uuid)
        )
        db.commit()
    except Exception as e:
        if 'already exists' in str(e) or 'UNIQUE constraint failed' in str(e):
            return render_template('register.html', error='Пользователь уже существует')
        return render_template('register.html', error='Ошибка сервера')
    finally:
        db.close()
    
    session['login'] = login
    session.permanent = True
    return redirect('/profile')

@app.route('/login', methods=['GET', 'POST'])
def authorization():
    if request.method == 'GET':
        return render_template('login.html')

    login_input = request.form['login']
    password = request.form['password']
    
    db = sqlite3.connect('users.db')
    cursor = db.execute(
        'SELECT login FROM users WHERE (login = ? OR email = ?) AND password = ?',
        (login_input, login_input, password)
    )
    login = cursor.fetchone()
    db.close()
    
    if login:
        session['login'] = login[0]
        session.permanent = True
        return redirect('/profile')

    return render_template('login.html', error='Неверный логин или пароль')

@app.route('/profile')
def profile():
    if 'login' not in session:
        return redirect('/login')
    
    db = sqlite3.connect('users.db')

    cursor = db.execute(
        'SELECT login, email, uuid FROM users WHERE login = ?',
        (session['login'],)
    )
    user = cursor.fetchone()
    db.close()

    return render_template('profile.html', user=user)

@app.route('/profile/get-key/<uuid>')
def get_key(uuid):
    with open('config.json') as f:
        config_template = json.load(f)
    
    config = config_template.copy()
    config['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = uuid
    
    response = jsonify(config)
    response.headers['Cache-Control'] = 'private, max-age=3600'
    return response

@app.route('/profile/regenerate')
def regenerate():
    if 'login' not in session:
        return redirect('/login')

    new_user_uuid = str(uuid.uuid4())
    login = session['login']

    db = sqlite3.connect('users.db')
    try:
        handler.remove_user(login)
        handler.add_user(login, new_user_uuid)        

        db.execute(
            'UPDATE users SET uuid = ? WHERE login = ?',
            (new_user_uuid, login)
        )
        db.commit()
    # except Exception:
    #     return 'Ошибка сервера'
    finally:
        db.close()

    return redirect('/profile')

@app.route('/logout')
def logout():
    session.pop('login', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
