# Clone the Repo
1. Clone with `git clone`
2. Paste your Riot API key inside `apikey.txt`.
3. Run `git update-index --assume-unchanged -- apikey.txt` so you don't accidentally commit your API key.

# Database Build Process
1. Run `clean.py` to delete any previous database.
2. Run `static-database.py` to pull static data into the database.
3. Run `create-match-database.py` to initialize the database schema.
4. Run `populate-match-database.py` to actually make the requests to the Riot API.
5. Run `process-match-data.py` to add value to data.
6. Run `export.py` to export data to JSON files.

# Website Build Process
1. Run `jekyll serve` to build the website.