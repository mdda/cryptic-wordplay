import os, sys, time
import re #, json
import yaml

import argparse

import wordplay
from wordplay import Problem
import wordplay.generic

#print(wordplay.config.keys())
sites_available = [k for k in wordplay.config.keys() if k!='test']

parser = argparse.ArgumentParser()
parser.add_argument("--author", type=str, required=True, help="Author 'tag' in the site URL for their pages")
parser.add_argument("--site",   type=str, required=True, choices=sites_available, help="One of the available sites")
parser.add_argument("--pages",  type=int, default=3, help="Number of pages to download (-1 for 'ALL')")

args = parser.parse_args()  # exits here on parse failure
#print("PARSE SUCCESS") 

# --author teacow --site fifteensquared = Financial Times  (Very nice wordplay)

# --author pipkirby --site timesforthetimes = Times Daily Cryptic - clean wordplay
# --author chris-woods --site timesforthetimes = Times Quick Cryptic - clean wordplay ... But still a lot of non-parses

## --author jackkt --site timesforthetimes = Times Quick Cryptic - clean wordplay (some color changes)
## --author kitty --site timesforthetimes = Times Quick Cryptic - clean wordplay (but difficult to parse)
## --author curarist --site timesforthetimes = Times Quick Cryptic - cleanish wordplay (some color changes)
## --author rolytoly --site timesforthetimes = Times Quick Cryptic - cleanish wordplay (some long explanations)


# eileen@fifteensquared = Guardian (looks good)

## Not so great for dataset building:
# davemulligangmail-com@timesforthetimes = Times Quick Cryptic (Uses 'strong' in wordplay)
# pipkirby@timesforthetimes = Times Daily Cryptic (But uses colours in the clues, rather than pure wordplay)
# Telegraph is on BigDave44.com ... tend to be wordy, rather than annotations (quick sample)


author, site = args.author, wordplay.config[args.site]
page_limit = args.pages

print("Downloading the author's index pages")
wordplay.get_all_author_index_pages(site, author=author)

print("Extracting the individual page URLs")
url_arr=wordplay.extract_individual_page_urls_for_author(site, author=author)
print(f"  Found {len(url_arr)} individual page URLs")

if page_limit>0:
  print(f"Downloading {page_limit} individual HTML pages")
  url_arr = url_arr[:page_limit]
else:
  print(f"Downloading ALL listed individual HTML pages")
wordplay.ensure_pages_downloaded(url_arr, site, author=author)

print(f"Processing {len(url_arr)} HTML pages")
for url in url_arr:
  #fname_stub = wordplay.url_to_fname_stub(url)
  #print(f"  Processing Page '{fname_stub}'")
  #soup = wordplay.get_content_from(site, fname_stub, author=author)
  #content=soup.select_one(site['css_content'])
  #
  #clue_starts=wordplay.generic.get_most_important_node_arr(content, debug=True)
  #print(f"    Found {len(clue_starts)} potential clue-starts")
  #
  #problem_list = wordplay.generic.build_problem_arr(clue_starts, content.next_sibling, debug=True)
  #print(f"    Found {len(problem_list)} Clues ... testing validity")

  wordplay.create_yaml_from_url(site, url, author=author, use_custom=False)

print("Gathering pages into author jsonl files (with splits)")
wordplay.gather_data_for_author(site, author=author)


gather_dataset="""
for split in train val; do
  find sites | grep author_aggregate_${split}.jsonl | sort > list.${split}
done
# Edit the files to select for the authors/sites required
dt=`date --iso-8601=minutes`
for split in train val; do
  { xargs cat < list.${split} ; } | uniq > ${dt}_wordplay.${split}.jsonl
done
"""
# python create_dataset_with_splits.py  --author teacow --site fifteensquared --pages -1
# python create_dataset_with_splits.py  --author pipkirby --site timesforthetimes --pages -1
# ? python create_dataset_with_splits.py  --author curarist --site timesforthetimes --pages -1
