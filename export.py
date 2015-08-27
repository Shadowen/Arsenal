import json

import sqlite3

import traceback

from functools import reduce

# Init
conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
	# The items you want to export
	bigItems = set([3001, 3003, 3004, 3006, 3009, 3020, 3022, 3023, 3025, 3026, 3027, 3031, 3035, 3041, 3046, 3047, 3050, 3056, 3060, 3065, 3068, 3069, 3071,
		3072, 3074, 3075, 3078, 3083, 3084, 3085, 3087, 3089, 3091, 3092, 3100, 3102, 3110, 3111, 3115, 3116, 3117, 3122, 3124, 3135, 3139, 3141, 3142, 3143,
		3146, 3151, 3152, 3153, 3156, 3157, 3158, 3165, 3172, 3174, 3180, 3190, 3222, 3285, 3290, 3401, 3504, 3508, 3512, 3706, 3711, 3713, 3715, 3742, 3800])
	# Nodes
	def exportNodes():
		c.execute('''SELECT itemStat.version, itemStat.id, item.name, itemStat.winRate
			FROM itemStat
			LEFT JOIN item ON itemStat.version = item.version AND itemStat.id = item.id
			''')
		def nodeFilter(node):
			return node[1] in bigItems
		def nodesToDict(node):
			return {
				'version' : node[0],
				'id' : node[1],
				'name' : node[2],
				'winRate': node[3]
			}
		return list(map(nodesToDict, filter(nodeFilter, c.fetchall())))
	# Links
	def exportLinks():
		c.execute('''SELECT [match].version,
			item1 AS item1Id,
			item2 AS item2Id,
			CAST (COUNT() AS FLOAT) / (
										SELECT TOTAL(itemStat.timesBought) 
											FROM itemStat
											WHERE match.version = itemStat.version AND
											    (item1 = itemStat.id OR item2 = itemStat.id)
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
			GROUP BY [match].version,
				item1,
				item2
			''')
		def linkFilter(link):
			return (link[1] in bigItems and link[2] in bigItems) and link[3] > 0
		def linksToDict(link):
			return {
				'version' : link[0],
				'source' : link[1],
				'target' : link[2],
				'value' : link[3]
			}
		return list(map(linksToDict, filter(linkFilter, c.fetchall())))
	with open('itemCross.json', 'w') as f:
		f.write(
			json.dumps({
			'nodes' : exportNodes(),
			'links' : exportLinks()
			}
			)
		)


	# Buy times
	c.execute('''SELECT itemStat.version, itemStat.id, item.name, itemStat.avgBuyTime, itemStat.medianBuyTime, itemStat.otherBuyTime, itemStat.winRate
		FROM itemStat
		LEFT JOIN item ON itemStat.version = item.version AND itemStat.id = item.id
		GROUP BY itemStat.id, itemStat.version
		''')
	def itemFilter(item):
		return item[1] in bigItems
	def itemToDict(item):
		return {
				'version' : item[0],
				'id' : item[1],
				'name' : item[2],
				'avgBuyTime' : item[3],
				'medianBuyTime' : item[4],
				'otherBuyTime' : item[5],
				'winRate' : item[6]
			}
	def itemReduce(prev, curr):
		if curr['id'] not in prev:
			prev[curr['id']] = {}
		prev[curr['id']][curr['version']] = curr
		return prev
	items = reduce(
				itemReduce, 
				map(
					itemToDict,
					filter(
						itemFilter,
						c.fetchall()
					)
				),
				{}
			)
	with open('itemStats.json', 'w') as f:
		f.write(json.dumps(items))
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()
