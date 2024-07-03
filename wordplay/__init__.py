import os, time
import re
#, json
#import yaml

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse  # To extract path information from urls

#import numpy as np  
import random # For random delays



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


# Process different page styles...
has_reference = re.compile('[Ss]ee[\s\:]*\d+')

class Problem:
  num, ad, clue, pattern, answer, wordplay, comment, valid=0,'', '', '', '', '', '', True
  def __str__(self):
    return f"{self.num:2d}{self.ad} : {self.answer} : '{self.clue}' ({self.pattern}) :: {self.wordplay} & '{self.comment}'"

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

"""
soup = wordplay.get_content_from(site, fname_stub, author='teacow')
soup

content=soup.find('div', class_='entry-content')
content 

groups =content.find_all('div', class_='fts-group')
groups

items = groups[10].find_all('div', class_='fts-subgroup')
items
"""
