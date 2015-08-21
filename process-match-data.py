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

# Some useful views
try:
	c.execute('''CREATE VIEW matchParticipant AS
		SELECT match.*, participant.*
		FROM participant
		LEFT JOIN match ON participant.matchId = match.id;''')
	c.execute('''SELECT matchId,
		participantId,
		timestamp,
		type,
		itemId,
		itemBefore,
		itemAfter,
		item.name AS itemName
	FROM event
		LEFT JOIN
		[match] ON event.matchId = [match].id
		LEFT JOIN
		item ON [match].version = item.version AND 
				event.itemId = item.id
	WHERE event.type = "ITEM_PURCHASED" OR 
		event.type = "ITEM_DESTROYED" OR 
		event.type = "ITEM_SOLD" OR 
		event.type = "ITEM_UNDO"
	ORDER BY timestamp''')
	c.execute('''CREATE VIEW participantItemStatic AS
		SELECT matchId,
				participantId,
				itemId,
				name,
				flatAp
			FROM participantItem
				LEFT JOIN
				[match] ON participantItem.matchId = [match].id
				LEFT JOIN
				item ON [match].version = item.version AND 
						participantItem.itemId = item.id''')
	c.execute('''CREATE VIEW eventItem AS
					SELECT event.matchId,
						event.participantId,
						event.timestamp,
						event.type,
						event.itemId,
						event.itemBefore,
						event.itemAfter,
						participantFrame.totalGold
					FROM event
						LEFT JOIN
						participantFrame ON event.matchId = participantFrame.matchId AND 
											event.frameTimestamp = participantFrame.timestamp AND 
											event.participantId = participantFrame.participantId
					WHERE event.type = 'ITEM_PURCHASED' OR 
						event.type = 'ITEM_DESTROYED' OR 
						event.type = 'ITEM_SOLD' OR 
						event.type = 'ITEM_UNDO'
					ORDER BY event.timestamp''')
	# c.execute('''CREATE VIEW itemPurchaseDestroy AS
	# 	SELECT purchase.matchId,
	# 		purchase.participantId,
	# 		purchase.timestamp,
	# 		purchase.itemId AS itemBought,
	# 		destroy.itemId AS itemDestroyed
	# 	FROM (
	# 			SELECT matchId,
	# 					participantId,
	# 					timestamp,
	# 					itemId
	# 				FROM eventItem
	# 				WHERE type = "ITEM_PURCHASED"
	# 		)
	# 		AS purchase
	# 		JOIN
	# 		(
	# 			SELECT matchId,
	# 					participantId,
	# 					timestamp,
	# 					itemId
	# 				FROM eventItem
	# 				WHERE type = "ITEM_DESTROYED" OR 
	# 					type = "ITEM_SOLD"
	# 		)
	# 		AS destroy ON purchase.matchId = destroy.matchId AND 
	# 					purchase.participantId = destroy.participantId AND 
	# 					purchase.timestamp = destroy.timestamp''')
	# Items bought
	c.execute('''SELECT matchId, id FROM participant;''')
	for (matchId, participantId) in c.fetchall():
		c.execute('''SELECT timestamp, type, itemId, itemBefore, itemAfter, totalGold
			FROM eventItem
			WHERE matchId = ? AND participantId = ?;''', (matchId, participantId))
		events = c.fetchall()
		items = []
		print(matchId, participantId)
		for (idx, (timestamp, eventType, itemId, itemBefore, itemAfter, goldThreshold)) in enumerate(events):
			item = itemId
			if item == None or item=="NULL":
				item = itemBefore
			if item == None or item == 0:
				item = itemAfter
			print(eventType, item)
			if eventType == 'ITEM_PURCHASED':
				items.append((item, timestamp, goldThreshold))
			elif eventType == 'ITEM_DESTROYED' or eventType == 'ITEM_SOLD':
				items.pop(list(zip(*items))[0].index(item))
			elif eventType == 'ITEM_UNDO':
				originalTime = -1
				itemBuy = False
				for (timestamp, eventType, itemId, ib, ia, goldThreshold) in events[idx - 1::-1]:
					if timestamp < originalTime:
						break
					elif itemId == item:
						if eventType == 'ITEM_PURCHASED':
							# Undo a buy
							items.pop(list(zip(*items))[0].index(itemId))
							originalTime = timestamp
						else:
							# Undo a sell
							items.append((itemId, timestamp, goldThreshold))
							break
					elif originalTime > 0 and eventType == 'ITEM_DESTROYED':
						# Undo buy side effects
						items.append((itemId, timestamp, goldThreshold))
			if len(items) > 0:
				print(list(zip(*items))[0])
		if len(items) > 7:
			print('Participant #{} in match {} has too many items!'.format(participantId, matchId))
			print(list(zip(*items))[0])
			raise "Error"
		for (itemId, timeBought, goldThreshold) in items:
			c.execute('''INSERT INTO participantItem (matchId, participantId, itemId, timeBought, goldThreshold)
				VALUES (?, ?, ?, ?, ?)''',
				(matchId, participantId, itemId, timeBought, goldThreshold))
	print('Final items determined')
	# Resolve stacks
	# RoA
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
		finalStacks = min(matchDuration // 60 - timeBought // 1000 // 60, 10)
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
	# Mejais
	class finalStacks:
		def __init__(self):
			self.stacks = 5
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
			self.stacks = 5
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
	print('Item stacks resolved')

	# Item AP
	def stacksToAp(itemId, stacks):
		# RoA
		if itemId == 3027:
			return stacks * 4
		# Mejai
		elif itemId == 3041:
			return stacks * 8
		return 0;
	conn.create_function("stacksToAp", 2, stacksToAp)
	c.execute('''SELECT participant.matchId,
						participant.id,
						TOTAL(item.flatAp + stacksToAp(item.id, participantItem.finalStacks) ),
						MAX(item.percentAp) 
				FROM participant
					LEFT JOIN
					[match] ON participant.matchId = [match].id
					LEFT JOIN
					participantItem ON [match].id = participantItem.matchId AND 
									participant.id = participantItem.participantId
					LEFT JOIN
					item ON [match].version = item.version AND 
							participantItem.itemId = item.id
				GROUP BY participant.matchId, participant.id;''')
	for (matchId, participantId, totalFlatItemAp, totalPercentItemAp) in c.fetchall():
		c.execute('''UPDATE participant
			SET totalFlatItemAp = ?, totalPercentItemAp = ?
			WHERE participant.matchId = ? AND participant.id = ?''',
			(totalFlatItemAp, totalPercentItemAp, matchId, participantId))
	# Rune AP
	c.execute('''SELECT participant.matchId, participant.id, TOTAL(rune.flatAp), TOTAL(rune.percentAp)
		FROM participant
		LEFT JOIN match ON participant.matchId = match.id
		LEFT JOIN participantRune ON participant.matchId = participantRune.matchId AND participant.id = participantRune.participantId
		LEFT JOIN rune ON match.version = rune.version AND participantRune.runeId = rune.id
		GROUP BY participant.matchId, participant.id''')
	for (matchId, participantId, totalFlatRuneAp, totalPercentRuneAp) in c.fetchall():
		c.execute('''UPDATE participant
			SET totalFlatRuneAp = ?, totalPercentRuneAp = ?
			WHERE participant.matchId = ? AND participant.id = ?''',
			(totalFlatRuneAp, totalPercentRuneAp, matchId, participantId))
	# Mastery AP
	c.execute('''SELECT participant.matchId, participant.id, TOTAL(mastery.flatAp), TOTAL(mastery.percentAp)
		FROM participant
		LEFT JOIN match ON participant.matchId = match.id
		LEFT JOIN participantMastery ON match.id = participantMastery.matchId AND participant.id = participantMastery.participantId
		LEFT JOIN mastery ON match.version = mastery.version AND participantMastery.masteryId = mastery.id AND participantMastery.rank = mastery.rank
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
	print('Total AP calculated')

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
		EPSILON = 1
		def __init__(self):
			self.apItemCount = 0
			self.adItemCount = 0
		def step(self, championId, itemId):
			if itemId in self.apItems:
				self.apItemCount += 1
			if itemId in self.adItems:
				self.adItemCount += 1
		def finalize(self):
			if self.apItemCount >= (self.adItemCount + self.EPSILON if self.adItemCount > 0 else 1):
				return 'AP'
			elif self.adItemCount >= (self.apItemCount + self.EPSILON if self.apItemCount > 0 else 1):
				return 'AD'
			return 'Undecided'
	conn.create_aggregate('getBuildType', 2, getBuildType)
	c.execute('''SELECT participant.matchId, participant.id, getBuildType(participant.championId, participantItem.itemId)
			FROM participant
			LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
			GROUP BY participantItem.matchId, participantItem.participantId''')
	for (matchId, participantId, buildType) in c.fetchall():
		c.execute('''UPDATE participant SET buildType = ?
			WHERE matchId = ? AND id = ?''',
			(buildType, matchId, participantId))
	print('Build types analyzed')

	# Solo Kills
	c.execute('''UPDATE participant
				SET soloKills = (
					SELECT COUNT() 
						FROM event
							LEFT JOIN
							[match] ON event.matchId = [match].id
							LEFT JOIN
							assist ON assist.matchId = event.matchId AND 
									assist.eventId = event.id
						WHERE type = "CHAMPION_KILL" AND 
							assist.participantId IS NULL AND 
							[match].id = participant.matchId AND 
							event.killerId = participant.id);''')
	print('Solo kills counted')

	# Champion stats
	c.execute('''CREATE TABLE championStat (
			version TEXT,
			championId INTEGER,
			picks INTEGER,
			bans INTEGER
			wins INTEGER,
			role TEXT,
			lane TEXT,
			buildType TEXT,
			winRate INTEGER,
			kills INTEGER,
			deaths INTEGER,
			assists INTEGER,
			assassinations INTEGER,
			firstBloodKillOrAssist INTEGER,
			firstTowerKillOrAssist INTEGER,
			totalTimeCrowdControlDealt INTEGER,
			damageDealt INTEGER,
			damageDealtToChampions INTEGER,
			magicDamageDealt INTEGER,
			magicDamageDealtToChampions INTEGER,
			avgTotalAp REAL,
			FOREIGN KEY (version, championId) REFERENCES champion(version, id)
		)''')
	c.execute('''INSERT INTO championStat (version, championId, winRate, picks, kills, deaths, assists, assassinations, firstBloodKillOrAssist,
		firstTowerKillOrAssist, totalTimeCrowdControlDealt, damageDealt, damageDealtToChampions, magicDamageDealt, magicDamageDealtToChampions, avgTotalAp)
			SELECT match.version, participant.championId, AVG(team.winner), COUNT(*), AVG(participant.kills), AVG(participant.deaths),
			AVG(participant.assists), AVG(participant.assassinations), AVG(participant.firstBloodKill + participant.firstBloodAssist),
			AVG(participant.firstTowerKill + participant.firstTowerAssist), AVG(participant.totalTimeCrowdControlDealt), AVG(participant.damageDealt),
			AVG(participant.damageDealtToChampions), AVG(participant.magicDamageDealt), AVG(participant.magicDamageDealtToChampions),
			AVG(participant.totalAp)
			FROM participant
			LEFT JOIN match ON participant.matchId = match.id
			LEFT JOIN team ON participant.matchId = team.matchId AND participant.teamId = team.id
			GROUP BY match.version, participant.championId''', ())
	c.execute('''UPDATE championStat
		SET bans = (SELECT COUNT(*)
			FROM ban
			LEFT JOIN match ON ban.matchId = match.id
			WHERE championStat.version = match.version AND championStat.championId = ban.championId
			)''')
	print('Champion power determined')

	# Item stats
	c.execute('''CREATE TABLE itemStat (
			version TEXT,
			itemId INTEGER,
			timesBought INTEGER,
			winRate REAL,
			goldThreshold REAL,
			FOREIGN KEY (version, itemId) REFERENCES item(version, id)
		)''')
	c.execute('''INSERT INTO itemStat (version, itemId, timesBought, goldThreshold)
			SELECT match.version, participantItem.itemId, COUNT(*), AVG(participantItem.goldThreshold)
			FROM participant
			LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
			LEFT JOIN match ON participant.matchId = match.id
			LEFT JOIN team ON participant.matchId = team.matchId AND participant.teamId = team.id
			GROUP BY match.version, participantItem.itemId''', ())
	c.execute('''UPDATE itemStat
		SET winRate = (SELECT AVG(team.winner)
			FROM participant
			LEFT JOIN match ON participant.matchId = match.id
			LEFT JOIN team ON match.id = team.matchId AND participant.teamId = team.id
			LEFT JOIN participantItem ON match.id = participantItem.matchId AND participant.id = participantItem.participantId
			WHERE itemStat.version = match.version AND itemStat.itemId = participantItem.itemId
			GROUP BY participant.id
			)''')
	print('Item efficiency analysis complete')

	# Player stats
	c.execute('''CREATE TABLE playerChampion (
		playerId INTEGER NOT NULL REFERENCES player(id),
		championId INTEGER NOT NULL,
		version TEXT,
		picks INTEGER,
		FOREIGN KEY (championId, version) REFERENCES champion(id, version)
		)''')
	c.execute('''INSERT INTO playerChampion (playerId, championId, version, picks)
		SELECT player.id, participant.championId, match.version, COUNT(*)
		FROM player
		LEFT JOIN participant ON player.id = participant.playerId
		LEFT JOIN match ON participant.matchId = match.id
		GROUP BY player.id, participant.championId
		''')
	c.execute('''CREATE TABLE playerItem (
		playerId INTEGER REFERENCES player(id),
		itemId INTEGER NOT NULL REFERENCES item(id),
		timesBought INTEGER,
		avgTimeBought INTEGER,
		version TEXT
		)''')
	c.execute('''INSERT INTO playerItem (playerId, itemId, version, timesBought, avgTimeBought)
		SELECT player.id, participantItem.itemId, match.version, COUNT(*), AVG(participantItem.timeBought)
		FROM player
		LEFT JOIN participant ON player.id = participant.playerId
		LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
		LEFT JOIN match ON participant.matchId = match.id
		GROUP BY player.id, match.version, participantItem.itemId
		''')
	c.execute('''CREATE TABLE playerStat (
		playerId INTEGER REFERENCES player(id),
		version TEXT,
		gamesPlayed INTEGER,
		apPicks INTEGER,
		adPicks INTEGER)
		''')
	c.execute('''INSERT INTO playerStat (playerId, version, gamesPlayed)
		SELECT player.id, match.version, COUNT(*)
		FROM player
		LEFT JOIN participant ON player.id = participant.playerId
		LEFT JOIN match ON participant.matchId = match.id
		GROUP BY match.version, player.id
		''')
	c.execute('''UPDATE playerStat
		SET
			apPicks = (
				SELECT COUNT(*)
				FROM player
				LEFT JOIN participant ON player.id = participant.playerId
				LEFT JOIN match ON participant.matchId = match.id
				WHERE playerStat.playerId = player.id AND playerStat.version = match.version AND participant.buildType = "AP"
			),
			adPicks = (
				SELECT COUNT(*)
				FROM player
				LEFT JOIN participant ON player.id = participant.playerId
				LEFT JOIN match ON participant.matchId = match.id
				WHERE playerStat.playerId = player.id AND playerStat.version = match.version AND participant.buildType = "AD"
			)
		''')
	print('Player profiling complete')

	# Item cross join
	c.execute('''SELECT m1.version,
		item1.itemId AS i1,
		item2.itemId AS i2,
		COUNT()
	FROM participantItem AS item1
		LEFT JOIN
		[match] AS m1 ON item1.matchId = m1.id
		CROSS JOIN
		participantItem AS item2 ON item1.matchId = item2.matchId AND
									item1.participantId = item2.participantId
		LEFT JOIN
		[match] AS m2 ON item2.matchId = m2.id
	WHERE m1.version = m2.version AND
		item1.rowid != item2.rowid
	GROUP BY m1.version,
			i1,
			i2;
''')
	print('Item correlations cross-referenced')
except:
	traceback.print_exc()

conn.commit()


conn.close()
print('Done!')
input()