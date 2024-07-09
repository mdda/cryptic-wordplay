import re
from bs4 import BeautifulSoup, Comment, NavigableString
from wordplay import Problem

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

is_answer   = re.compile(r'^[\"\']?[\-\sA-Z\'\’]+[\"\']?$')
has_pattern = re.compile(r'(\([\d\-\,]+\))')
has_lower   = re.compile(r'[a-z]')
has_upper   = re.compile(r'[A-Z]')
remove_nums = re.compile(r'^([\d\.]+\s*)?(.+?)(\s*\([\d\-\,]+\))?$')

def add_num_to_found(found, txt):
  arr = txt.strip().replace('.','').split(' ')
  try:
    found['num'] = int(arr[0])
  except:
    pass

def add_text_snippets_to_found(found, txt, allow_clue=False, debug=False):
  if debug: print(f'Looking for things in "{txt}" {allow_clue=}')
  add_num_to_found(found, txt)
  # This could be CLUE_PART, PATTERN, ANSWER, WORDPLAY, COMMENT/EXTRA or nothing
  if is_answer.match(txt.strip()): # Likely ANSWER, on its own, at start, whole thing
    if debug: print(f"Setting found['answer']={txt}")
    found['answer'] = txt
  else:
    pattern_match = has_pattern.search(txt)
    if pattern_match:
      if debug: print(f"Setting found['pattern']={pattern_match.group(1)}")
      found['pattern'] = pattern_match.group(1)
    txt_no_nums = re.sub(remove_nums, r'\2', txt)
    score_clue, score_wordplay = 0,0
    if has_lower.search(txt_no_nums) and has_upper.search(txt_no_nums):
      score_clue=10
      #score_wordplay=10
    if pattern_match:
      score_clue+=10
    if '{' in txt_no_nums:
      score_clue+=10
    if '}' in txt_no_nums:
      score_clue+=10
    if '<' in txt_no_nums or '*' in txt_no_nums or '"' in txt_no_nums or '”' in txt_no_nums or '+' in txt_no_nums:
      score_wordplay+=20
    if '(' in txt_no_nums and ')' in txt_no_nums :
      score_wordplay+=10
    if '[' in txt_no_nums and ']' in txt_no_nums :
      score_wordplay+=20
    parens = re.sub(r'[^\(\)]', '', txt) # only parens from original txt
    if len(parens)>2:
      score_wordplay+=(len(parens)-2)*5
    tl=txt.lower()
    if tl.startswith('cryptic definition') or tl.startswith('double definition') or tl.startswith('&lit;') or txt.startswith('DD'):
      score_wordplay+=20

    if not allow_clue: 
      score_clue=-10

    # True or 
    if debug: print(f"Calculated : {score_clue=}, {score_wordplay=} for '{txt}'")
    if score_clue>score_wordplay:
      if len(found.get('clue', ''))==0:
        if debug: print(f"Setting found['clue']={txt_no_nums}")
        found['clue']=txt_no_nums
    elif score_wordplay>0:
      if len(found.get('wordplay',''))==0:
        if debug: print(f"Setting found['wordplay']={txt}")
        #txt_wordplay = standardise_wordplay(txt)
        found['wordplay']=txt
      else:
        #txt_wordplay = standardise_wordplay(txt)
        if txt != found['wordplay']:
          print(f"Setting found['comment']={txt}")
          found['comment']=(found.get('comment','')+' '+txt).strip()

def add_spans_to_found(found, span_arr, debug=False):
  if debug: print("Looking in spans", span_arr)
  str_arr=[]
  for span in span_arr:
    if isinstance(span, str):
      str_arr.append( span )
      continue
    if isinstance(span, NavigableString):
      str_arr.append( span.text )
      continue
    #print(f"{span.get('style', '')=}")
    if 'underline' in span.get('style', ''):
      str_arr.append( '{' + span.text.strip() + '}' )
    else:
      str_arr.append( span.text.strip() )
  spans_combined = ' '.join([s for s in str_arr]).strip()
  add_text_snippets_to_found(found, spans_combined, allow_clue=True, debug=debug)

def match_in_component(component, debug=False):
  found, span_arr = dict(), []
  if component is None or isinstance(component, (str, )):
    return found 
  for e in component:
    gather_spans=False
    if isinstance(e, (Comment,)):
      pass
    #elif isinstance(e, (str,)):
    #  if len(e.strip())>0:
    #    add_text_snippets_to_found(found, e.strip(), allow_clue=True, debug=debug)
    #    span_arr.append(e)
    elif isinstance(e, NavigableString): # Pure text
      if len(e.string.strip())>0:
        add_text_snippets_to_found(found, e.string.strip(), allow_clue=True, debug=debug)
        span_arr.append(e)
    #elif e.name=='p' and len(e.text)>0: # This is stand-alone
    #  add_text_to_found(found, e.text)
    elif (e.name=='span' or e.name=='u') and len(e.text)>0:  # These can be joined together... ?
      add_text_snippets_to_found(found, e.text, debug=debug)
      if e.name=='u': e.style='underline'  # Fix-up      
      span_arr.append(e)
    elif e.name=='br': # This is a splitter...
      if debug: print("Splitting at <br>")
      gather_spans=True

    if gather_spans and len(span_arr)>0:
      add_spans_to_found(found, span_arr, debug=debug)
      span_arr=[]
  if len(span_arr)>0:
    add_spans_to_found(found, span_arr, debug=debug)
  return found

def get_most_important_node_arr(content):
  node_list_by_found=dict()
  for component in content.descendants:
    if len(str(component).strip())==0: continue
    found = match_in_component(component)
    #print(str(component)[:100])
    #print("***", found)
    if len(found)>0:
      content_pattern = '|'.join(sorted(list(found.keys())))
      if content_pattern not in node_list_by_found:
        node_list_by_found[content_pattern]=[]
      node_list_by_found[content_pattern].append(component)

  #most_useful_found = dict()
  max_score, max_arr = -1, []
  for k,arr in node_list_by_found.items():
    score=0
    if 'clue' in k: 
      score+=10
      if 'num' in k: score +=2
      if 'pattern' in k: score +=2
      if 'answer' in k: score +=5
      if 'wordplay' in k: score +=5
    score*=len(arr)
    #most_useful_found[k]=score
    #print(f"{len(arr)}: {score=} :: {k}")
    if score>max_score:
      max_score=score
      max_arr=arr
  return max_arr

def build_problem_list(clue_starts, content_next):
  problem_arr=[]
  for i,c in enumerate(clue_starts):
    # Determine when to give up on this clue..
    clue_ends = content_next # After the list (only when i is at end of clue_starts list)
    if i+1<len(clue_starts):
      clue_ends = clue_starts[i+1]
    found = dict()
    
    while c is not None:
      found_new = match_in_component(c)
      if len(found_new)>0:
        #print(found_new)
        for k,v in found_new.items():
          if k not in found:
            found[k]=v
        missing=False
        for k in 'clue pattern answer wordplay'.split(' '):
          if k not in found:
            missing=True
        if not missing:
          #print("FILLED IN REQUIRED ENTRIES")
          problem = Problem()
          problem.from_dict(found) # Fill out the structure
          #print(f"Saving : {problem}")
          problem_arr.append(problem)
          found=dict()
          break
        c = c.next_sibling  # Don't go inside, if we found something
      else:
        c = c.next_element  # Try next element
      if c==clue_ends:
        break
    #print("--- Try next element ---")
  return problem_arr
