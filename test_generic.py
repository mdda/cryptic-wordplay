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
  
  if False: # Test custom (vs that already saved as groundtruth in repo)
    problem_arr = wordplay.create_yaml_from_url(site, url, author=author, 
                              overwrite=False, force_parse=True, use_custom=True, use_generic=False)
    
  if True: # Test generic parser (vs that already saved as groundtruth in repo from custom parser)
    problem_arr = wordplay.create_yaml_from_url(site, url, author=author, 
                              overwrite=False, force_parse=True, use_custom=False, use_generic=True)
  
  fname_stub = wordplay.url_to_fname_stub(url)
  site_base, site_url = site['site_base'], site['site_url']
  fname_base = f"{site_base}/{author}/{fname_stub}"

  with open(f"{fname_base}.yaml", 'r') as infile:
    data_loaded = yaml.safe_load(infile)
    problem_arr_custom = []
    for clue in data_loaded['clues']:
      p=wordplay.Problem()
      p.from_dict(clue)
      problem_arr_custom.append(p)
      #print(p)

  for c_custom, c_generic in zip(problem_arr_custom, problem_arr):
    same=True
    c_custom_dict =c_custom.as_dict()
    c_generic_dict=c_generic.as_dict()
    for k in 'ad clue pattern answer wordplay'.split(' '):
      c_custom_nospc =c_custom_dict.get(k, 'MISSING').replace(' ','')
      c_generic_nospc=c_generic_dict.get(k, 'NOTFOUND').replace(' ','')
      if c_custom_nospc != c_generic_nospc:
        same=False
        break
    if not same:
      print(c_custom)
      print(c_generic)
      print()
