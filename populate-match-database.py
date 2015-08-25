import urllib3
import certifi

import json

import sqlite3

import traceback
import math
import time

from collections import defaultdict
# Init
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',  # Force certificate check.
    ca_certs=certifi.where(),  # Path to the Certifi bundle.
)
conn = sqlite3.connect('database.db')
c = conn.cursor()

with open('apikey.txt', 'r') as f:
    apiKey = f.read()

# 1852538938 # Contains DCap
# 1852559476 # Contains RoA
# 1852563520 # Contains Mejais
files = ['5.11/RANKED_SOLO/NA.json', '5.14/RANKED_SOLO/NA.json']
for matchSet in files:
    fileName = 'dataset/' + matchSet
    print('Loading match list from ' + str(fileName))
    with open(fileName, 'r') as f:
        matchIds = json.loads(f.read())

    requestNum = 1
    for (matchNum, matchId) in enumerate(matchIds):
        ## TODO
        if matchNum == 3:
            break
        try:
            while True:
                time.sleep(1)
                print("Loading match {}({})".format(matchId, requestNum))
                requestNum += 1
                r = http.request(
                    'GET', 'https://na.api.pvp.net/api/lol/na/v2.2/match/{}?includeTimeline=true&api_key={}'.format(matchId, apiKey))
                if r.status != 200:
                    print('HTTP Request failed: ' + str(r.status))
                    if (r.status == 429):
                        header = r.getheader('Retry-After')
                        waitTime = header if header is not None else 2
                        print('Waiting {} seconds...'.format(waitTime))
                        time.sleep(float(waitTime) + 1)
                    elif (r.status == 403):
                        print('Uh oh! Blacklisted.')
                        time.sleep(10000)
                    print('Retrying...')
                    continue
                data = json.loads(r.data.decode('UTF-8'))
                matchId = data['matchId']

                c.execute('''INSERT INTO match (id, version, duration, region, queueType) VALUES (?, ?, ?, ?, ?)''',
                          (matchId, data['matchVersion'][:4], data['matchDuration'], data['region'], data['queueType']))
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
                # Participants
                for participant in data['participants']:
                    participantId = participant['participantId']
                    c.execute('''INSERT INTO participant (matchId, id, teamId, championId, champLevel, role, lane, kills, deaths, assists, damageDealt, damageDealtToChampions,
                        physicalDamageDealt, physicalDamageDealtToChampions, magicDamageDealt, magicDamageDealtToChampions, trueDamageDealt, trueDamageDealtToChampions, firstBloodKill,
                        firstBloodAssist, firstTowerKill, firstTowerAssist, totalTimeCrowdControlDealt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (matchId, participantId, participant['teamId'], participant['championId'], participant['stats']['champLevel'], participant['timeline']['role'], participant['timeline']['lane'],
                            participant['stats']['kills'], participant['stats']['deaths'], participant['stats']['assists'], participant['stats']['totalDamageDealt'],
                        participant['stats']['totalDamageDealtToChampions'], participant['stats']['physicalDamageDealt'], participant['stats']['physicalDamageDealtToChampions'],
                        participant['stats']['magicDamageDealt'], participant['stats']['magicDamageDealtToChampions'], participant['stats']['trueDamageDealt'], participant['stats']['trueDamageDealtToChampions'],
                        participant['stats']['firstBloodKill'], participant['stats']['firstBloodAssist'], participant['stats']['firstTowerKill'], participant['stats']['firstTowerAssist'],
                        participant['stats']['totalTimeCrowdControlDealt']))
                    for mastery in participant.get('masteries', []):
                        c.execute('''INSERT INTO participantMastery (matchId, participantId, masteryId, rank) VALUES (?, ?, ?, ?)''',
                            (matchId, participantId, mastery['masteryId'], mastery['rank']))
                    for rune in participant.get('runes', []):
                        c.execute('''INSERT INTO participantRune (matchId, participantId, runeId, rank) VALUES (?, ?, ?, ?)''',
                            (matchId, participantId, rune['runeId'], rune['rank']))
                # Players
                for player in data['participantIdentities']:
                    participantId = player['participantId']
                    summonerId = player['player']["summonerId"]
                    c.execute('''UPDATE participant SET playerId = ?
                        WHERE matchId = ? AND id = ?''', (summonerId, matchId, participantId))
                    # Add the player if we don't have him/her yet
                    c.execute('''SELECT *
                        FROM player
                        WHERE id = ?''', (summonerId,))
                    if c.fetchone() is None:
                        c.execute('''INSERT INTO player (id, name, matchHistoryUri, profileIcon) VALUES (?, ?, ?, ?)''',
                            (summonerId, player['player']['summonerName'], player['player']['matchHistoryUri'], player['player']['profileIcon']))

                for frame in data['timeline']['frames']:
                    for (participantId, participantFrame) in frame['participantFrames'].items():
                        position = participantFrame.get('position', {'x': None, 'y': None});
                        c.execute('''INSERT INTO participantFrame (matchId, timestamp, participantId, positionX, positionY, currentGold, totalGold, level,
                            minionsKilled, jungleMinionsKilled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (matchId, frame['timestamp'], participantFrame['participantId'], position['x'], position['y'], participantFrame['currentGold'],
                                participantFrame['totalGold'], participantFrame['level'], participantFrame['minionsKilled'], participantFrame['jungleMinionsKilled']))
                    for event in frame.get('events', []):
                        eventDefault = defaultdict(lambda: None, event)
                        itemId = eventDefault['itemId']
                        if itemId == None:
                            itemId = eventDefault['itemBefore']
                        if itemId == None or itemId == 0:
                            itemId = eventDefault['itemAfter']
                        c.execute('''INSERT INTO event (matchId, frameTimestamp, timestamp, type, itemId, participantId, creatorId, killerId, victimId,
                            positionX, positionY) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (matchId, frame['timestamp'], event['timestamp'], event['eventType'], itemId, eventDefault['participantId'], eventDefault['creatorId'], eventDefault['killerId'],
                            eventDefault['victimId'], event.get('position', {'x' : None})['x'], event.get('position', {'y' : None})['y']))
                        for assist in event.get('assistingParticipantIds', []):
                            c.execute('''INSERT INTO assist (matchId, eventId, participantId)
                                VALUES (?, ?, ?)''', (matchId, c.lastrowid, participantId))
                conn.commit()
                break
        except sqlite3.Error:
            traceback.print_exc()
        except:
            traceback.print_exc()
conn.close()
print('Done!')    
input()