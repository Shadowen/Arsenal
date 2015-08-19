# Clone the Repo
1. Clone with `git clone`
2. Paste your Riot API key inside `apikey.txt`.

# Database Build Process
1. Run `clean.py` to delete any previous database.
2. Run `static-database.py` to pull static data into the database.
3. Run `create-match-database.py` to initialize the database schema.
4. Run `populate-match-database.py` to actually make the requests to the Riot API.
5. Run `process-match-data.py` to add value to data.