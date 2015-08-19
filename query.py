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
	# c.execute('''SELECT totalFlatItemAp, totalPercentItemAp, totalFlatRuneAp, totalPercentRuneAp
	# 	FROM participant
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	WHERE match.id = 1852538938 and participant.id = 2''')
	# print(json.dumps(c.fetchall(), indent=2))
	c.execute('''SELECT participantItem.itemId, item.id, item.name, match.version
		FROM participantItem
		LEFT JOIN match ON participantItem.matchId = match.id
		LEFT JOIN item ON participantItem.itemId = item.id AND match.version = item.version
		WHERE matchId = 1852538938 AND participantId = 2;
		''')
	print(json.dumps(c.fetchall(), indent=2))
	conn.commit()
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()


1852538938
2
74