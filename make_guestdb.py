#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('/var/lib/backdoor/guests.db')
c = conn.cursor()
c.execute('CREATE TABLE mit (email TEXT, expdate TEXT)')
c.execute('CREATE TABLE other (username TEXT, password TEXT, expdate TEXT)')
conn.commit()
conn.close()
