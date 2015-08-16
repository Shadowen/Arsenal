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

matchId = 1852538938
with open('apikey.txt', 'r') as f:
    apiKey = f.read()

r = http.request(
    'GET', 'https://na.api.pvp.net/api/lol/na/v2.2/match/{}?includeTimeline=true&api_key={}'.format(matchId, apiKey))
data = json.loads(r.data.decode('UTF-8'))
matchId = data['matchId']
try:
    c.execute('''INSERT INTO match (id, version, duration, region, queueType) VALUES (?, ?, ?, ?, ?)''',
              (matchId, data['matchVersion'], data['matchDuration'], data['region'], data['queueType']))
    # Assert frameInterval == 60000
    frameInterval = data['timeline']['frameInterval']
    if (frameInterval != 60000):
        print('Frame interval of ' + str(frameInterval) + ' detected!')
    ###
    for team in data['teams']:
        c.execute('''INSERT INTO team (matchId, id, winner) VALUES (?, ?, ?)''', (matchId, team["teamId"], team["winner"]))
        for ban in team['bans']:
            c.execute('''INSERT INTO ban (matchId, teamId, championId, pickTurn) VALUES (?, ?, ?, ?)''',
                (matchId, team['teamId'], ban['championId'], ban['pickTurn']))

    for participant in data['participants']:
        participantId = participant['participantId']
        c.execute('''INSERT INTO participant (matchId, id, teamId, championId, role, lane, kills, deaths, assists) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (matchId, participantId, participant['teamId'], participant['championId'], participant['timeline']['role'], participant['timeline']['lane'], participant['stats']['kills'], participant['stats']['deaths'], participant['stats']['assists']))
        for mastery in participant['masteries']:
            c.execute('''INSERT INTO participantMastery (matchId, participantId, masteryId, rank) VALUES (?, ?, ?, ?)''', (matchId, participantId, mastery['masteryId'], mastery['rank']))
        for rune in participant['runes']:
            c.execute('''INSERT INTO participantRune (matchId, participantId, runeId, rank) VALUES (?, ?, ?, ?)''', (matchId, participantId, rune['runeId'], rune['rank']))
        for item in [participant['stats']['item' + str(i)] for i in range(0, 7)]:
            c.execute('''INSERT INTO participantItem (matchId, itemId) VALUES (?, ?)''', (matchId, item))

    for frame in data['timeline']['frames']:
        timestamp = frame['timestamp']
        for (participantId, participantFrame) in frame['participantFrames'].items():
            print(participantId, '@', timestamp)
            c.execute('''INSERT INTO participantFrame (matchId, timestamp, participantId, positionX, positionY, currentGold, totalGold, level, minionsKilled, jungleMinionsKilled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (matchId, timestamp, participantFrame['participantId'], participantFrame['position']['x'], participantFrame['position']['y'], participantFrame['currentGold'],
                    participantFrame['totalGold'], participantFrame['level'], participantFrame['minionsKilled'], participantFrame['jungleMinionsKilled']))
        for event in frame.get('events', []):
            eventDefault = defaultdict(lambda: 'NULL', event)
            c.execute('''INSERT INTO event (matchId, timestamp, type, itemId, participant, creatorId, killerId, victimId, positionX, positionY) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (matchId, event['timestamp'], event['eventType'], event['itemId'], eventDefault['participantId'], eventDefault['creatorId'],
                    eventDefault['killerId'], eventDefault['victimId'], event.get('position', {'x' : 'NULL'})['x'], event.get('position', {'y' : 'NULL'})['y']))
except sqlite3.Error:
    traceback.print_exc()



# # 3006: Zerks
# # 3153: BotRK
# # 3072: BT
# # 3035: LW
# # 3031: IE
# # 3046: PD
# adItems = set([3006, 3153, 3072, 3035, 3031, 3046])
# # 3001: Abyssal
# # 3027: RoA
# # 3157: Hourglass
# # 3165: Morello
# # 3089: DCap
# # 3151: Liandry
# # 3116: Rylai
# # 3036: Seraph
# # 3041: Mejai
# apItems = set([3001, 3027, 3157, 3165, 3089, 3151, 3116, 3036, 3041])

# items = [participant['stats'][
#     'item' + str(itemNum)] for itemNum in range(0, 7)]
# print('Items: ' + str(items))
# print('Build: ', end='')
# if (any(adItem in items for adItem in adItems)):
#     print('AD')
# elif (any(apItem in items for apItem in apItems)):
#     print('AP')
# else:
#     print('Undecided')
# totalFlatItemAp = 0
# totalPercentItemAp = 0
# for item in items:
#     c.execute('SELECT flat_ap, percent_ap FROM item WHERE id=?', (item,))
#     responseData = c.fetchone()
#     itemAp = responseData[0]
#     itemPercentAp = responseData[1]
#     # Mejai's
#     if item == 3041:
#         stacks = 0
#         maxStacks = 0
#         for frame in sorted(data['timeline']['frames'], key=lambda fr: fr['timestamp']):
#             if 'events' in frame:
#                 for event in sorted(frame['events'], key=lambda ev: ev['timestamp']):
#                     if event['eventType'] == 'ITEM_PURCHASED' and event['participantId'] == participant['participantId'] and event['itemId'] == 3041:
#                         stacks = 6
#                     elif event['eventType'] == 'CHAMPION_KILL':
#                         # Kill
#                         if event['killerId'] == participant['participantId']:
#                             stacks = min(stacks + 2, 20)
#                         # Death
#                         elif event['victimId'] == participant['participantId']:
#                             stacks = math.ceil(stacks / 2)
#                         # Assist
#                         elif participant['participantId'] in event.get('assistingParticipantIds', []):
#                             stacks = min(stacks + 1, 20)
#                     maxStacks = max(maxStacks, stacks)
#         itemAp += stacks * 20
#     # RoA
#     elif item == 3027:
#         stacks = 0
#         for frame in data['timeline']['frames']:
#             if 'events' in frame:
#                 for event in sorted(frame['events'], key=lambda ev: ev['timestamp']):
#                     if event['eventType'] == 'ITEM_PURCHASED' and event['participantId'] == participant['participantId'] and event['itemId'] == 3041:
#                         stacks = (
#                             data['matchDuration'] - event['timestamp'] / 1000) // 60
#         itemAp += stacks * 2
#     # Deathcap
#     elif item == 3089:
#         itemPercentAp = 30
#     totalFlatItemAp += itemAp
#     totalPercentItemAp = max(totalPercentItemAp, itemPercentAp)


# print('Kills: ' + str(participant['stats']['kills']))
# print('Deaths: ' + str(participant['stats']['deaths']))
# print('Assists: ' + str(participant['stats']['assists']))

# print('Damage Dealt: ' + str(participant['stats']['totalDamageDealt']))
# print('Damage Dealt to Champions: ' +
#       str(participant['stats']['totalDamageDealtToChampions']))
# print('Magic Damage Dealt: ' + str(participant['stats']['magicDamageDealt']))
# print('Magic Damage Dealt to Champions: ' +
#       str(participant['stats']['magicDamageDealtToChampions']))

# print('First Blood Kill: ' + str(participant['stats']['firstBloodKill']))
# print('First Blood Assist: ' + str(participant['stats']['firstBloodAssist']))
# print('First Tower Kill: ' + str(participant['stats']['firstTowerKill']))
# print('First Tower Assist: ' + str(participant['stats']['firstTowerAssist']))

# print('CC Given: ' + str(participant['stats']['totalTimeCrowdControlDealt']))


# def runesToRunes(rune):
#     return rune['runeId']
# print('Runes: ' + str(list(map(runesToRunes, participant['runes']))))
# totalFlatRuneAp = 0
# totalPercentRuneAp = 0
# for rune in participant['runes']:
#     c.execute(
#         'SELECT flat_ap, percent_ap FROM rune WHERE id=?', (rune['runeId'],))
#     responseData = c.fetchone()
#     flatRuneAp = responseData[0]
#     totalFlatRuneAp += flatRuneAp
#     percentRuneAp = responseData[1]
#     totalPercentRuneAp += percentRuneAp


# def masteriesToMasteries(mastery):
#     return mastery['masteryId']
# print(
#     'Masteries: ' + str(list(map(masteriesToMasteries, participant['masteries']))))
# totalFlatMasteryAp = 0
# totalPercentMasteryAp = 0
# for mastery in participant['masteries']:
#     c.execute('SELECT flat_ap, percent_ap FROM mastery WHERE id=? AND rank=?',
#               (mastery['masteryId'], mastery['rank']))
#     responseData = c.fetchone()
#     if (responseData is not None):
#         flatMasteryAp = responseData[0]
#         totalFlatMasteryAp += flatMasteryAp
#         percentMasteryAp = responseData[1]
#         totalPercentMasteryAp += percentMasteryAp

# # Total AP
# ap = (totalFlatItemAp + totalFlatRuneAp + totalFlatMasteryAp) * \
#     (100 + totalPercentItemAp +
#      totalPercentRuneAp + totalPercentMasteryAp) / 100
# print('Item AP: ' + str(totalFlatItemAp * (100 + totalPercentItemAp) / 100))
# print('Rune AP: ' + str(totalFlatRuneAp * (100 + totalPercentRuneAp) / 100))
# print('Masteries AP: ' +
#       str(totalFlatMasteryAp * (100 + totalPercentMasteryAp) / 100))
# print('Total AP: ' + str(ap))
print("done!")
conn.close()
