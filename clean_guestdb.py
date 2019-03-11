#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('/var/lib/backdoor/guests.db')
c = conn.cursor()
c.execute('DELETE FROM mit   WHERE expdate < date("now")')
c.execute('DELETE FROM other WHERE expdate < date("now")')
conn.commit()
conn.close()
