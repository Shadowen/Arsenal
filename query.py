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
	class getBuildType:
		# 3006: Zerks
		# 3153: BotRK
		# 3072: BT
		# 3035: LW
		# 3031: IE
		# 3046: PD
		adItems = set([3006, 3153, 3072, 3035, 3031, 3046])
		# 3001: Abyssal
		# 3027: RoA
		# 3157: Hourglass
		# 3165: Morello
		# 3089: DCap
		# 3151: Liandry
		# 3116: Rylai
		# 3036: Seraph
		# 3041: Mejai
		apItems = set([3001, 3027, 3157, 3165, 3089, 3151, 3116, 3036, 3041])
		def __init__(self):
			self.apItemCount = 0
			self.adItemCount = 0
		def step(self, championId, itemId):
			if itemId in self.apItems:
				self.apItemCount += 1
			if itemId in self.adItems:
				self.adItemCount += 1
		def finalize(self):
			if self.apItemCount > self.adItemCount:
				return 'AP'
			elif self.adItemCount > self.apItemCount:
				return 'AD'
			return 'Undecided'
	conn.create_aggregate("getBuildType", 2, getBuildType)
	c.execute('''SELECT participant.matchId, participant.id, getBuildType(participant.championId, participantItem.itemId)
				FROM participant
				LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
				GROUP BY participantItem.matchId, participantItem.participantId''')
	print(json.dumps(c.fetchall(), indent=2))
except:
	traceback.print_exc()


conn.close()
print('Done!')
input()