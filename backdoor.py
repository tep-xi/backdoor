#!/usr/bin/env python3

import flask
import gpiozero
import OpenSSL
import re
import time
import sqlite3
import secrets
import string
from enum import Enum

trusted_file = '/var/lib/backdoor/tepz'
guests_file = '/var/lib/backdoor/guests.db'
gpio_pin = 4
open_secs = 3

app = flask.Flask(__name__)

class Auth(Enum):
    UNAUTHED = 0
    GUEST = 1
    TEP = 2

def cert_auth(tep_only=False):
    if 'X-SSL-CLIENT-CERT' in flask.request.headers:
        certtext_raw = flask.request.headers['X-SSL-CLIENT-CERT']
        certtext = re.sub('\t', '', certtext_raw) # don't really know why this is necessary
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certtext)
        email = cert.get_subject().emailAddress
        with open(trusted_file) as trusted:
            if (email + '\n') in trusted.readlines():
                return Auth.TEP
        if not tep_only:
            conn = sqlite3.connect(guests_file)
            c = conn.cursor()
            c.execute('SELECT * FROM mit WHERE email=? AND expdate >= date("now")', (email,))
            guest = c.fetchall() != []
            conn.close()
            if guest:
                return Auth.GUEST
    return Auth.UNAUTHED

@app.route('/', methods=['GET', 'POST'])
def backdoor():
    auth = cert_auth()
    if auth == Auth.UNAUTHED:
        creds = flask.request.authorization
        if not creds:
            return flask.Response('401 Unauthorized', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        conn = sqlite3.connect(guests_file)
        c = conn.cursor()
        c.execute('SELECT * FROM other WHERE username=? AND password=? AND expdate >= date("now")',
                (creds.username, creds.password))
        if c.fetchall():
            auth = Auth.GUEST
        conn.close()
    if auth == Auth.UNAUTHED:
        flask.abort(403)
    if flask.request.method == 'POST':
        door_unlatch = gpiozero.DigitalOutputDevice(gpio_pin)
        door_unlatch.on()
        time.sleep(open_secs)
        door_unlatch.off()
    return flask.render_template('index.html', is_tep=(auth == Auth.TEP))

@app.route('/addguest/mit', methods=['GET', 'POST'])
def addguest_mit():
    auth = cert_auth(tep_only=True)
    if auth != Auth.TEP:
        flask.abort(403)
    if flask.request.method == 'POST':
        form = flask.request.form
        kerb = form['kerberos']
        email = kerb + '@MIT.EDU'
        try:
            days = int(form['days'])
        except ValueError:
            return flask.render_template('addguest_mit.html', msg='Error: days must be an integer')
        days = max(days, 1)
        days = min(days, 7)
        conn = sqlite3.connect(guests_file)
        c = conn.cursor()
        c.execute('INSERT INTO mit VALUES (?, date("now", "-1 day", "+%i days"))' % days, (email,))
        conn.commit()
        conn.close()
        return flask.render_template('addguest_mit.html', msg=('Added %s for %i days' % (kerb, days)))
    return flask.render_template('addguest_mit.html')

@app.route('/addguest/other', methods=['GET', 'POST'])
def addguest_other():
    auth = cert_auth(tep_only=True)
    if auth != Auth.TEP:
        flask.abort(403)
    if flask.request.method == 'POST':
        form = flask.request.form
        username = form['username']
        try:
            days = int(form['days'])
        except ValueError:
            return flask.render_template('addguest_other.html', msg='Error: days must be an integer')
        days = max(days, 0)
        days = min(days, 7)
        alphabet = string.ascii_letters + string.digits + string.punctuation
        passlen = 16 + secrets.randbelow(9)
        password = ''.join(secrets.choice(alphabet) for i in range(passlen))
        conn = sqlite3.connect(guests_file)
        c = conn.cursor()
        c.execute('INSERT INTO other VALUES (?, ?, date("now", "-1 day", "+%i days"))' % days, (username, password))
        conn.commit()
        conn.close()
        return flask.render_template('addguest_mit.html',
            msg=('Added %s for %i days, with password %s' % (username, days, password)))
    return flask.render_template('addguest_other.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
