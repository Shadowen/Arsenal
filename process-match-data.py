import urllib3
import certifi

import json

import sqlite3

import traceback
import math
import time
from functools import reduce

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
					ORDER BY event.rowId''')
		# Item stats
	c.execute('''CREATE VIEW itemStat AS 
			SELECT [match].version AS version,
		       participantItem.shortItemId AS id,
		       AVG(participantItem.timeBought) AS timeBought,
		       AVG(participantItem.finalStacks) AS finalStacks,
		       AVG(participantItem.goldThreshold) AS goldThreshold,
		       AVG(team.winner) AS winRate
		  FROM participant
		       LEFT JOIN
		       [match] ON participant.matchId = [match].id
		       LEFT JOIN
		       team ON [match].id = team.matchId AND 
		               participant.teamId = team.id
		       INNER JOIN
		       participantItem ON [match].id = participantItem.matchId AND 
		                          participant.id = participantItem.participantId
		       LEFT JOIN
		       item ON [match].version = item.version AND 
		               participantItem.shortItemId = item.id
		 GROUP BY [match].version,
		          participantItem.shortItemId;
		''')
	print('Item efficiency analysis complete')
	# Items bought
	c.execute('''SELECT matchId, id, championId FROM participant;''')
	for (matchId, participantId, championId) in c.fetchall():
		c.execute('''SELECT type, itemId, timestamp, totalGold
			FROM eventItem
			WHERE matchId = ? AND participantId = ?;''', (matchId, participantId))
		events = c.fetchall()
		items = []
		playerActions = []
		idx = 0
		if championId == 429:
			# Kalista's Black Spear
			items.append((3599, 0, 0))
		elif championId == 112:
			# Viktor's Hex Core
			items.append((3200, 0, 0))
		while idx < len(events):
			# Init
			event = events[idx]
			eventType = event[0]
			item = (event[1], event[2], event[3])
			# Conditions
			if eventType == 'ITEM_PURCHASED':
				items.append(item)
				itemsDestroyed = []
				idx += 1
				while idx < len(events):
					destroyEvent = events[idx]
					destroyItem = (destroyEvent[1], destroyEvent[2], destroyEvent[3])
					if destroyItem[1] != item[1] or destroyEvent[0] != 'ITEM_DESTROYED':
						break
					items.pop(list(zip(*items))[0].index(destroyItem[0]))
					itemsDestroyed.append(destroyItem)
					idx += 1
				playerActions.append(('buy', item, itemsDestroyed))
				continue
			elif eventType == 'ITEM_SOLD':
				item = items.pop(list(zip(*items))[0].index(item[0]))
				playerActions.append(('sell', item))
			elif eventType == 'ITEM_DESTROYED':
				# Elixirs TODO can be consumed before buying?
				if item[0] == 2137 or item[0] == 2138 or item[0] == 2139 or item[0] == 2140:
					break
				items.pop(list(zip(*items))[0].index(item[0]))
				# Archangel -> Seraph
				if item[0] == 3003:
					items.append((3040, item[1], item[2]))
				# Manamune -> Muramana
				elif item[0] == 3004:
					items.append((3041, item[1], item[2]))
				# Devourer -> Sated Devourer
				# Stalker's Blade
				elif item[0] == 3710:
					items.append((3930, item[1], item[2]))
				# Poacher's Knife
				elif item[0] == 3722:
					items.append((3932, item[1], item[2]))
				# Skirmisher's Sabre
				elif item[0] == 3718:
					items.append((3931, item[1], item[2]))
				# Ranger's Trailblazer
				elif item[0] == 3726:
					items.append((3933, item[1], item[2]))
			elif eventType == 'ITEM_UNDO':
				action = playerActions.pop()
				if action[0] == 'buy':
					# Undo buy
					items.pop(list(zip(*items))[0].index(action[1][0]))
					items.extend(action[2])
				elif action[0] == 'sell':
					# Undo sell
					items.append(action[1])
			# Increment
			idx += 1

		# Disable error checking for better performance
		# def collapseStackables(prev, curr):
		# 	# HPot, MPot, Biscuit, Ward, VWard
		# 	stackables = [2003, 2004, 2010, 2044, 2043]
		# 	if curr in prev and curr in stackables:
		# 		return prev
		# 	return prev + [curr]
		# if len(reduce(collapseStackables, map(lambda i: i[0], items), [])) > 7:
		# 	print('Participant #{} in match {} has too many items!'.format(participantId, matchId))
		# 	print(list(zip(*items))[0])
		# 	raise "Error"

		def shortenItems(itemId):
			mapping = {
			# Ruby Sightstone -> Sightstone
			2045 : 2049,
			# Seraph -> Archangel
			3040 : 3003, 3048 : 3003, 3007 : 3003,
			# Muramana -> Manamune
			3043 : 3004, 3042 : 3004, 3008 : 3004,
			# Swiftness
			1306 : 3009, 1308 : 3009, 1035 : 3009, 1307 : 3009, 1309 : 3009, 1336 : 3009, 3280 : 3009, 3284 : 3009, 3281 : 3009, 3283 : 3009, 3282 : 3009, 3280 : 3009,
			# Mobi
			1326 : 3117, 1328 : 3117, 1325 : 3117, 1327 : 3117, 1329 : 3117, 1340 : 3117, 3270 : 3117, 3271 : 3117, 3273 : 3117, 3270 : 3117, 3274 : 3117, 3272 : 3117,
			# Lucidity
			1331 : 3158, 1333 : 3158, 1330 : 3158, 1332 : 3158, 1334 : 3158, 1341 : 3158, 3275 : 3158, 3276 : 3158, 3278 : 3158, 3279 : 3158, 3277 : 3158, 3275 : 3158,
			# Mercury Treads
			1321 : 3111, 1323 : 3111, 1320 : 3111, 1322 : 3111, 1324 : 3111, 1339 : 3111, 3265 : 3111, 3269 : 3111, 3268 : 3111, 3266 : 3111, 3267 : 3111, 3265 : 3111,
			# Bezerker's
			1301 : 3006, 1303 : 3006, 1300 : 3006, 1302 : 3006, 1304 : 3006, 1335 : 3006, 3250 : 3006, 3254 : 3006, 3252 : 3006, 3251 : 3006, 3253 : 3006,
			# Ninja Tabi
			1316 : 3047, 1318 : 3047, 1315 : 3047, 1317 : 3047, 1319 : 3047, 1338 : 3047, 3260 : 3047, 3261 : 3047, 3263 : 3047, 3262 : 3047, 3060 : 3047, 3264 : 3047,
			# Sorcs
			1311 : 3020, 1313 : 3020, 1310 : 3020, 1312 : 3020, 1314 : 3020, 1337 : 3020, 3255 : 3020, 3257 : 3020, 3256 : 3020, 3259 : 3020, 3258 : 3020,
			# Stalker's Blade
			3707 : 3706, 3708 : 3706, 3709 : 3706, 3710 : 3706, 3930 : 3706,
			# Poacher's Knife
			3719 : 3711, 3720 : 3711, 3721 : 3711, 3722 : 3711, 3932 : 3711,
			# Skirmisher's Sabre
			3714 : 3715, 3716 : 3715, 3717 : 3715, 3718 : 3715, 3931 : 3715,
			# Ranger's Trailblazer
			3723 : 3713, 3724 : 3713, 3725 : 3713, 3726 : 3713, 3933 : 3713,
			# Warding Totem
			3361 : 3340, 3362 : 3340,
			# Sweeping Lens
			3364 : 3341,
			# Scrying Orb
			3363 : 3342
			}
			if itemId in mapping:
				return mapping[itemId]
			return itemId

		for (itemId, timeBought, goldThreshold) in items:
			c.execute('''INSERT INTO participantItem (matchId, participantId, itemId, shortItemId, timeBought, goldThreshold)
				VALUES (?, ?, ?, ?, ?, ?)''',
				(matchId, participantId, itemId, shortenItems(itemId), timeBought, goldThreshold))
	print('Final items determined')
	# Resolve stacks
	# RoA
	c.execute('''SELECT matchId, participantId, timeBought
		FROM participantItem
		WHERE participantItem.itemId = 3027''')
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
	print('RoA stacks resolved')
	# Mejais
	c.execute('''SELECT matchId, participantId, timeBought
		FROM participantItem
		WHERE participantItem.itemId = 3041''')
	for (matchId, participantId, timeBought) in c.fetchall():
		# Calculate the final number of stacks
		c.execute('''SELECT event.killerId, event.victimId, assist.participantId
			FROM event
			LEFT JOIN assist ON event.matchId = assist.matchId AND event.id = assist.eventId
			WHERE event.matchId = ? AND event.type = 'CHAMPION_KILL' AND event.timestamp > ? AND
			(event.killerId = ? OR event.victimId = ? OR assist.participantId = ?)
			ORDER BY event.rowId''',
			(matchId, timeBought, participantId, participantId, participantId))
		stacks = 5
		maxStacks = stacks
		for (killer, victim, assistant) in c.fetchall():
			if participantId == killer:
				stacks = min(stacks + 2, 20)
			elif participantId == victim:
				stacks //= 2
			elif participantId == assistant:
				stacks = min(stacks + 1, 20)
			else:
				print(matchId, participantId, killer, victim, assitant)
				raise 'Error'
			maxStacks = max(stacks, maxStacks)
		# Update database
		c.execute('''UPDATE participantItem
			SET finalStacks = ?, maxStacks = ?
			WHERE matchId = ? AND participantId = ? AND itemId = 3041''',
			(stacks, maxStacks, matchId, participantId))
	print('Stacking items resolved')

	# Item AP
	# def stacksToAp(itemId, stacks):
	# 	# RoA
	# 	if itemId == 3027:
	# 		return stacks * 4
	# 	# Mejai
	# 	elif itemId == 3041:
	# 		return stacks * 8
	# 	return 0;
	# conn.create_function("stacksToAp", 2, stacksToAp)
	# c.execute('''SELECT participant.matchId,
	# 					participant.id,
	# 					TOTAL(item.flatAp + stacksToAp(item.id, participantItem.finalStacks)),
	# 					MAX(item.percentAp) 
	# 			FROM participant
	# 				LEFT JOIN
	# 				[match] ON participant.matchId = [match].id
	# 				LEFT JOIN
	# 				participantItem ON [match].id = participantItem.matchId AND 
	# 								participant.id = participantItem.participantId
	# 				LEFT JOIN
	# 				item ON [match].version = item.version AND 
	# 						participantItem.itemId = item.id
	# 			GROUP BY participant.matchId, participant.id;''')
	# for (matchId, participantId, totalFlatItemAp, totalPercentItemAp) in c.fetchall():
	# 	c.execute('''UPDATE participant
	# 		SET totalFlatItemAp = ?, totalPercentItemAp = ?
	# 		WHERE participant.matchId = ? AND participant.id = ?''',
	# 		(totalFlatItemAp, totalPercentItemAp, matchId, participantId))
	# # Rune AP
	# c.execute('''SELECT participant.matchId, participant.id, TOTAL(rune.flatAp), TOTAL(rune.percentAp)
	# 	FROM participant
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	LEFT JOIN participantRune ON participant.matchId = participantRune.matchId AND participant.id = participantRune.participantId
	# 	LEFT JOIN rune ON match.version = rune.version AND participantRune.runeId = rune.id
	# 	GROUP BY participant.matchId, participant.id''')
	# for (matchId, participantId, totalFlatRuneAp, totalPercentRuneAp) in c.fetchall():
	# 	c.execute('''UPDATE participant
	# 		SET totalFlatRuneAp = ?, totalPercentRuneAp = ?
	# 		WHERE participant.matchId = ? AND participant.id = ?''',
	# 		(totalFlatRuneAp, totalPercentRuneAp, matchId, participantId))
	# # Mastery AP
	# c.execute('''SELECT participant.matchId, participant.id, TOTAL(mastery.flatAp), TOTAL(mastery.percentAp)
	# 	FROM participant
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	LEFT JOIN participantMastery ON match.id = participantMastery.matchId AND participant.id = participantMastery.participantId
	# 	LEFT JOIN mastery ON match.version = mastery.version AND participantMastery.masteryId = mastery.id AND participantMastery.rank = mastery.rank
	# 	GROUP BY participant.matchId, participant.id''')
	# for (matchId, participantId, totalFlatMasteryAp, totalPercentMasteryAp) in c.fetchall():
	# 	c.execute('''UPDATE participant
	# 		SET totalFlatMasteryAp = ?, totalPercentMasteryAp = ?
	# 		WHERE participant.matchId = ? AND participant.id = ?''',
	# 		(totalFlatMasteryAp, totalPercentMasteryAp, matchId, participantId))
	# # Total AP
	# c.execute('''UPDATE participant
	# 	SET totalAp = (
	# 		SELECT (totalFlatItemAp + totalFlatRuneAp + totalFlatMasteryAp) *
	# 		(1 + (totalPercentItemAp + totalPercentRuneAp + totalPercentMasteryAp) / 100)
	# 		FROM participant AS p
	# 		WHERE participant.matchId = p.matchId AND participant.id = p.id
	# 		)
	# ''')
	# print('Total AP calculated')

	# class getBuildType:
	# 	# 3006: Zerks
	# 	# 3153: BotRK
	# 	# 3072: BT
	# 	# 3035: LW
	# 	# 3031: IE
	# 	# 3046: PD
	# 	adItems = set([3006, 3153, 3072, 3035, 3031, 3046])
	# 	# 3001: Abyssal
	# 	# 3027: RoA
	# 	# 3157: Hourglass
	# 	# 3165: Morello
	# 	# 3089: DCap
	# 	# 3151: Liandry
	# 	# 3116: Rylai
	# 	# 3036: Seraph
	# 	# 3041: Mejai
	# 	apItems = set([3001, 3027, 3157, 3165, 3089, 3151, 3116, 3036, 3041])
	# 	EPSILON = 1
	# 	def __init__(self):
	# 		self.apItemCount = 0
	# 		self.adItemCount = 0
	# 	def step(self, championId, itemId):
	# 		if itemId in self.apItems:
	# 			self.apItemCount += 1
	# 		if itemId in self.adItems:
	# 			self.adItemCount += 1
	# 	def finalize(self):
	# 		if self.apItemCount >= (self.adItemCount + self.EPSILON if self.adItemCount > 0 else 1):
	# 			return 'AP'
	# 		elif self.adItemCount >= (self.apItemCount + self.EPSILON if self.apItemCount > 0 else 1):
	# 			return 'AD'
	# 		return 'Undecided'
	# conn.create_aggregate('getBuildType', 2, getBuildType)
	# c.execute('''SELECT participant.matchId, participant.id, getBuildType(participant.championId, participantItem.itemId)
	# 		FROM participant
	# 		LEFT JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
	# 		GROUP BY participantItem.matchId, participantItem.participantId''')
	# for (matchId, participantId, buildType) in c.fetchall():
	# 	c.execute('''UPDATE participant SET buildType = ?
	# 		WHERE matchId = ? AND id = ?''',
	# 		(buildType, matchId, participantId))
	# print('Build types analyzed')

	# Solo Kills
	# 	c.execute('''UPDATE participant
	# 				SET soloKills = (
	# 					SELECT COUNT() 
	# 						FROM event
	# 							LEFT JOIN
	# 							[match] ON event.matchId = [match].id
	# 							LEFT JOIN
	# 							assist ON assist.matchId = event.matchId AND 
	# 									assist.eventId = event.id
	# 						WHERE type = "CHAMPION_KILL" AND 
	# 							assist.participantId IS NULL AND 
	# 							[match].id = participant.matchId AND 
	# 							event.killerId = participant.id);''')
	# print('Solo kills counted')

	# Champion stats
	# c.execute('''CREATE TABLE championStat (
	# 		version TEXT,
	# 		championId INTEGER,
	# 		picks INTEGER,
	# 		bans INTEGER
	# 		wins INTEGER,
	# 		role TEXT,
	# 		lane TEXT,
	# 		buildType TEXT,
	# 		winRate INTEGER,
	# 		kills INTEGER,
	# 		deaths INTEGER,
	# 		assists INTEGER,
	# 		assassinations INTEGER,
	# 		firstBloodKillOrAssist INTEGER,
	# 		firstTowerKillOrAssist INTEGER,
	# 		totalTimeCrowdControlDealt INTEGER,
	# 		damageDealt INTEGER,
	# 		damageDealtToChampions INTEGER,
	# 		magicDamageDealt INTEGER,
	# 		magicDamageDealtToChampions INTEGER,
	# 		avgTotalAp REAL,
	# 		FOREIGN KEY (version, championId) REFERENCES champion(version, id)
	# 	)''')
	# c.execute('''INSERT INTO championStat (version, championId, winRate, picks, kills, deaths, assists, assassinations, firstBloodKillOrAssist,
	# 	firstTowerKillOrAssist, totalTimeCrowdControlDealt, damageDealt, damageDealtToChampions, magicDamageDealt, magicDamageDealtToChampions, avgTotalAp)
	# 		SELECT match.version, participant.championId, AVG(team.winner), COUNT(*), AVG(participant.kills), AVG(participant.deaths),
	# 		AVG(participant.assists), AVG(participant.assassinations), AVG(participant.firstBloodKill + participant.firstBloodAssist),
	# 		AVG(participant.firstTowerKill + participant.firstTowerAssist), AVG(participant.totalTimeCrowdControlDealt), AVG(participant.damageDealt),
	# 		AVG(participant.damageDealtToChampions), AVG(participant.magicDamageDealt), AVG(participant.magicDamageDealtToChampions),
	# 		AVG(participant.totalAp)
	# 		FROM participant
	# 		LEFT JOIN match ON participant.matchId = match.id
	# 		LEFT JOIN team ON participant.matchId = team.matchId AND participant.teamId = team.id
	# 		GROUP BY match.version, participant.championId''', ())
	# c.execute('''UPDATE championStat
	# 	SET bans = (SELECT COUNT(*)
	# 		FROM ban
	# 		LEFT JOIN match ON ban.matchId = match.id
	# 		WHERE championStat.version = match.version AND championStat.championId = ban.championId
	# 		)''')
	# print('Champion power determined')

	# Player stats
	# c.execute('''CREATE TABLE playerChampion (
	# 	playerId INTEGER NOT NULL REFERENCES player(id),
	# 	championId INTEGER NOT NULL,
	# 	version TEXT,
	# 	picks INTEGER,
	# 	FOREIGN KEY (championId, version) REFERENCES champion(id, version)
	# 	)''')
	# c.execute('''INSERT INTO playerChampion (playerId, championId, version, picks)
	# 	SELECT player.id, participant.championId, match.version, COUNT(*)
	# 	FROM player
	# 	LEFT JOIN participant ON player.id = participant.playerId
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	GROUP BY player.id, participant.championId
	# 	''')
	# c.execute('''CREATE TABLE playerItem (
	# 	playerId INTEGER REFERENCES player(id),
	# 	itemId INTEGER NOT NULL REFERENCES item(id),
	# 	timesBought INTEGER,
	# 	avgTimeBought INTEGER,
	# 	version TEXT
	# 	)''')
	# c.execute('''INSERT INTO playerItem (playerId, itemId, version, timesBought, avgTimeBought)
	# 	SELECT player.id, participantItem.itemId, match.version, COUNT(*), AVG(participantItem.timeBought)
	# 	FROM player
	# 	LEFT JOIN participant ON player.id = participant.playerId
	# 	INNER JOIN participantItem ON participant.matchId = participantItem.matchId AND participant.id = participantItem.participantId
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	GROUP BY player.id, match.version, participantItem.itemId
	# 	''')
	# c.execute('''CREATE TABLE playerStat (
	# 	playerId INTEGER REFERENCES player(id),
	# 	version TEXT,
	# 	gamesPlayed INTEGER,
	# 	apPicks INTEGER,
	# 	adPicks INTEGER)
	# 	''')
	# c.execute('''INSERT INTO playerStat (playerId, version, gamesPlayed)
	# 	SELECT player.id, match.version, COUNT(*)
	# 	FROM player
	# 	LEFT JOIN participant ON player.id = participant.playerId
	# 	LEFT JOIN match ON participant.matchId = match.id
	# 	GROUP BY match.version, player.id
	# 	''')
	# c.execute('''UPDATE playerStat
	# 	SET
	# 		apPicks = (
	# 			SELECT COUNT(*)
	# 			FROM player
	# 			LEFT JOIN participant ON player.id = participant.playerId
	# 			LEFT JOIN match ON participant.matchId = match.id
	# 			WHERE playerStat.playerId = player.id AND playerStat.version = match.version AND participant.buildType = "AP"
	# 		),
	# 		adPicks = (
	# 			SELECT COUNT(*)
	# 			FROM player
	# 			LEFT JOIN participant ON player.id = participant.playerId
	# 			LEFT JOIN match ON participant.matchId = match.id
	# 			WHERE playerStat.playerId = player.id AND playerStat.version = match.version AND participant.buildType = "AD"
	# 		)
	# 	''')
	# print('Player profiling complete')

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