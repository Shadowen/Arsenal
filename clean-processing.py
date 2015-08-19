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
	c.execute('''DELETE FROM participantItem''')
	c.execute('''DROP TABLE championStat''')
	c.execute('''DROP TABLE itemStat''')
	c.execute('''DROP TABLE playerChampion''')
	c.execute('''DROP TABLE playerItem''')
	c.execute('''DROP TABLE playerStat''')
	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()
