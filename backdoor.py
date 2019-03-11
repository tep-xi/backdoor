#!/usr/bin/env python3

import flask
import gpiozero
import OpenSSL
import re
import time

trusted_file = "/var/lib/tepz"
gpio_pin = 4
open_secs = 3

app = flask.Flask(__name__)

door_unlatch = gpiozero.DigitalOutputDevice(gpio_pin)

@app.route('/', methods=['GET', 'POST'])
def backdoor():
    certtext_raw = flask.request.headers['X-SSL-CLIENT-CERT']
    # don't really know why this is necessary
    certtext = re.sub('\t', '', certtext_raw)
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certtext)
    email = cert.get_subject().emailAddress

    # reopen the file every time to allow the list to be updated externally
    with open(trusted_file) as trusted:
        authed = (email + '\n') in trusted.readlines()
    if authed and flask.request.method == 'POST':
        door_unlatch.on()
        time.sleep(open_secs)
        door_unlatch.off()
    return flask.render_template('index.html', authed=authed)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
