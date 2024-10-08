import re
from bs4 import BeautifulSoup, Comment, NavigableString
from wordplay import Problem

"""
# FTS-style
groups = content.select('div.fts-group')
print(len(groups))

items = groups[10].select('div.fts-subgroup')
for item in items:
  print(item)
  print("***")

from collections import defaultdict
# Let's look to see whether we can find the repetitive elements in the groups...
tag_counts=defaultdict(int)

for i,tag in enumerate(content):
  tag_counts[tag.name] += 1
  #if True: # i==5:
    #print(tag)
  #  print(dir(tag))
    #print(tag.name)
  #  break
tag_counts  
# fts-style defaultdict(int, {None: 8, 'p': 6, 'div': 1}) -- this kind misses the important stuff
# p-style   defaultdict(int, {None: 39, 'p': 37, 'div': 1})


"""

def clue_fts_style(content):
  problem_arr, ad = [], ''
  for group in content.find_all('div', class_='fts-group'):
    res = Problem()
    res.ad=ad
    if not group.find('div', class_='fts-subgroup'):
      ad = group.text[0].upper()  # Without subgroups => This is the heading for Across/Down
      continue
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
    problem_arr.append(res)   
  return problem_arr

def clue_p_style(content):
  problem_arr, ad = [], ''
  for group in content.find_all('p'):
    res = Problem()
    res.ad=ad
    if group.find('strong'):
      ad_maybe = group.text[0].upper()  # Without subgroups => This is the heading for Across/Down
      if ad_maybe in 'AD':
        ad = ad_maybe
      continue
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
    problem_arr.append(res)
  return problem_arr
