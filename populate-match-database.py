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

with open('apiKey.txt', 'r') as f:
    apiKey =f.read()
files = ['5.11/RANKED_SOLO/NA.json', '5.14/RANKED_SOLO/NA.json']
try:
    for matchSet in files:
        fileName = 'dataset/' + matchSet
        print('Loading match list from ' + str(fileName))
        with open(fileName, 'r') as f:
            matchIds = json.loads(f.read())

        requestNum = 1
        for (matchNum, matchId) in enumerate(matchIds):
            ## TODO
            if matchNum == 50:
                break
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
                        magicDamageDealt, magicDamageDealtToChampions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (matchId, participantId, participant['teamId'], participant['championId'], participant['timeline']['role'], participant['timeline']['lane'],
                            participant['stats']['kills'], participant['stats']['deaths'], participant['stats']['assists'], participant['stats']['totalDamageDealt'],
                        participant['stats']['totalDamageDealtToChampions'], participant['stats']['magicDamageDealt'], participant['stats']['magicDamageDealtToChampions']))
                    for item in [participant['stats']['item' + str(i)] for i in range(0, 7)]:
                        c.execute('''INSERT INTO participantItem (matchId, participantId, itemId) VALUES (?, ?, ?)''', (matchId, participantId, item))
                break
    conn.commit()
except:
    traceback.print_exc()
conn.close()
print("done!")
input()