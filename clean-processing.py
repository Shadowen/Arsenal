import urllib3
import certifi

import json

import sqlite3

import traceback
import math
from collections import defaultdict
# Init

conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
	c.execute('''DROP VIEW matchParticipant''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP VIEW eventItem''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP VIEW participantItemStatic''')
except:
	traceback.print_exc()
try:
	c.execute('''DELETE FROM participantItem''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP TABLE championStat''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP TABLE itemStat''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP TABLE playerChampion''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP TABLE playerItem''')
except:
	traceback.print_exc()
try:
	c.execute('''DROP TABLE playerStat''')
except:
	traceback.print_exc()
try:
	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()
