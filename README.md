# Arsenal ([live](http://shadowen.github.io/Arsenal/))
A force-directed graph to help visualize the difference in item win rates and co-occurrences from patch 5.11 to 5.14. 

[Runner-up](https://developer.riotgames.com/discussion/announcements/show/xE4xpdJ6) for [Riot Games API Challenge 2.0](https://developer.riotgames.com/discussion/announcements/show/2lxEyIcE) - AP Item Analysis.

![image](https://cloud.githubusercontent.com/assets/8551479/10398678/611590ea-6e7c-11e5-8829-8fd0fe2e06c3.png)

The graph has two basic rules:

- **Nodes** represent items. The size corresponds to the rate at which players who bought the item won the game.
- **Edges** represent the frequency with which the items were seen in the same player's inventory. The thicker and shorter the edge, the higher the frequency. 

These two simple rules, plus a few fundamental forces (gravity and charge) used to keep the diagram on screen, combine to form an incredible interactive visualization. Users may pluck at nodes or focus on parts of the graph to explore in depth. 

# Implementation 
The data used to power the graph was pulled from the patch 5.11 and 5.14 [match lists provided](https://github.com/Shadowen/Arsenal/tree/master/dataset). A Python script stored all the match data in a local SQLite database, then a mixture of Python and SQL was used to process the data. Finally, the output was exported to JSON format and loaded onto the website.

The website is written in Jekyll for GitHub Pages, entirely in JavaScript powered by [D3.js](d3js.org) and [jQuery](http://jquery.com/). The [force-directed graph layout](https://github.com/mbostock/d3/wiki/Force-Layout) of D3 was heavily customized for the purposes of this application. [MasterMaps d3-slider](https://github.com/MasterMaps/d3-slider) was used to generate the slider bars at the top of the application.

# Build Process
The main principle behind the design of this project is that it should be buildable by anyone from scratch with just the contents of the repository. For this reason, the entire database can be built at any time by simply running the scripts in order. No additional setup required. All configuration files are included in the repository. The website can likewise be built quickly and easily with a local Jekyll server configured identically to GitHub Pages.

## Clone the Repo
*Prerequisites:* Have [git](https://git-scm.com/) installed and obtain a [Riot API key](developer.riotgames.com).

1. Clone with `git clone https://github.com/Shadowen/Arsenal.git`
2. Paste your Riot API key inside `apikey.txt`.
3. Run `git update-index --assume-unchanged -- apikey.txt` so you don't accidentally commit your API key.

## Database Build Process
*Prerequisites:* Have Python 3.x installed. [`certifi`](https://pypi.python.org/pypi/certifi) is recommended for SSL certificates.

1. Run `clean.py` to delete any previous database.
2. Run `static-database.py` to pull static data into the database.
3. Run `create-match-database.py` to initialize the database schema.
4. Run `populate-match-database.py` to actually make the requests to the Riot API. Make sure the delay between requests is adjusted to account for your [rate limit](https://developer.riotgames.com/docs/rate-limiting).
5. Run `process-match-data.py` to add value to data. This may take a while.
  - `clean-processing.py` can revert this step if necessary.
6. Run `export.py` to export data to JSON files.

## Website Build Process
*Prerequisites:* Set up [Jekyll for GitHub Pages](https://help.github.com/articles/using-jekyll-with-pages/).

1. Clone the website with `git clone https://github.com/Shadowen/Arsenal.git`
2. Checkout the website with `git checkout gh-pages`
3. Run `bundle exec jekyll serve` to build the website.

# How it works
This application is a two-step process. First the data is crunched on a local machine with Python and SQL, then the data is uploaded to GitHub Pages, where a user can view the site. The actual visualization is generated by client side JavaScript.

## The Database
We begin in our `master` branch with the scripts `static-database.py` and `create-match-database.py`. They create the structure or *schema* of the database the data will be stored in. Together, they issue `CREATE TABLE` queries through Python 3's `sqlite` library to a database on disk. The final structure of the database is shown below.

![database_diagram](https://cloud.githubusercontent.com/assets/8551479/9565717/3768c70e-4eaf-11e5-9d4b-69d4d440f697.jpg)

`static-database.py` and `populate-match-database.py` import Python 3's `urllib3` to make `GET` requests to [Riot's API](https://developer.riotgames.com/api/methods). To ensure the security of the API key, the API key is stored in an external file `apiKey.txt`. This file is then "*[hijacked](http://stackoverflow.com/a/19011529/5195629)*" (`git update-index --assume-unchanged`) from the repository when it is cloned, so it will never be committed. A developer can then insert the API key to be used into this file and it will never leave the local machine.

A delay is added as necessary to ensure that the API requests obey the rate limit. If a `429 Rate Limit Exceeded` error code is received, the script will automatically wait the time specified in the `Retry-After` header. The script will also retry requests as necessary if any fail due to `404 Not Found` or `503 Service Unavailable` errors.

`process-match-data.py` then does the majority of the work. It crawls through the events timeline for each game, tracking item buys, sells, and undos. It also accounts for item transformations such as *Devourer* -> *Sated Devourer*, or *Manamune* -> *Muramana* (Seriously Riot, you could've documented those events a bit better). To each item, the script attaches additional data such as the time of buy, the player's gold at the time, and even the number of stacks on items including *Mejai's Soulstealer* and *Rod of Ages*.

The process can take a few seconds per game, since data has to be referenced across the player, event timeline, and static item tables. Initially, this process was even slower, but a combination of correctly indexing the tables and moving some more ~~complicated~~ awkward calculations from SQL to Python helped speed it up by as much as 100 times.

In this stage, we also coalaese some items together. Following precedent, we choose to count all enchantments as the same as the base item. That means both boot and jungle item enchantments. Transformation items such as *Seraph's Embrace* are also counted as their base item, *Archangel's Staff* in this case. List below:

Counted As | Item
---|---
Sightstone (2049) | Ruby Sightstone (2045)
Archangel's Staff (3003) | Seraph's Embrace (3040)
Manamune (3004) | Muramana (3043)
Boots of Swiftness (3009) | Various enchantments
Mobility Boots (3117) | Various enchantments
Boots of Lucidity (3158) | Various enchantments
Mercury Treads (3111)  | Various enchantments
Berserker's Greaves (3006) | Various enchantments
Ninja Tabi (3047) | Various enchantments
Sorcerer's Shoes (3020) | Various enchantments
Stalker's Blade (3706) | Various enchantments*
Poacher's Knife (3711) | Various enchantments*
Skirmisher's Saber (3715) | Various enchantments*
Ranger's Trailblazer (3713) | Various enchantments*
Warding Totem (3340) | Upgraded warding trinket (3361), Pink ward trinket (3362)
Sweeping Lens (3341) | Oracle's Lens (3364)
Scrying Orb (3363) | Farsight Orb (3342)

*Sated Devourer is counted as Devourer, which is counted as one of the various jungle items.

Finally, we are ready for `export.py`. All this script does is pull data that is already in the database our, filter it for only completed items, and export to a JSON format that the website can understand. This is saved into a file called `itemCross.json`.

## The Website
Now we switch over to our `gh-pages` branch. We left off with a JSON file containing all of our useful information called `itemCross.json`. This file is then uploaded to the website's `data/` folder where - you guessed it - the data resides.

Then the site is assembled by GitHub Page's Jekyll. This creates the static site accessible at [shadowen.github.io/Arsenal/](shadowen.github.io/Arsenal/). The entire application is contained in `index.html`'s single script tag. All DOM elements are created via JavaScript.

When a user views the website, the JavaScript embedded in the website executes. It gets the JSON file `data/itemCross.json`, loads all the data, and populates the graph nodes at the default settings. The graph draws in SVG (Scalable Vector Graphics) for optimal performance across a large variety of screen sizes. The data is [joined](http://bost.ocks.org/mike/join/) to the DOM in D3, allowing it to be [fully animated](http://bost.ocks.org/mike/transition/) as it changes.

The `d3-sliders` library is used to generate the sliders at the top of the page. These are linked to the graph and update it whenever their values change. Mouseover styling and tooltips are implemented in CSS where possible and jQuery where impossible.

# Next Steps
For this visualization, we make use of only the final items in the inventory of the player at the end of the game. However, since we have been able to extract data about the state of the player's inventory at any point in the game, we are looking to find new ways to apply this information in future applications.
