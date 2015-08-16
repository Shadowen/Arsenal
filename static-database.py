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
# Items
try:
    c.execute(
        'CREATE TABLE item (id INTEGER PRIMARY KEY, name text, flat_ap INTEGER, percent_ap REAL, gold INTEGER)')
    r = http.request(
        'GET', 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/item?version=5.11.1&itemListData=gold,image,stats&api_key=f84bdaf1-2720-4743-90b6-45576a21a5f5')
    responseData = json.loads(r.data.decode("utf-8"))
    for itemId, item in responseData["data"].items():
        c.execute('INSERT INTO item (id, name, flat_ap, percent_ap, gold) VALUES (?, ?, ?, ?, ?)', (item["id"], item["name"], item[
                  "stats"].get("FlatMagicDamageMod", 0), item["stats"].get("PercentMagicDamageMod", 0), item["gold"]["total"]))
    conn.commit()
    print("Items table created with {} items.".format(
        len(responseData["data"])))
except Exception:
    traceback.print_exc()
# Runes
try:
    c.execute(
        'CREATE TABLE rune (id INTEGER PRIMARY KEY, name text, flat_ap INTEGER, percent_ap REAL)')
    r = http.request(
        'GET', 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/rune?version=5.11.1&runeListData=stats&api_key=f84bdaf1-2720-4743-90b6-45576a21a5f5')
    responseData = json.loads(r.data.decode("utf-8"))
    for runeId, rune in responseData["data"].items():
        c.execute('INSERT INTO rune (id, name, flat_ap, percent_ap) VALUES (?, ?, ?, ?)', (rune["id"], rune[
                  "name"], rune["stats"].get("FlatMagicDamageMod", 0), rune["stats"].get("PercentMagicDamageMod", 0)))
    conn.commit()
    print("Runes table created with {} runes.".format(
        len(responseData["data"])))
except Exception:
    traceback.print_exc()
# Masteries
try:
    c.execute(
        'CREATE TABLE mastery (id INTEGER, name text, rank INTEGER, flat_ap INTEGER, percent_ap REAL)')
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4123, 'Mental Force', 1, 6, 0))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4123, 'Mental Force', 2, 11, 0))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4123, 'Mental Force', 3, 16, 0))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4133, 'Arcane Mastery', 1, 6, 0))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4143, 'Archmage', 1, 0, 2))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4143, 'Archmage', 2, 0, 3.5))
    c.execute('INSERT INTO mastery (id, name, rank, flat_ap, percent_ap) VALUES (?, ?, ?, ?, ?)',
              (4143, 'Archmage', 3, 0, 5))
    conn.commit()
    print("Masteries table created with {} mastery.".format(7))
except Exception:
    traceback.print_exc()
# Finalize
conn.close()
