import urllib3
import certifi

import json

import sqlite3

import traceback
import math
from collections import defaultdict
# Init
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',  # Force certificate check.
    ca_certs=certifi.where(),  # Path to the Certifi bundle.
)
conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
	class MySum:
	    def __init__(self):
	    	pass

	    def step(self, value):
	        self.count += value

	    def finalize(self):
	        return self.count

	conn.create_aggregate("finalStacks", 2, MySum)

	# Items bought
	# c.execute('''INSERT INTO participantItem (matchId, participantId, itemId, flatAp, percentAp)
	# 	SELECT event.matchId, event.participantId, event.itemId, item.flatAp, item.percentAp
	# 	FROM event
	# 	LEFT JOIN item ON event.itemId = item.id
	# 	WHERE event.type == "ITEM_PURCHASED"
	# 	''')
	# Resolve stacks
	# RoA
	c.execute('''SELECT * FROM participantItem WHERE participantItem.itemId = 3027''')
	print(c.fetchone())
	finalStacks = 0
	maxStacks = 0
	matchId = 0
	participantId = 0
	itemId = 0
	c.execute('''UPDATE participantItem SET finalStacks = ?, maxStacks = ?
		WHERE matchId = ? AND participantId = ? AND itemId = ?''',
		(finalStacks, maxStacks, matchId, participantId, itemId))
	# # Mejais
	# c.execute('''SELECT event.itemId, event.timestamp
	# FROM event
	# LEFT JOIN match ON event.matchId = match.id
	# WHERE event.type = "ITEM_PURCHASED" AND event.itemId = 3041
	# LIMIT 1''')
	# # Deathcap
	# c.execute('''SELECT event.itemId, 1
	# FROM event
	# LEFT JOIN match ON event.matchId = match.id
	# WHERE event.type = "ITEM_PURCHASED" AND event.itemId = 3089
	# LIMIT 1''')

	conn.commit()
except sqlite3.Error:
    traceback.print_exc()


conn.close()
input()