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
has_reference = re.compile('[Ss]ee[\s\:]*\d+')  # ~ See:

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

def clue_fts_style(group):
  res = Problem()
  if not group.find('div', class_='fts-subgroup'):
    res.ad = group.text[0].upper()  # Without subgroups => This is the heading for Across/Down
    return res
  try:
    for row, subgroup in enumerate(group.find_all('div', class_='fts-subgroup')):
      # These are like : 
      #   8. More than one retired clergyman housed in close (7)
      #   SEVERAL
      #  (REV)< (clergyman, <retired) in SEAL (close)
      #print(row, subgroup)
      if row==0:
        # This is several things separated in <span>, some with underline
        arr=[]
        for span in subgroup.find_all('span'):
          txt = span.text
          if 'underline' in span['style']:
            txt = f"{{{txt}}}"
          arr.append(txt)
        #print(arr)
        res.num = int(arr[0].replace('.','').strip())
        res.clue = ''.join(arr[1:]).strip() # includes pattern
      if row==1:
        # This the answer
        res.answer=subgroup.text
      if row==2:
        # This contains the wordplay in <p>
        #print(subgroup.text)
        wordplay=subgroup.text.strip()
        arr = wordplay.split('\n')
        res.wordplay = arr[0].strip()
        res.comment=''
        if len(arr)>1:
          res.comment=' '.join(arr[1:]).replace('\n', ' - ')  # The comments here should mostly be same line
  except Exception as e:
    res.valid=False
  return res

def clue_p_style(group):
  res = Problem()
  if group.find('strong'):
    ad_maybe = group.text[0].upper()  # Without subgroups => This is the heading for Across/Down
    if ad_maybe in 'AD':
      res.ad = ad_maybe
    return res
  try:
    rows = [[],]
    for element in group.children:
      #print("element:", element)
      if element.name is None or element.name.lower()!='br':
        rows[-1].append(element)
      else:
        rows.append([])
    # Now we have all the rows
    #print("rows:", rows)
    if len(rows)>0:
      arr=rows[0]
      # arr[] has several things separated in <span>, some with underline
      try:
        res.num = int(arr[0].replace('.','').strip())
      except Exception as e:
        res.valid=False
      for i in range(1, len(arr)):
        txt = arr[i].text
        if 'underline' in arr[i]['style']:
          txt = f"{{{txt}}}"
        arr[i]=txt
      if len(arr)>0:
        res.clue = ''.join(arr[1:]).strip() # includes pattern
        
    if len(rows)>1:
      res.answer=' '.join([a.text for a in rows[1]]).strip()
    
    if len(rows)>2:
      arr = [a for row in rows[2:] for a in row]
      # This contains the wordplay in <p>
      #print(subgroup.text)
      res.wordplay = arr[0].text.strip()
      res.comment=''
      if len(arr)>1:
        res.comment=' '.join(arr[1:]).replace('\n', ' - ')  # The comments here should mostly be same line
  except Exception as e:
    res.valid=False
  return res
