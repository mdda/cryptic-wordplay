import os, time
import re
#, json
#import yaml

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse  # To extract path information from urls

#import numpy as np  
import random # For random delays

#import wordplay.custom, wordplay.generic

def rel_path(p):
  return os.path.join(os.path.dirname(__file__), p)

from omegaconf import OmegaConf
config = OmegaConf.load(rel_path('../sites/config.yaml'))


# https://www.fifteensquared.net/author/teacow/
def get_all_author_index_pages(site, p='author', author='teacow', polite_delay_sec=1.0):
  site_base, site_url = site['site_base'], site['site_url']
  os.makedirs(rel_path(f"../{site_base}/{author}"), exist_ok=True)
  page=1
  while True:
    page_index = f"{site_base}/{author}/page_index_{page:d}.html"
    fname = rel_path(f"../{page_index}")
    fname_end = fname+'-end'
    if os.path.isfile(fname_end):
      break # No need to keep going - have already found that there are no more
    if os.path.isfile(fname):
      print(f"Already have : {page_index}")
    else:
      r = requests.get(f"{site_url}/{p}/{author}/page/{page:d}")
      if r.status_code==200: # Success
        print(f"Writing {fname}")
        with open(fname, 'wt') as f: 
          f.write(r.text)
        time.sleep(polite_delay_sec*(random.uniform(1., 3.))) # Short, variable delay
      else:
        print(f"Finishing with {fname_end}")
        with open(fname_end, 'wt') as f: 
          f.write(f"Finished with a {r.status_code}\n")
        break
    page+=1
#get_all_author(site, author='teacow')

def extract_individual_page_urls_for_author(site, author='teacow'):
  site_base, site_url = site['site_base'], site['site_url']
  pages, page = [], 1
  while True:
    page_index = f"{site_base}/{author}/page_index_{page:d}.html"
    fname = rel_path(f"../{page_index}")
    fname_end = fname+'-end'
    if os.path.isfile(fname_end):
      break # No need to keep going - have already found that there are no more
    with open(fname, 'rt') as f: 
      soup = BeautifulSoup(f, features="html.parser")
    # Off to the races!
    # h2 itemprop="headline"
    for header in soup.find_all('h2', itemprop='headline'):
      #print(header)
      link=header.find('a')
      #print(link)
      pages.append(link['href'])
    page+=1
    #break
  return pages
#arr=extract_individual_page_urls_for_author(author='teacow')
#len(arr)


def url_to_fname_stub(url):
  page = urlparse(url)
  page_path = page.path
  if page_path.startswith('/'): page_path=page_path[1:]
  if page_path.endswith('/'): page_path=page_path[:-1]
  page_path = page_path.replace('/', '_')
  return page_path
  
def ensure_pages_downloaded(arr, site, author='teacow', polite_delay_sec=1.0):
  site_base, site_url = site['site_base'], site['site_url']
  for url in arr:
    #print(url)
    fname_stub = url_to_fname_stub(url)
    page_html = f"{site_base}/{author}/{fname_stub}.html"
    fname = rel_path(f"../{page_html}")
    
    if os.path.isfile(fname):
      print(f"  Found {page_html}")
    else:
      #print(f"  Missing {page_html}"); continue
      r = requests.get(url) #  download the file from 'url'
      if r.status_code==200: # Success
        print(f"  Writing {page_html}")
        with open(fname, 'wt') as f: 
          f.write(r.text)
        time.sleep(polite_delay_sec*(random.uniform(1., 3.))) # Short, variable delay
      else:
        print(f"Got code {r.status_code} for {url}")

class Problem:
  num, ad, clue, pattern, answer, wordplay, comment, valid=0,'', '', '', '', '', '', True
  def __str__(self):
    return f"{self.num:2d}{self.ad} : {self.answer} : '{self.clue}' ({self.pattern}) :: {self.wordplay} & '{self.comment}'"
  def from_dict(self, found):
    for k in 'num clue answer pattern wordplay comment'.split(' '):
      if k in found:
        setattr(self, k, found[k])
  # wordplay : Capital letters get written into the grid/answer
  # wordplay : ()* = anagrammed; (*anagram-signifier)
  # wordplay : ()< = reversed; (<reversal-signifier)
  # wordplay : [] = remove letters; next bracket (removal-signifier)  


def get_content_from(site, fname_stub, author='teacow'):
  page_html = f"{site['site_base']}/{author}/{fname_stub}.html"
  fname = rel_path(f"../{page_html}")
  with open(fname, 'rt') as f: 
    soup = BeautifulSoup(f, features="html.parser")
  return soup



def parse_content(soup, use_custom=False, use_generic=True):
  problem_arr=[]
  content=soup.find('div', class_='entry-content')
  
  if use_custom:
    if soup.find('div', class_='fts-group'):
      print("  fts-style custom parser")
      problem_arr = wordplay.custom.clue_fts_style(content)
    else: # Default
      print("  p-style custom parser")
      problem_arr = wordplay.custom.clue_p_style(content)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using custom parsers")
      
  if use_generic:
    print("  generic parser")
    problem_arr = wordplay.generic.ETC(content)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using generic parser")
      
  return problem_arr


def fix_ad_for_list(problem_arr):
  # Let's run through the #num for all the problems, and look for the 'restart' of the ordering 
  #   First : Check whether we've got numbers for everything
  drops, drop_last = 0, -1
  for i in range(len(problem_arr)-1):
    if problem_arr[i].num > problem_arr[i+1].num:
      drops+=1
      drop_last=i
  #print(f"{drops=}, {drop_last=}")
  if drops==1: # Expected, good, case
    for i,p in enumerate(problem_arr):
      ad = 'A' if i<=drop_last else 'D'
      if len(p.ad)==0:
        p.ad=ad
      else:
        if ad!=p.ad:
          print(f"Mismatched Across/Down!\n  {p}")
  return problem_arr

def extract_pattern_from_clue_and_normalise(problem_arr):
  for p in problem_arr:
    if len(p.clue)>0:
      if len(p.pattern)==0:  # Get the pattern out of the clue
        clue = p.clue
        bracket_index=clue.rfind('(')
        if bracket_index<0: 
          print(f"No pattern found in '{clue}'")
          p.valid=False  # Must be able to find a pattern
        else:
          p.clue    = clue[:bracket_index].strip()
          p.pattern = clue[bracket_index+1:]
    p.pattern = p.pattern.replace('(','').replace(')','').strip()
  return problem_arr

def invalidate_missing(problem_arr):
  required='ad clue pattern answer wordplay'.split(' ')
  for p in problem_arr:
    missing=False
    for k in required:
      if len(getattr(p, k, ''))==0: 
        print(f"{k} missing from {p}")
        missing=True
    p.valid = not missing
  return problem_arr

# Process different page styles...
has_reference = re.compile('[Ss]ee[\s\:]*\d+')  # ~ See:

def invalidate_referential_clues(problem_arr):
  for p in problem_arr:
    if any(c.isdigit() for c in p.clue): p.valid=False  # Clues cannot include references to numbers # brutal
    if has_reference.search(p.clue): p.valid=False      # Clues cannot include references # better, but brittle
  return problem_arr

standard_terms={
  'cryptic definition': 'Cryptic Definition',
  'double definition': 'Double Definition',
  'dd': 'Double Definition',
  '&lit;': '&lit;',
}

def standardise_wordplay(txt):
  tl=txt.lower()
  for term, standardised in standard_terms.items():
    if tl.startswith(term):
      txt = standardised + txt[len(term):]
      break
  return txt

def standardise_all_wordplay(problem_arr):
  for p in problem_arr:
    p.wordplay = standardise_wordplay(p.wordplay)
  return problem_arr

def fix_all_definition_brackets(problem_arr):
  for p in problem_arr:
    if p.wordplay.startswith('Double Definition'):  # This has been standardised
      p.clue = p.clue.replace('}{', '} {')  # Maybe a space got filled in
    else:
      p.clue = p.clue.replace('{}', '').replace('}{', '') # Maybe over-bracketed
  return problem_arr

def invalidate_missing_definition(problem_arr):
  for p in problem_arr:
    curlies='{}'
    if p.wordplay.startswith("Double Definition"): # Need two sets of {}
      curlies='{}{}'
    clue_only_curlies = re.sub(r'[^\{\}]', '', p.clue)
    if not clue_only_curlies.startswith(curlies):
      print("Missing '{}' in {p}")
      p.valid = False
  return problem_arr

def invalidate_answer_mismatches_pattern(problem_arr):
  for p in problem_arr:
    pattern_len_arr = re.split(r'[^\d]', p.pattern) # List of all lengths (str)
    pattern_len = sum([int(pl) for pl in pattern_len_arr if len(pl)>0])
    answer_letters = re.sub(r'[^A-Z]', '', p.answer) # All the upper-case characters in p.answer
    answer_len = len(answer_letters)
    if pattern_len != answer_len:
      print(f"{pattern_len=} {answer_len=} in {p}")
      p.valid=False
  return problem_arr

def invalidate_answer_mismatches_wordplay_somewhat(problem_arr):
  for p in problem_arr:
    if p.wordplay.startswith('Double Definition') or p.wordplay.startswith('Cryptic Definition'):  # These have been standardised    
      continue # Cannot check
    wordplay_output = re.sub(r'[^A-Z]', '', p.wordplay) # Extract the uppercase letters in p.wordplay
    answer_letters  = re.sub(r'[^A-Z]', '', p.answer)   # All the upper-case characters in p.answer    
    # Criteria : Do at least 75% of the letters match?
    cnt=0
    for wl in wordplay_output:
      if wl in answer_letters:  # Super-simple check
        cnt+=1
    if cnt<len(answer_letters)*.75:
      print(f"Found {cnt} wordplay letters of {len(answer_letters)} in {p}")
      p.valid=False
  return problem_arr


def discard_invalid_clues(problem_arr):
  return [p for p in problem_arr if p.valid]

