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
			duration TEXT
			)''')
    c.execute('''CREATE TABLE team (
		    matchId INTEGER REFERENCES match(id),
		    id INTEGER,
		    winner INTEGER NOT NULL,
		    PRIMARY KEY (matchId, id)
		    )''')
    c.execute('''CREATE TABLE ban (
			matchId INTEGER,
			teamId INTEGER,
			championId INTEGER,
			pickTurn INTEGER,
			FOREIGN KEY (matchId, teamId) REFERENCES team(matchId, id)
			)''')
    c.execute('''CREATE TABLE participant (
	        matchId INTEGER REFERENCES match(id),
	        playerId INTEGER REFERENCES player(id),
	        id INTEGER NOT NULL,
	        teamId INTEGER REFERENCES team(id),
	        championId INTEGER,
	        champLevel INTEGER,
	        role TEXT,
	        lane TEXT,
	        buildType TEXT,
	        kills INTEGER,
	        deaths INTEGER,
	        assists INTEGER,
	        assassinations INTEGER
        )''')
    c.execute('''CREATE TABLE participantMastery (
	    	matchId INTEGER,
	    	participantId INTEGER,
	    	masteryId INTEGER REFERENCES mastery(id),
	    	rank INTEGER,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantRune (
	    	matchId INTEGER,
	    	participantId INTEGER,
	    	runeId INTEGER REFERENCES rune(id),
	    	rank INTEGER,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantItem (
	    	matchId INTEGER,
	    	participantId INTEGER,
	    	itemId INTEGER REFERENCES item(id),
	    	timeBought INTEGER,
	    	orderBought INTEGER,
	    	goldThreshold INTEGER,
	    	maxStacks INTEGER,
	    	finalStacks INTEGER,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, participantId))''')
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
            PRIMARY KEY (matchId, timestamp)
            )''')
    c.execute('''CREATE TABLE event (
            matchId INTEGER REFERENCES match(id),
            timestamp INTEGER NOT NULL,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            itemId INTEGER REFERENCES item(itemId),
            participantId INTEGER,
            creatorId INTEGER,
            killerId INTEGER,
            victimId INTEGER,
            positionX INTEGER,
            positionY INTEGER
            )''')
    c.execute('''CREATE TABLE assist (
            matchId INTEGER,
            eventId INTEGER,
            participantId INTEGER,
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
