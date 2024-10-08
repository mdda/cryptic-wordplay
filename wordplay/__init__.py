import os, time
import re
import yaml, json

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse  # To extract path information from urls

#import numpy as np  
import random # For random delays


class Problem:
  num, ad, clue, pattern, answer, wordplay, comment, valid=0,'', '', '', '', '', '', True
  def __str__(self):
    return f"#{self.num:2d}{self.ad} : A='{self.answer}' : Q='{self.clue}' ({self.pattern}) :: W='{self.wordplay}' & C='{self.comment}'"
  def from_dict(self, found):
    for k in 'num ad clue answer pattern wordplay comment'.split(' '):
      if k in found:
        setattr(self, k, found[k])
  def as_dict(self):
    d=dict()
    for k in 'num ad clue answer pattern wordplay comment'.split(' '):
      v=getattr(self, k)
      if len(str(v))>0:
        d[k]=v
    return d
  # wordplay : Capital letters get written into the grid/answer
  # wordplay : ()* = anagrammed; (*anagram-signifier)
  # wordplay : ()< = reversed; (<reversal-signifier)
  # wordplay : [] = remove letters; next bracket (removal-signifier)  

from . import custom, generic



def rel_path(p):
  return os.path.join(os.path.dirname(__file__), p)

from omegaconf import OmegaConf
config = OmegaConf.load(rel_path('../sites/config.yaml'))


# https://www.fifteensquared.net/author/teacow/
def get_all_author_index_pages(site, author='teacow', polite_delay_sec=1.0):
  site_base, site_url, site_author = site['site_base'], site['site_url'], site['site_author']
  os.makedirs(rel_path(f"../{site_base}/{author}"), exist_ok=True)
  page=1
  while True:
    page_index = f"{site_base}/{author}/page_index_{page:d}.html"
    fname = rel_path(f"../{page_index}")
    fname_end = fname+'-end'
    if os.path.isfile(fname_end):
      break # No need to keep going - have already found that there are no more
    if os.path.isfile(fname):
      print(f"  Already have : {page_index}")
    else:
      r = requests.get(f"{site_author}/{author}/page/{page:d}")
      if r.status_code==200: # Success
        print(f"  Writing {page_index}")
        with open(fname, 'wt') as f: 
          f.write(r.text)
        time.sleep(polite_delay_sec*(random.uniform(1., 3.))) # Short, variable delay
      else:
        print(f"  Finishing with {page_index}")
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
    # h2 class='entry-title'
    for header in soup.find_all('h2', class_='entry-title'):
      link=header.find('a')
      pages.append(link['href'])
    #if len(pages)==0:
    #  for header in soup.find_all('h2', itemprop='headline'):
    #    link=header.find('a')
    #    pages.append(link['href'])
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
      print(f"  Already have : {page_html}")
    else:
      print(f"  Fetching : {page_html}")
      r = requests.get(url) #  download the file from 'url'
      if r.status_code==200: # Success
        print(f"    Writing: {page_html}")
        with open(fname, 'wt') as f: 
          f.write(r.text)
        time.sleep(polite_delay_sec*(random.uniform(1., 3.))) # Short, variable delay
      else:
        print(f"*Got error code {r.status_code} for {url}*")

def get_content_from(site, fname_stub, author='teacow'):
  page_html = f"{site['site_base']}/{author}/{fname_stub}.html"
  fname = rel_path(f"../{page_html}")
  with open(fname, 'rt') as f: 
    soup = BeautifulSoup(f, features="html.parser")
  return soup
 


def XXXparse_content(content, use_custom=False, use_generic=True):
  problem_arr=[]
  
  if use_custom and len(problem_arr)==0:
    if content.find('div', class_='fts-group'):
      print("  fts-style custom parser")
      problem_arr = custom.clue_fts_style(content)
    else: # Default
      print("  p-style custom parser")
      problem_arr = custom.clue_p_style(content)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using custom parsers")
      
  if use_generic and len(problem_arr)==0:
    print("  generic parser")
    problem_arr = generic.parse_content(content)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using generic parser")
      
  return problem_arr


def fix_ad_for_list(problem_arr):
  # Let's run through the #num for all the problems, and look for the 'restart' of the ordering 
  #   First : Check whether we've got numbers for everything
  drops, drop_last = 0, -1
  for i in range(len(problem_arr)-1):
    if problem_arr[i].num > problem_arr[i+1].num > 0:
      drops+=1
      drop_last=i
  if drops==1: # Expected, good, case
    for i,p in enumerate(problem_arr):
      ad = 'A' if i<=drop_last else 'D'
      if len(p.ad)==0:
        p.ad=ad
      else:
        if ad!=p.ad:
          print(f"Mismatched Across/Down!\n  {p}")
  else:
    print(f"{drops=}, {drop_last=} in ad fixer")
    for i,p in enumerate(problem_arr):
      print(f"index={i:2d} : num={p.num:2d}")
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
has_reference = re.compile(r'[Ss]ee[\s\:]*\d+')  # ~ See:

def invalidate_referential_clues(problem_arr):
  for p in problem_arr:
    if any(c.isdigit() for c in p.clue): p.valid=False  # Clues cannot include references to numbers # brutal
    if has_reference.search(p.clue): p.valid=False      # Clues cannot include references # better, but brittle
  return problem_arr

def remove_answer_from_clue(problem_arr):
  for p in problem_arr:
    answer = p.answer.strip()
    clue = p.clue.strip()
    if clue.upper().startswith(answer.upper()):
      clue = clue[len(answer):]
      clue = re.sub(r'^[\s\-\–]+', '', clue)
    p.clue = clue
  return problem_arr

standard_terms={
  'cryptic definition': 'Cryptic Definition',
  'double definition': 'Double Definition',
  'double (cryptic) definition': 'Double Definition (cryptic)',
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
    answer = p.answer.strip()
    wordplay = p.wordplay.strip()
    if wordplay.upper().startswith(answer.upper()):
      wordplay = wordplay[len(answer):]
      wordplay = re.sub(r'^[\s\-\–]+', '', wordplay)
    p.wordplay = standardise_wordplay(wordplay)
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
      print(f"Missing '{curlies}' in {p}")
      p.valid = False
  return problem_arr

def invalidate_answer_mismatches_pattern(problem_arr):
  for p in problem_arr:
    pattern_len_arr = re.split(r'[^\d]', p.pattern) # List of all lengths (str)
    if False:
      pattern_len = sum([int(pl) for pl in pattern_len_arr if len(pl)>0])
      answer_letters = re.sub(r'[^A-Z]', '', p.answer) # All the upper-case characters in p.answer
      answer_len = len(answer_letters)
      if pattern_len != answer_len:
        print(f"{pattern_len=} {answer_len=} in {p}")
        p.valid=False
    if True:
      pattern_len_arr = [ int(p) for p in pattern_len_arr if len(p)>0 ]
      answer_arr = p.answer.upper().replace('-', ' ').split(' ')
      answer_len_arr = [ len(a) for a in answer_arr ]
      if len(pattern_len_arr) == len(answer_len_arr):
        for i in range(len(pattern_len_arr)):
          if pattern_len_arr[i] != answer_len_arr[i]:
            print(f"{pattern_len_arr=} {answer_len_arr=} in {p}")
            p.valid=False
            break
      else:
        print(f"{pattern_len_arr=} {answer_len_arr=} in {p}")
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

def invalidate_wordplay_too_long(problem_arr, wordplay_len_max=100):
  for p in problem_arr:
    if len(p.wordplay) > wordplay_len_max:
      p.valid = False
  return problem_arr


def discard_invalid_clues(problem_arr):
  return [p for p in problem_arr if p.valid]



def clean_content(problem_arr):
  problem_arr = fix_ad_for_list(problem_arr)
  problem_arr = extract_pattern_from_clue_and_normalise(problem_arr)
  problem_arr = invalidate_missing(problem_arr)
  problem_arr = invalidate_referential_clues(problem_arr)
  
  problem_arr = discard_invalid_clues(problem_arr)

  problem_arr = remove_answer_from_clue(problem_arr)
  problem_arr = standardise_all_wordplay(problem_arr)
  problem_arr = fix_all_definition_brackets(problem_arr)
  
  problem_arr = invalidate_missing_definition(problem_arr)
  problem_arr = invalidate_answer_mismatches_pattern(problem_arr)
  problem_arr = invalidate_answer_mismatches_wordplay_somewhat(problem_arr)
  problem_arr = invalidate_wordplay_too_long(problem_arr)
  
  problem_arr = discard_invalid_clues(problem_arr)
  
  return problem_arr


def create_yaml_from_url(site, url, author='teacow', overwrite=False, force_parse=False, 
                         use_custom=False, use_generic=True):
  fname_stub = url_to_fname_stub(url)
  site_base, site_url = site['site_base'], site['site_url']
  fname_base = f"{site_base}/{author}/{fname_stub}"
  page_html, fyaml = f"{fname_base}.html", f"{fname_base}.yaml"
  fname, fyaml = rel_path(f"../{page_html}"), rel_path(f"../{fyaml}")
  
  data=dict(url=url, fname=page_html, fname_stub=fname_stub, author=author, )
  if not os.path.isfile(fname):
    print(f"  Failed to find file {page_html}")
    return
  if os.path.isfile(fyaml) and not overwrite and not force_parse:
    print(f"  Nothing to do - Found YAML for {page_html}")
    return
  
  print(f"Processing : {fname_base}")
  soup = get_content_from(site, fname_stub, author=author)
  #with open(fname, 'rt') as f: 
  #  soup = BeautifulSoup(f)

  title=soup.find('h1', itemprop='headline')
  if title is None:
    title=soup.find('h1', class_='entry-title')
  if title is not None:
    data['title']=title.text
  
  # TODO: Extract Setter, Publication and is_quick
  #   fname_stub might be like  date_pub_serial_setter
  extract_setter_etc = re.match(r'([\d\_\-]*_)?([a-z\-]+)-(\d+)-([a-z\-]+)', fname_stub)
  if extract_setter_etc:
    data['publication']=extract_setter_etc.group(2)
    data['setter']     =extract_setter_etc.group(4).replace('by-', '')
    data['is_quick']   ='quick' in data['publication'].lower()
  else:
    if 'title' in data:
      data['is_quick'] ='quick' in data['title'].lower()
    
  #content=soup.find('div', class_='entry-content')
  content=soup.select_one(site['css_content'])

  #problem_arr = parse_content(soup, use_custom=use_custom, use_generic=use_generic)
  problem_arr=[]
  if use_custom and len(problem_arr)==0:
    if content.find('div', class_='fts-group'):
      print("  Using fts-style custom parser")
      problem_arr = custom.clue_fts_style(content)
    else: # Default
      print("  Using p-style custom parser")
      problem_arr = custom.clue_p_style(content)
    problem_arr = clean_content(problem_arr)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using custom parsers")
      
  if use_generic and len(problem_arr)==0:
    print("  Using generic parser")
    problem_arr = generic.parse_content(content)
    problem_arr = clean_content(problem_arr)
    if len(problem_arr)==0:
      print("  FAILED TO EXTRACT DATA using generic parser")
  
  if len(problem_arr)>0:
    if not os.path.isfile(fyaml) or overwrite:
      data['clues']=[ p.as_dict() for p in problem_arr ]
      with open(fyaml, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
  else:
    print(f"  Failed to parse {fname}")
    
  return problem_arr


def remove_non_uppers(s):
  return re.sub(r'[^A-Z]', '' , s)

def load_cryptonite_wordlist(split):
  words=set()
  with open(rel_path(f"../prebuilt/cryptonite.{split}.txt"), 'rt') as fin:
    for l in fin.readlines():
      words.add( l.strip() )
  return words
 
def gather_data_for_author(site, author='teacow'):
  cryptonite_test_words=load_cryptonite_wordlist("test")
  cryptonite_val_words =load_cryptonite_wordlist("val")

  site_base = site['site_base']
  author_path = rel_path(f"../{site_base}/{author}")
  author_path_printable =f"{site_base}/{author}"
    
  clues_train, clues_val=[],[]  # These are going to be big...
  for fyaml in sorted(os.listdir(author_path)):
    if not fyaml.endswith('.yaml'): continue
    if fyaml.startswith('author_aggregate'): continue  # Not present any more
    with open(f"{author_path}/{fyaml}", 'r') as infile:
      data_loaded = yaml.safe_load(infile)
    clues_all = data_loaded['clues']
    
    # Add file-wise fields into individual clues
    for clue in clues_all:
      clue['is_quick']   =data_loaded.get('is_quick', None)
      clue['publication']=data_loaded.get('publication', None)
      clue['setter']     =data_loaded.get('setter', None)
      clue['author']     =author  # Attribution FTW!
      
    # Now do the splits - consistent with cryptonite
    clues_nontest = [ clue for clue in clues_all
      if remove_non_uppers(clue['answer']) not in cryptonite_test_words  # Filter out the cryptonite_test set
    ]
    for clue in clues_nontest:
      if remove_non_uppers(clue['answer']) in cryptonite_val_words:  # Now split into train+val
        clues_val.append(clue)
      else:
        clues_train.append(clue)
    print(f"{len(clues_all):3d}=all, {len(clues_nontest):3d}=not_test : {fyaml}")
    
  #def save_aggregate_yaml(clues, stub='train'):
  #  data=dict(clues=clues)
  #  final_yaml = f"{author_path}/author_aggregate_{stub}.yaml"
  #  with open(final_yaml, 'w') as outfile:
  #    yaml.dump(data, outfile, default_flow_style=False)
  #  print(f"Saved {len(clues):4d}={stub: <5s} : {final_yaml}")
    
  def save_aggregate_jsonl(clues, stub='train'):
    aggregate_jsonl = f"author_aggregate_{stub}.jsonl"
    with open(f"{author_path}/{aggregate_jsonl}", 'w') as outfile:
      for clue in clues:
        outfile.write(json.dumps(clue) + "\n")
    #print(f"Saved {len(clues):4d} clues in : {stub:s}")
    print(f"Saved {len(clues):4d} clues in : {author_path_printable}/{aggregate_jsonl}")
    
  save_aggregate_jsonl(clues_train, 'train')
  save_aggregate_jsonl(clues_val, 'val')
