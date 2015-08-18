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


	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()