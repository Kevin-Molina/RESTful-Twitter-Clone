import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, jsonify, \
     current_app
from werkzeug import check_password_hash, generate_password_hash
from flask_basicauth import BasicAuth

class Subclass(BasicAuth):
    def check_credentials(self,username,password):
        result = query_db('''
        select pw_hash from user where username = ?
        limit 1''', [username])
        result = dict(result[0])
        return check_password_hash(result['pw_hash'], password)


# configuration
DATABASE = '/tmp/minitwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'

app = Flask('mt_api')
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)
basic_auth = Subclass(app)


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

@app.cli.command('populatedb')
def populatedb_command():
    """populates DB tables"""
    populate_db()
    print('Populated the database')

def populate_db():
    """Populates the database."""
    db = get_db()
    with app.open_resource('population.sql', mode='r') as p:
        db.cursor().executescript(p.read())
    db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db

def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select user_id from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None

@app.route('/tweets', methods=['GET'])
def public_timeline():
    """Displays the latest messages of all users."""
    response = query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id
        order by message.pub_date desc limit ?''', [PER_PAGE])
    response = [dict(x) for x in response]
    response = jsonify(response)
    response.status_code = 200
    return response

@app.route('/users', methods=['POST'])
def users():
    """Registers the user."""
    if not request.json['username']:
        error = 'You have to enter a username'
    elif not request.json['email'] or \
            '@' not in request.json['email']:
        error = 'You have to enter a valid email address'
    elif not request.json['password']:
        error = 'You have to enter a password'
    elif request.json['password'] != request.json['password2']:
        error = 'The two passwords do not match'
    elif get_user_id(request.json['username']) is not None:
        error = 'The username is already taken'
    else:
        db = get_db()
        db.execute('''insert into user (
          username, email, pw_hash) values (?, ?, ?)''',
          [request.json['username'], request.json['email'],
           generate_password_hash(request.json['password'])])
        db.commit()
        response = jsonify(url_for('users') + '/' + request.json['username'])
        response.status_code = 201
        return response
    response = jsonify(response)
    response.status_code = 400
    response.error = error
    return response


@app.route('/users/<username>/followers', methods=['POST', 'DELETE'])
@basic_auth.required
def followers(username):
    if request.method == "POST":
        """Adds the current user as follower of the given user."""
        who_id = get_user_id(request.authorization.username)
        whom_id = get_user_id(username)
        if who_id is None or whom_id is None:
            abort(400)
        db = get_db()
        # Uses username/id because form provided id, but rest api username
        db.execute('insert into follower (who_id, whom_id) values (?, ?)',
                  [who_id, whom_id])
        db.commit()
        response = jsonify(url_for('timeline', username=username))
        response.status_code = 201
        return response
    else:
        who_id = get_user_id(request.authorization.username)
        whom_id = get_user_id(username)
        if who_id is None or whom_id is None:
            abort(400)
        db = get_db()
        # Uses username/id because form provided id, but rest api username
        db.execute('delete from follower where who_id=? and whom_id=?',
                  [who_id, whom_id])
        db.commit()
        response = jsonify(url_for('timeline', username=username))
        response.status_code = 200
        return response


@app.route('/users/<username>/timeline', methods=['GET'])
@basic_auth.required
def timeline(username):
    """Shows a users timeline."""
    response = query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id and (
            user.user_id = ? or
            user.user_id in (select whom_id from follower
                                    where who_id = ?))
        order by message.pub_date desc limit ?''',
        [get_user_id(username), get_user_id(username), PER_PAGE])
    response = [dict(x) for x in response]
    response = jsonify(response)
    response.status_code = 200
    return response


@app.route('/tweets/<username>', methods=['GET'])
def user_tweets(username):
    """Display's a users tweets."""
    profile_user = query_db('select * from user where username = ?',
                            [username], one=True)
    if profile_user is None:
        abort(404)
    response =  query_db('''
            select message.*, user.* from message, user where
            user.user_id = message.author_id and user.user_id = ?
            order by message.pub_date desc limit ?''',
            [get_user_id(username), PER_PAGE])
    response = [dict(x) for x in response]
    response = jsonify(response)
    response.status_code = 200
    return response


@app.route('/tweets/<username>', methods=['POST'])
@basic_auth.required
def add_message(username):
    headerUsername = request.authorization.username
    if not headerUsername == username:
        print headerUsername
        print username
        abort(401)
    elif not get_user_id(headerUsername) == int(request.json['user_id']):
        abort(401)
    else:
        db = get_db()
        db.execute('''insert into message (author_id, text, pub_date)
          values (?, ?, ?)''', (request.json['user_id'], request.json['text'],
                                int(time.time())))
        db.commit()
        url = url_for('timeline', username=username)
        response = jsonify(url)
        response.status_code = 201
        return response
