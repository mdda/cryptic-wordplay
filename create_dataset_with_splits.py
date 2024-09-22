import os, sys, time
import re #, json
import yaml

import wordplay
#print(wordplay.config.keys())
sites_available = [k for k in wordplay.config.keys() if k!='test']

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--author", type=str, required=True, help="Author 'tag' in the site URL for their pages")
parser.add_argument("--site",   type=str, required=True, choices=sites_available, help="One of the available sites")

args = parser.parse_args()  # exits here on parse failure
#print("PARSE SUCCESS") 

# --author teacow --site fifteensquared = Financial Times  (Very nice wordplay)

# --author pipkirby --site timesforthetimes = Times Daily Cryptic - clean wordplay
# --author curarist --site timesforthetimes = Times Quick Cryptic - clean wordplay

# eileen@fifteensquared = Guardian (looks good)

## Not so great for dataset building:
# davemulligangmail-com@timesforthetimes = Times Quick Cryptic (Uses 'strong' in wordplay)
# pipkirby@timesforthetimes = Times Daily Cryptic (But uses colours in the clues, rather than pure wordplay)
# Telegraph is on BigDave44.com ... tend to be wordy, rather than annotations (quick sample)


author, site = args.author, wordplay.config[args.site]

wordplay.get_all_author_index_pages(site, author=author)
