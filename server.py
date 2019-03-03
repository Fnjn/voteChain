import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify

from blockchain import Blockchain
from block import Block
from transaction import Transaction

import crypto
import utils


# Instantiate the Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()

msg = b'hello, world'
key = crypto.loadKey('key.pem')
signature = crypto.signing(key, msg)
crypto.verification(key.public_key(), msg, signature)
addr = crypto.genAddr(key.public_key())

block = Block(addr)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'server.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route('/mine', methods=['GET'])
def mine():
    global block
    if block.transactions:
        print("Block: ", block.transactions)
        print("blockchain.last_block", blockchain.last_block)
        block.prev_block = blockchain.last_block
        print(str(block))
        blockchain.last_block = block
        print("blockchain.last_block", blockchain.last_block)

        block.build_merkle_tree()
        block.proofOfWork()
    block = Block(addr, key)

    return jsonify({"Status":"Success"}), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'voteGroup']
    if not all(k in values for k in required):
        return 'Missing values', 400

    t = Transaction(values['sender'])
    t.set_tip(0.5)
    t.add_receiver(values['sender'], values['voteGroup'])
    t.signing(key)

    block.add_transaction(t)
    print("Block: ", block.transactions)

    crypto.verification(key.public_key(), bytes(t), t.signature)

    response = {'message': 'Transaction will be added to Block'}
    return jsonify(response), 201

@app.route('/votesummary', methods=['GET'])
def vote_summary():
    #Counts all votes that have been added to the blockchain via successful transactions
    #Returns a JSON response with voting parties and their respective vote-counts so far
    block_iter = blockchain.last_block
    dict_votes = {}
    print("Block: ", block_iter.transactions)
    while block_iter != None:
        print("Block: ", block_iter.transactions)
        for tr in block_iter.transactions:
            print(tr.send_to)
            if tr.send_to[0][1] not in dict_votes:
                dict_votes[tr.send_to[0][1]] = 1
            else:
                dict_votes[tr.send_to[0][1]] += 1
        block_iter = block_iter.prev_block

    return jsonify(dict_votes), 200


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('flaskr/flaskr/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/lookup-cert')
def show_entries():
    db = get_db()
    cur = db.execute('select addr, cert from entries')
    entries = cur.fetchall()
    # return render_template('show_entries.html', entries=entries)
    return entries


@app.route('/add-cert', methods=['POST'])
def add_entry():
    # if not session.get('logged_in'):
    #     abort(401)
    db = get_db()
    db.execute('insert into entries (addr, cert) values (?, ?)',
                 [request.form['addr'], request.form['cert']])
    db.commit()
    flash('New entry was successfully posted')
    # return redirect(url_for('show_entries'))


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
