import urllib3
import certifi
import json
import sqlite3
import traceback
# Init
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where(),
)
conn = sqlite3.connect('database.db')
c = conn.cursor()

with open('apikey.txt', 'r') as f:
    apiKey = f.read()

# Champions
try:
    c.execute('''CREATE TABLE champion (
        version TEXT,
        id INTEGER,
        name TEXT,
        title TEXT,
        PRIMARY KEY (version, id))
        ''')
except:
    traceback.print_exc()
try:
    # Items
    c.execute(
    '''CREATE TABLE item (
        version TEXT,
        id INTEGER,
        name TEXT,
        flatAp INTEGER,
        percentAp REAL,
        gold INTEGER,
        PRIMARY KEY (version, id)
        )''')
except:
    traceback.print_exc()
try:
    # Runes
    c.execute(
    '''CREATE TABLE rune (
        id INTEGER,
        name TEXT,
        version TEXT,
        flatAp INTEGER,
        percentAp REAL,
        PRIMARY KEY (version, id)
        )''')
except:
    traceback.print_exc()
try:
    # Masteries
    c.execute(
        '''CREATE TABLE mastery (
            id INTEGER,
            name TEXT,
            version TEXT,
            rank INTEGER,
            flatAp INTEGER,
            percentAp REAL,
            PRIMARY KEY (version, id, rank)
            )''')
except:
    traceback.print_exc()

def populateStaticTables(version):
    print('Version ' + version + ' static tables')
    # Champions
    try: 
        r = http.request(
            'GET', 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/champion?version={}&api_key={}'.format(version, apiKey))
        if r.status != 200:
            print('HTTP request failed:' + str(r.status))
            raise Exception
        responseData = json.loads(r.data.decode("utf-8"))
        for championKey, champion in responseData["data"].items():
            c.execute('''INSERT INTO champion (version, id, name, title) VALUES (?, ?, ?, ?)''',
                (version[:4], champion['id'], champion['name'], champion['title']))
        print("Champions table created with {} champions.".format(
            len(responseData["data"])))
    except Exception:
        traceback.print_exc()
    # Items
    try: 
        r = http.request(
            'GET', 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/item?version={}&itemListData=gold,image,stats&api_key={}'.format(version, apiKey))
        if r.status != 200:
            print('HTTP request failed:' + str(r.status))
            raise Exception
        responseData = json.loads(r.data.decode("utf-8"))
        for itemId, item in responseData["data"].items():
            c.execute('''INSERT INTO item (id, name, version, flatAp, percentAp, gold) VALUES (?, ?, ?, ?, ?, ?)''',
                (item["id"], item["name"], version[:4], item["stats"].get("FlatMagicDamageMod", 0),
                    item["stats"].get("PercentMagicDamageMod", 0), item["gold"]["total"]))
        # Deathcap pls
        c.execute('''UPDATE item SET percentAp = 30 WHERE id = 3089''')
        print("Items table created with {} items.".format(
            len(responseData["data"])))
    except Exception:
        traceback.print_exc()
    # Runes
    try:
        r = http.request(
            'GET', 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/rune?version={}&runeListData=stats&api_key={}'.format(version, apiKey))
        if r.status != 200:
            print('HTTP request failed:' + str(r.status))
            raise Exception
        responseData = json.loads(r.data.decode("utf-8"))
        for runeId, rune in responseData["data"].items():
            c.execute('INSERT INTO rune (id, name, version, flatAp, percentAp) VALUES (?, ?, ?, ?, ?)', (rune["id"], rune[
                      "name"], version[:4], rune["stats"].get("FlatMagicDamageMod", 0), rune["stats"].get("PercentMagicDamageMod", 0)))
        print("Runes table created with {} runes.".format(len(responseData["data"])))
    except Exception:
        traceback.print_exc()
    # Masteries
    try:
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4123, 'Mental Force', version[:4], 1, 6, 0))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4123, 'Mental Force', version[:4], 2, 11, 0))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4123, 'Mental Force', version[:4], 3, 16, 0))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4133, 'Arcane Mastery', version[:4], 1, 6, 0))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4143, 'Archmage', version[:4], 1, 0, 2))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4143, 'Archmage', version[:4], 2, 0, 3.5))
        c.execute('INSERT INTO mastery (id, name, version, rank, flatAp, percentAp) VALUES (?, ?, ?, ?, ?, ?)',
                  (4143, 'Archmage', version[:4], 3, 0, 5))
        print("Masteries table created with {} masteries.".format(7))
    except Exception:
        traceback.print_exc()

populateStaticTables('5.11.1')
populateStaticTables('5.14.1')
conn.commit()
# Finalize
conn.close()
print('Done!')
input()
