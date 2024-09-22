import os, sys, time
#import re #, json
import yaml

import wordplay
#print(wordplay.config.test)
site = wordplay.config['test']
author='author'

test_cases = [
  dict( # fts-style 
    url='https://example.com/2024_05_06_financial-times-17727-by-bobcat', 
  ), 
  dict( # p-style        
    url='https://example.com/2018_05_28_financial-times-15869-by-crux', 
  ), 
]

for case in test_cases:  # [1:2]
  url = case['url']
  
  if False: # Test saved (vs that already saved as groundtruth in repo)
    problem_arr = wordplay.create_yaml_from_url(site, url, author=author, 
                              overwrite=False, force_parse=True, use_custom=True, use_generic=False)
    
  if True: # Test parser parser (vs that already saved as groundtruth in repo from saved parser)
    problem_arr = wordplay.create_yaml_from_url(site, url, author=author, 
                              overwrite=False, force_parse=True, use_custom=False, use_generic=True)
  
  fname_stub = wordplay.url_to_fname_stub(url)
  site_base, site_url = site['site_base'], site['site_url']
  fname_base = f"{site_base}/{author}/{fname_stub}"

  with open(f"{fname_base}.yaml", 'r') as infile:
    data_loaded = yaml.safe_load(infile)
    problem_arr_saved = []
    for clue in data_loaded['clues']:
      p=wordplay.Problem()
      p.from_dict(clue)
      problem_arr_saved.append(p)
      #print(p)

  differences_reported=False
  for c_save in problem_arr_saved:  # Look through all the known-good examples
    found=False
    for c_parse in problem_arr: # Check against all newly found problems
      if c_save.num!=c_parse.num or c_save.ad!=c_parse.ad:
        continue
      found=True
      same=True
      c_save_dict =c_save.as_dict()
      c_parse_dict=c_parse.as_dict()
      for k in 'clue pattern answer wordplay'.split(' '):
        c_save_nospc =c_save_dict.get(k, 'MISSING').replace(' ','')
        c_parse_nospc=c_parse_dict.get(k, 'NOTFOUND').replace(' ','')
        if c_save_nospc != c_parse_nospc:
          same=False
          break
      if not same:
        print("\nMis-match between saved, and the following:")
        print(c_saved)
        print(c_parser)
        differences_reported=True
      c_parse.num=-1 # Make sure this not printed again
    if not found:
      print("\nThe following saved problem did not match any found problem:")
      print(c_save)
      differences_reported=True

  for c_parse in problem_arr: # Print out non-matched newly found problems
    if c_parse.num>=0:
      print("\nThe following matched no saved problem:")
      print(c_parse)
      print()
      differences_reported=True

  if not differences_reported:
    print("* No problems detected * ")
    print()
    
  continue
  # Should do something more sophisticated than this to match the 'num' fields
  #   .. so that missing a clue out doesn't invalidate rest of clues vs gold data on disk
  for c_saved, c_parser in zip(problem_arr_saved, problem_arr):
    same=True
    c_saved_dict =c_saved.as_dict()
    c_parser_dict=c_parser.as_dict()
    for k in 'ad clue pattern answer wordplay'.split(' '):
      c_saved_nospc =c_saved_dict.get(k, 'MISSING').replace(' ','')
      c_parser_nospc=c_parser_dict.get(k, 'NOTFOUND').replace(' ','')
      if c_saved_nospc != c_parser_nospc:
        same=False
        break
    if not same:
      print(c_saved)
      print(c_parser)
      print()
