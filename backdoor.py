#!/usr/bin/env python3
# large portions taken from https://www.ajg.id.au/2018/01/01/mutual-tls-with-python-flask-and-werkzeug/

import flask
import sys
import werkzeug.serving
import ssl
import OpenSSL
import gpiozero

app_key = "/etc/openssl/backdoor.mit.edu.key"
app_crt = "/etc/openssl/backdoor.mit.edu.crt"
ca_crt = "/etc/openssl/ca.crt"
trusted_file = "/var/lib/tepz"
gpio_pin = 4
open_secs = 3

class EmailWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    """
    We subclass this class so that we can gain access to the connection
    property. self.connection is the underlying client socket. When a TLS
    connection is established, the underlying socket is an instance of
    SSLSocket, which in turn exposes the getpeercert() method.

    The output from that method is what we want to make available elsewhere
    in the application.
    """
    def make_environ(self):
        """
        The superclass method develops the environ hash that eventually
        forms part of the Flask request object.

        We allow the superclass method to run first, then we insert the
        peer certificate into the hash. That exposes it to us later in
        the request variable that Flask provides
        """
        environ = super(EmailWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(True)
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
        environ['email'] = x509.get_subject().emailAddress
        return environ

app = flask.Flask(__name__)

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=ca_crt)
ssl_context.load_cert_chain(certfile=app_crt, keyfile=app_key)
ssl_context.verify_mode = ssl.CERT_REQUIRED

door_unlatch = gpiozero.DigitalOutputDevice(gpio_pin)

@app.route('/', methods=['GET', 'POST'])
def backdoor():
    email = request.environ['email']
    # reopen the file every time to allow the list to be updated externally
    with open(trusted_file) as trusted:
        authed = (email + '\n') in trusted.readlines()
    if authed and request.method == 'POST':
        door_unlatch.blink(on_time=open_secs, n=1)
    return flask.render_template('index.html', authed=authed)

if __name__ == '__main__':
    host, port = sys.argv[1], int(sys.argv[2])
    app.run(host=host, port=port, ssl_context=ssl_context, request_handler=EmailWSGIRequestHandler)
