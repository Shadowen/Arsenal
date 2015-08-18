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
	# Items bought
	c.execute('''INSERT INTO participantItem (matchId, participantId, itemId, timeBought, flatAp, percentAp, goldThreshold)
		SELECT event.matchId, event.participantId, event.itemId, event.timestamp, item.flatAp, item.percentAp, participantFrame.totalGold
		FROM event
		LEFT JOIN item ON event.itemId = item.id
		LEFT JOIN participantFrame ON event.matchId = participantFrame.matchId AND event.participantId = participantFrame.participantId AND CAST(event.timestamp / 60000 AS INTEGER) * 60000 = participantFrame.timestamp
		WHERE event.type == "ITEM_PURCHASED"
		''')
	# Resolve stacks
	# RoA
	try:
		c.execute('''SELECT matchId, participantId, timeBought
			FROM participantItem
			WHERE participantItem.itemId = 3027
			GROUP BY matchId''')
		storedMatchId = -1
		for (matchId, participantId, timeBought) in c.fetchall():
			# Cache matchDuration to minimize additional queries
			if matchId != storedMatchId:
				c.execute('''SELECT duration
					FROM match
					WHERE id = ?''', (matchId,))
				storedMatchId = matchId
				matchDuration = c.fetchone()[0]
			# Calculate the final number of stacks
			finalStacks = min(matchDuration // 60 - timeBought // 1000 // 60, 20)
			# Update the table
			c.execute('''UPDATE participantItem
				SET finalStacks = ?, maxStacks = ?
				WHERE matchId = ? AND participantId = ? AND itemId = 3027''',
				(finalStacks, finalStacks, matchId, participantId))
			# Multiple of the same item bought? Need SQLITE_enable_update_delete_limit
			# c.execute('''UPDATE participantItem SET finalStacks = ?, maxStacks = ?
			# 	WHERE matchId = ? AND participantId = ? AND itemId = 3027
			# 	ORDER BY timeBought
			# 	LIMIT 1''',
			# 	(finalStacks, maxStacks, matchId, participantId))
	except:
		traceback.print_exc()
	# Mejais
	try:
		class finalStacks:
			def __init__(self):
				self.stacks = 6
			def step(self, participantId, killerId, victimId, assistId):
				if participantId == killerId:
					self.stacks = min(self.stacks + 2, 20)
				elif participantId == victimId:
					self.stacks //= 2
				elif participantId == assistId:
					self.stacks = min(self.stacks + 1, 20)
				else:
					print(participantId, killerId, victimId, assistId)
					raise 'Error'
			def finalize(self):
				return self.stacks
		conn.create_aggregate("finalStacks", 4, finalStacks)
		class maxStacks:
			def __init__(self):
				self.stacks = 6
				self.maxStacks = self.stacks
			def step(self, participantId, killerId, victimId, assistId):
				if participantId == killerId:
					self.stacks = min(self.stacks + 2, 20)
				elif participantId == victimId:
					self.stacks //= 2
				elif participantId == assistId:
					self.stacks = min(self.stacks + 1, 20)
				else:
					print(participantId, killerId, victimId, assistId)
					raise 'Error'
				self.maxStacks = max(self.stacks, self.maxStacks)
			def finalize(self):
				return self.maxStacks
		conn.create_aggregate("maxStacks", 4, maxStacks)
		c.execute('''SELECT matchId, participantId, timeBought
			FROM participantItem
			WHERE participantItem.itemId = 3041
			GROUP BY matchId''')
		for (matchId, participantId, timeBought) in c.fetchall():
			# Calculate the final number of stacks
			c.execute('''SELECT ?, event.killerId, event.victimId, assist.participantId
				FROM event
				LEFT JOIN (
					SELECT assist.matchId, assist.eventId, assist.participantId
					FROM assist
					WHERE assist.participantId = ?
					) AS assist ON event.matchId = assist.matchId AND event.id = assist.eventId
				WHERE event.type == 'CHAMPION_KILL' AND event.timestamp > ? AND
				(event.killerId == ? OR event.victimId == ? OR assist.participantId == ?)
				ORDER BY event.timestamp''',
				(participantId, participantId, timeBought, participantId, participantId, participantId))
			c.execute('''SELECT
				finalStacks(?, event.killerId, event.victimId, assist.participantId),
				maxStacks(?, event.killerId, event.victimId, assist.participantId)
				FROM event
				LEFT JOIN assist ON event.matchId = assist.matchId AND event.id = assist.eventId
				WHERE event.type == 'CHAMPION_KILL' AND event.timestamp > ? AND
				(event.killerId == ? OR event.victimId == ? OR assist.participantId == ?)
				ORDER BY event.timestamp''',
				(participantId, participantId, timeBought, participantId, participantId, participantId))
			finalStacks, maxStacks = c.fetchone()
			# Update database
			c.execute('''UPDATE participantItem
				SET finalStacks = ?, maxStacks = ?
				WHERE matchId = ? AND participantId = ? AND itemId = 3041''',
				(finalStacks, maxStacks, matchId, participantId))
	except:
		traceback.print_exc()
	try:
		# Item AP
		c.execute('''SELECT participant.matchId, participant.id, TOTAL(item.flatAp + participantItem.finalStacks * 20), MAX(item.percentAp)
			FROM participant
			LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
			LEFT JOIN item ON participantItem.itemId = item.id
			GROUP BY participant.matchId, participant.id''')
		# WHERE participantItem.stacks = 0 OR participantItem.itemId = RoA OR Mejai	
		for (matchId, participantId, totalFlatItemAp, totalPercentItemAp) in c.fetchall():
			c.execute('''UPDATE participant
				SET totalFlatItemAp = ?, totalPercentItemAp = ?
				WHERE participant.matchId = ? AND participant.id = ?''',
				(totalFlatItemAp, totalPercentItemAp, matchId, participantId))
		# Rune AP
		c.execute('''SELECT participant.matchId, participant.id, TOTAL(rune.flatAp), TOTAL(rune.percentAp)
			FROM participant
			LEFT JOIN participantRune ON participant.matchId = participantRune.matchId AND participant.id = participantRune.participantId
			LEFT JOIN rune ON participantRune.runeId = rune.id
			GROUP BY participant.matchId, participant.id''')
		for (matchId, participantId, totalFlatRuneAp, totalPercentRuneAp) in c.fetchall():
			c.execute('''UPDATE participant
				SET totalFlatRuneAp = ?, totalPercentRuneAp = ?
				WHERE participant.matchId = ? AND participant.id = ?''',
				(totalFlatRuneAp, totalPercentRuneAp, matchId, participantId))
		# Mastery AP
		c.execute('''SELECT participant.matchId, participant.id, TOTAL(mastery.flatAp), TOTAL(mastery.percentAp)
			FROM participant
			LEFT JOIN participantMastery ON participant.matchId = participantMastery.matchId AND participant.id = participantMastery.participantId
			LEFT JOIN mastery ON participantMastery.masteryId = mastery.id AND participantMastery.rank = mastery.rank
			GROUP BY participant.matchId, participant.id''')
		for (matchId, participantId, totalFlatMasteryAp, totalPercentMasteryAp) in c.fetchall():
			c.execute('''UPDATE participant
				SET totalFlatMasteryAp = ?, totalPercentMasteryAp = ?
				WHERE participant.matchId = ? AND participant.id = ?''',
				(totalFlatMasteryAp, totalPercentMasteryAp, matchId, participantId))
		# Total AP
		c.execute('''UPDATE participant
			SET totalAp = (
				SELECT (totalFlatItemAp + totalFlatRuneAp + totalFlatMasteryAp) *
				(1 + (totalPercentItemAp + totalPercentRuneAp + totalPercentMasteryAp) / 100)
				FROM participant AS p
				WHERE participant.matchId = p.matchId AND participant.id = p.id
				)
		''')
	except:
		traceback.print_exc()
	try:
		# Build type
		class getBuildType:
			def __init__(self):
				self.type = 'AD'
			def step(self, championId, itemId):
				self.type = self.type = 'AD' if self.type == 'AP' else 'AD'
			def finalize(self):
				return self.type
		conn.create_aggregate("getBuildType", 2, getBuildType)
		c.execute('''UPDATE participant
			SET buildType = (
				SELECT getBuildType(championId, itemId)
				FROM participantItem 
				WHERE participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
				GROUP BY participantItem.matchId, participantItem.participantId
			)
			''')
	except:
		traceback.print_exc()
	conn.commit()
except sqlite3.Error:
	traceback.print_exc()


conn.close()
print('Done!')
input()