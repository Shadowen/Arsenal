# Arsenal
A force-directed graph to help visualize the difference in item win rates and co-occurrences from patch 5.11 to 5.14. 

The graph has two basic rules:

- Items are nodes whose size corresponds to the rate at which players who bought the item won the game.
- Edges represent the frequency with which the items were seen in the same player's inventory. The thicker and shorter the edge, the higher the frequency. 

These two simple rules, plus a few fundamental forces (gravity and charge) used to keep the diagram on screen, combine to form an incredible interactive visualization. Users may pluck at nodes or focus on parts of the graph to explore in depth. 

# Implementation 
The data used to power the graph was pulled from the patch 5.11 and 5.14 [match lists provided](https://github.com/Shadowen/Arsenal/tree/master/dataset). A Python script stored all the match data in a local SQLite database, then a mixture of Python and SQL was used to process the data. Finally, the output was exported to JSON format and loaded onto the website.
The website is written in Jekyll for GitHub Pages, entirely in JavaScript powered by [D3.js](d3js.org) and [jQuery](http://jquery.com/). The [force-directed graph layout](https://github.com/mbostock/d3/wiki/Force-Layout) of D3 was heavily customized for the purposes of this application. [MasterMaps d3-slider](https://github.com/MasterMaps/d3-slider) was used to generate the slider bars at the top of the application.

# Build Process
## Clone the Repo
1. Clone with `git clone`
2. Paste your Riot API key inside `apikey.txt`.
3. Run `git update-index --assume-unchanged -- apikey.txt` so you don't accidentally commit your API key.

## Database Build Process
1. Run `clean.py` to delete any previous database.
2. Run `static-database.py` to pull static data into the database.
3. Run `create-match-database.py` to initialize the database schema.
4. Run `populate-match-database.py` to actually make the requests to the Riot API.
5. Run `process-match-data.py` to add value to data.
6. Run `export.py` to export data to JSON files.

## Website Build Process
1. Set up [Jekyll for GitHub Pages](https://help.github.com/articles/using-jekyll-with-pages/).
1. Run `bundle exec jekyll serve` to build the website.


