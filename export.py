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
	data = {}
	# Nodes
	c.execute('''SELECT itemStat.version, itemStat.id, item.name, itemStat.winRate
		FROM itemStat
		LEFT JOIN item ON itemStat.version = item.version AND itemStat.id = item.id;
		''')
	def nodesToDict(node):
		return {
			'version' : node[0],
			'id' : node[1],
			'name' : node[2],
			'winRate': node[3]
		}
	data['nodes'] = list(map(nodesToDict, c.fetchall()))
	# Links
	c.execute('''SELECT [match].version,
       item1 AS item1Id,
       item2 AS item2Id,
       COUNT() 
  FROM (
           SELECT i1.matchId,
                  i1.participantId,
                  i1.itemId AS item1,
                  i2.itemId AS item2
             FROM participantItem AS i1
                  CROSS JOIN
                  participantItem AS i2 ON i1.matchId = i2.matchId AND 
                                           i1.participantId = i2.participantId AND 
                                           i1.itemId < i2.itemId
       )
       LEFT JOIN
       [match] ON matchId = [match].id
       LEFT JOIN
       item AS item1 ON [match].version = item1.version AND 
                        item1 = item1.id
       LEFT JOIN
       item AS item2 ON [match].version = item2.version AND 
                        item2 = item2.id
 GROUP BY [match].version,
          item1,
          item2
		''')
	def linksToDict(link):
		return {
			'version' : link[0],
			'source' : link[1],
			'target' : link[2],
			'value' : link[3]
		}
	data['links'] = list(map(linksToDict, c.fetchall()))
	with open('itemCross.json', 'w') as f:
		f.write(json.dumps(data))
	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()
