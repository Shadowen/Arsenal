import sqlite3
import traceback

conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
    c.execute('''CREATE TABLE match (
            id INT PRIMARY KEY,
            version TEXT NOT NULL,
            duration TEXT
            )''')
    c.execute('''CREATE TABLE frame (
            matchId INT REFERENCES match(id),
            timestamp INT,
            participantId INT REFERENCES participant(id),
            positionX INT,
            positionY INT,
            currentGold INT,
            totalGold INT,
            level INT,
            minionsKilled INT,
            jungleMinionsKilled INT,
            PRIMARY KEY (matchId, timestamp)
            )''')
    c.execute('''CREATE TABLE event (
            matchId INT REFERENCES match(id),
            timestamp INT NOT NULL,
            id INT PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            item INT REFERENCES item(itemId),
            participant INT,
            creatorId INT,
            killerId INT,
            victimId INT,
            positionX INT,
            positionY INT
            )''')
    c.execute('''CREATE TABLE assist (
            match INT,
            event INT,
            participantId INT,
            FOREIGN KEY (matchId, eventId) REFERENCES event(matchId, id)
            )''')
    c.execute('''CREATE TABLE participant (
	        matchId INT REFERENCES match(id),
	        playerId INT REFERENCES player(id),
	        id INT NOT NULL,
	        team INT REFERENCES team(id),
	        championId INT,
	        champLevel INT,
	        role TEXT,
	        lane TEXT,
	        buildType TEXT,
	        kills INT,
	        deaths INT,
	        assists INT
        )''')
    c.execute('''CREATE TABLE participantMastery (
	    	matchId INT,
	    	participantId INT,
	    	masteryId INT REFERENCES mastery(id),
	    	rank INT,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantRune (
	    	matchId INT,
	    	participantId INT,
	    	runeId INT REFERENCES rune(id),
	    	rank INT,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, id)
    	)''')
    c.execute('''CREATE TABLE participantItem (
	    	matchId INT,
	    	participantId INT,
	    	itemId INT REFERENCES item(id),
	    	timeBought INT,
	    	orderBought INT,
	    	goldThreshold INT,
	    	maxStacks INT,
	    	finalStacks INT,
	    	FOREIGN KEY (matchId, participantId) REFERENCES participant(matchId, participantId))''')
    c.execute('''CREATE TABLE team (
	        match INT REFERENCES match(id),
	        id INT NOT NULL,
	        winner INT NOT NULL
	        )''')

    c.execute('''CREATE TABLE player (
			id INT PRIMARY KEY,
			name TEXT NOT NULL,
			matchHistoryUri TEXT,
			profileIcon INT
	    	)''')
    conn.commit()
except Exception:
    traceback.print_exc()

conn.close()
