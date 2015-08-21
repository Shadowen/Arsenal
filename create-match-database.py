import sqlite3
import traceback

conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
    c.execute('''CREATE TABLE match (
			id INTEGER PRIMARY KEY,
			region TEXT,
			queueType TEXT,
			version TEXT NOT NULL,
			duration INTEGER
			)''')
    c.execute('''CREATE TABLE team (
		    matchId INTEGER REFERENCES match(id),
		    id INTEGER,
		    winner INTEGER NOT NULL,
		    PRIMARY KEY (matchId, id)
		    )''')
    c.execute('''CREATE TABLE ban (
			matchId INTEGER REFERENCES match(id),
			teamId INTEGER,
			championId INTEGER REFERENCES champion(id),
			pickTurn INTEGER,
			PRIMARY KEY (matchId, pickTurn),
			FOREIGN KEY (matchId, teamId) REFERENCES team(matchId, id)
			)''')
    c.execute('''CREATE TABLE participant (
	        matchId INTEGER REFERENCES match(id),
	        playerId INTEGER REFERENCES player(id),
	        id INTEGER NOT NULL,
	        teamId INTEGER REFERENCES team(id),
	        championId INTEGER REFERENCES champion(id),
	        champLevel INTEGER,
	        role TEXT,
	        lane TEXT,
	        buildType TEXT,
	        kills INTEGER,
	        deaths INTEGER,
	        assists INTEGER,
	        soloKills INTEGER,
	        assassinations INTEGER,
	        firstBloodKill INTEGER,
	        firstBloodAssist INTEGER,
	        firstTowerKill INTEGER,
	        firstTowerAssist INTEGER,
	        totalTimeCrowdControlDealt INTEGER,
	        damageDealt INTEGER,
	        damageDealtToChampions INTEGER,
	        physicalDamageDealt INTEGER,
	        physicalDamageDealtToChampions INTEGER,
	        magicDamageDealt INTEGER,
	        magicDamageDealtToChampions INTEGER,
	        trueDamageDealt INTEGER,
	        trueDamageDealtToChampions INTEGER,
			totalFlatItemAp INT,
			totalPercentItemAp REAL,
			totalFlatRuneAp REAL,
			totalPercentRuneAp REAL,
			totalFlatMasteryAp REAL,
			totalPercentMasteryAp REAL,
			totalAp REAL,
			PRIMARY KEY (matchId, id)
	        )''')
    c.execute('''CREATE TABLE participantItem (
    		matchId INTEGER,
    		participantId INTEGER,
    		itemId INTEGER,
    		timeBought INTEGER,
    		finalStacks INTEGER,
    		maxStacks INTEGER,
    		stackAp INTEGER,
    		goldThreshold INTEGER,
    		FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id),
    		FOREIGN KEY (matchId, timeBought) REFERENCES event(matchId, timestamp)
	    	)''')
    c.execute('''CREATE TABLE participantMastery (
	    	matchId INTEGER,
	    	participantId INTEGER,
	    	masteryId INTEGER REFERENCES mastery(id),
	    	rank INTEGER,
	    	PRIMARY KEY (matchId, participantId, masteryId),
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantRune (
	    	matchId INTEGER REFERENCES match(id),
	    	participantId INTEGER,
	    	runeId INTEGER REFERENCES rune(id),
	    	rank INTEGER,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantFrame (
            matchId INTEGER REFERENCES match(id),
            timestamp INTEGER,
            participantId INTEGER REFERENCES participant(id),
            positionX INTEGER,
            positionY INTEGER,
            currentGold INTEGER,
            totalGold INTEGER,
            level INTEGER,
            minionsKilled INTEGER,
            jungleMinionsKilled INTEGER,
            PRIMARY KEY (matchId, timestamp, participantId)
            )''')
    c.execute('''CREATE TABLE event (
            matchId INTEGER REFERENCES match(id),
            frameTimestamp INTEGER,
            timestamp INTEGER NOT NULL,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            itemId INTEGER REFERENCES item(itemId),
            itemBefore INTEGER,
            itemAfter INTEGER,
            participantId INTEGER,
            creatorId INTEGER,
            killerId INTEGER,
            victimId INTEGER,
            positionX INTEGER,
            positionY INTEGER,
            FOREIGN KEY (matchId, frameTimestamp) REFERENCES participantFrame(matchId, frameTimestamp)
            )''')
    c.execute('''CREATE TABLE assist (
            matchId INTEGER REFERENCES match(id),
            eventId INTEGER,
            participantId INTEGER REFERENCES participant(id),
            FOREIGN KEY (matchId, eventId) REFERENCES event(matchId, id)
            )''')

    c.execute('''CREATE TABLE player (
			id INTEGER PRIMARY KEY,
			name TEXT NOT NULL,
			matchHistoryUri TEXT,
			profileIcon INTEGER
	    	)''')
    conn.commit()
except sqlite3.Error:
    traceback.print_exc()

conn.close()
print('Done!')
input()