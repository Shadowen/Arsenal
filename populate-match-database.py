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
        c.execute('''INSERT INTO participant (matchId, id, teamId, championId, role, lane, kills, deaths, assists, damageDealt, damageDealtToChampions,
            magicDamageDealt, magicDamageDealtToChampions, firstBloodKill, firstBloodAssist, firstTowerKill, firstTowerAssist, totalTimeCrowdControlDealt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (matchId, participantId, participant['teamId'], participant['championId'], participant['timeline']['role'], participant['timeline']['lane'],
                participant['stats']['kills'], participant['stats']['deaths'], participant['stats']['assists'], participant['stats']['totalDamageDealt'],
            participant['stats']['totalDamageDealtToChampions'], participant['stats']['magicDamageDealt'], participant['stats']['magicDamageDealtToChampions'],
            participant['stats']['firstBloodKill'], participant['stats']['firstBloodAssist'], participant['stats']['firstTowerKill'],
            participant['stats']['firstTowerAssist'], participant['stats']['totalTimeCrowdControlDealt']))
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

print("done!")
conn.close()
