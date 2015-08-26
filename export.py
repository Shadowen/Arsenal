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
	data = {'nodes' : [], 'links' : []}
	# The items you want to export
	bigItems = set([3001, 3003, 3004, 3006, 3009, 3020, 3022, 3023, 3025, 3026, 3027, 3031, 3035, 3041, 3046, 3047, 3050, 3056, 3060, 3065, 3068, 3069, 3071,
		3072, 3074, 3075, 3078, 3083, 3084, 3085, 3087, 3089, 3091, 3092, 3100, 3102, 3110, 3111, 3115, 3116, 3117, 3122, 3124, 3135, 3139, 3141, 3142, 3143,
		3146, 3151, 3152, 3153, 3156, 3157, 3158, 3165, 3172, 3174, 3180, 3190, 3222, 3285, 3290, 3401, 3504, 3508, 3512, 3706, 3711, 3713, 3715, 3742, 3800])
	# Nodes
	def exportNodes(version):
		c.execute('''SELECT itemStat.version, itemStat.id, item.name, itemStat.winRate
			FROM itemStat
			LEFT JOIN item ON itemStat.version = item.version AND itemStat.id = item.id
			WHERE itemStat.version = ?
			''', (version,))
		def nodeFilter(node):
			return node[1] in bigItems
		def nodesToDict(node):
			if node[1] == 3250:
				print('probs!')
			return {
				'version' : node[0],
				'id' : node[1],
				'name' : node[2],
				'winRate': node[3]
			}
		data['nodes'] += list(map(nodesToDict, filter(nodeFilter, c.fetchall())))
	# Links
	def exportLinks(version):
		c.execute('''SELECT [match].version,
	       item1 AS item1Id,
	       item2 AS item2Id,
	       CAST (COUNT() AS FLOAT) / (
	                                     SELECT COUNT(DISTINCT id) 
	                                       FROM [match]
	                                 )
	  FROM (
	           SELECT i1.matchId,
	                  i1.participantId,
	                  i1.shortItemId AS item1,
	                  i2.shortItemId AS item2
	             FROM participantItem AS i1
	                  CROSS JOIN
	                  participantItem AS i2 ON i1.matchId = i2.matchId AND 
	                                           i1.participantId = i2.participantId AND 
	                                           i1.shortItemId < i2.shortItemId
	       )
	       LEFT JOIN
	       [match] ON matchId = [match].id
	       LEFT JOIN
	       item AS item1 ON [match].version = item1.version AND 
	                        item1 = item1.id
	       LEFT JOIN
	       item AS item2 ON [match].version = item2.version AND 
	                        item2 = item2.id
	 WHERE [match].version = ?
	 GROUP BY [match].version,
	          item1,
	          item2
			''', (version,))
		def linkFilter(link):
			return (link[1] in bigItems and link[2] in bigItems) and link[3] > 0
		def linksToDict(link):
			return {
				'version' : link[0],
				'source' : link[1],
				'target' : link[2],
				'value' : link[3]
			}
		data['links'] += list(map(linksToDict, filter(linkFilter, c.fetchall())))
	exportNodes('5.11')
	exportNodes('5.14')
	exportLinks('5.11')
	exportLinks('5.14')
	with open('itemCross.json', 'w') as f:
		f.write(json.dumps(data))
	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()
