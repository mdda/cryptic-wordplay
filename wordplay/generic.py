import re
from bs4 import BeautifulSoup, Comment, NavigableString
from . import Problem

"""
soup = wordplay.get_content_from(site, fname_stub, author='teacow')
soup

content=soup.find('div', class_='entry-content')
content 

groups =content.find_all('div', class_='fts-group')
groups

items = groups[10].find_all('div', class_='fts-subgroup')
items

tag_sequences = defaultdict(list)

def traverse_and_record(element, current_sequence=None):
  "Recursively traverses the HTML tree and records tag sequences."
  #print("ENTERED")
  if current_sequence is None:
    current_sequence = []

  if isinstance(element, NavigableString):
    # Handle text content here.
    # For example, print it or append it to a list.
    #print("Text:", element.strip())
    if element.strip():
      current_sequence.append('TXT')
      tag_sequences[">".join(current_sequence)].append(
        element.string.strip()
      )
  #  pass
  elif element.name and not isinstance(element, (Comment)): # , BeautifulSoup
    # Only consider tags with direct text content
    current_sequence.append(element.name)
    if element.string and element.string.strip():
      tag_sequences[">".join(current_sequence)].append(
        #element.string.strip() if element.string and element.string.strip() else ''
        element.string.strip()
      )
    
  if hasattr(element, 'children'):
    for child in element.children:
      traverse_and_record(child, current_sequence.copy())

if False:
  #traverse_and_record(content.parent())
  traverse_and_record(soup.find('div', class_='entry-content'))
  #traverse_and_record(soup)
  
  # Filter for potentially repetitive patterns (appearing more than once)
  repetitive_patterns = {
    selector: examples
    for selector, examples in tag_sequences.items()
    if len(examples) > 1
  }
  
  for selector, examples in repetitive_patterns.items():
    print(f"CSS Selector: {selector}")
    print(f"Example Text: {len(examples)=} {examples}")
    print("-" * 20)

# Take an element, and go through its parts:
#   TXT != ''
#   BR
#   P
#   SPAN
# and see what matches we have - return a dict with the matches for:
  #   NUM, CLUE_PART, PATTERN, ANSWER, WORDPLAY, COMMENT/EXTRAx
"""

is_answer   = re.compile(r'^[\"\']?[\-\sA-Z\'\’]+[\"\']?$')
has_pattern = re.compile(r'(\([\d\-\,]+\))')
has_lower   = re.compile(r'[a-z]')
has_upper   = re.compile(r'[A-Z]')
not_upper   = re.compile(r'[^A-Z]+')
remove_nums = re.compile(r'^([\d\.]+\s*)?(.+?)(\s*\([\d\-\,]+\))?$')

#wordplay.generic.is_answer.match("A-SD")
#wordplay.generic.has_pattern.search("  (2,5)") # Better than match
#wordplay.generic.is_answer.match("KING’S RANSOM")


#def add_num_to_found(found, txt):

def add_text_snippets_to_found(found, txt, allow_clue=False, debug=False):
  if debug: print(f'Looking for things in "{txt}" {allow_clue=}')
  #add_num_to_found(found, txt)
  
  arr = txt.strip().replace('.','').split(' ')
  try:
    found['num'] = int(arr[0])
    if arr[0]==''.join(arr) and found['num']>0:
      return # we set the num, and that was all that there was...
  except:
    pass
  
  # This could be CLUE_PART, PATTERN, ANSWER, WORDPLAY, COMMENT/EXTRA or nothing
  if is_answer.match(txt.strip()): # Likely ANSWER, on its own, at start, whole thing
    if debug: print(f"Setting found['answer']={txt}")
    found['answer'] = txt
  else:
    pattern_match = has_pattern.search(txt)
    if pattern_match:
      if debug: print(f"Setting found['pattern']={pattern_match.group(1)}")
      found['pattern'] = pattern_match.group(1)
      if found['pattern']==txt.strip():
        return  # If pattern matched whole txt - all done!
    txt_no_nums = re.sub(remove_nums, r'\2', txt)
    
    score_clue, score_wordplay = 0,0
    if has_lower.search(txt_no_nums) and has_upper.search(txt_no_nums):
      score_clue+=10
      #score_wordplay+=10
    txt_upper_only = re.sub(not_upper, ' ', txt_no_nums) # So spans of upper case are kept together, with spaces in between
    txt_upper_only_group_counts = [ max(len(up)-1,0) for up in txt_upper_only.split(' ') ]
    # True or 
    if debug: print(f"{txt_upper_only=} {txt_upper_only_group_counts=}")
    if sum(txt_upper_only_group_counts)>1:  # i.e. more than 1 group of multiple upper letters
      score_wordplay+=20  
      
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
    else:
      for term in 'cryptic double definition'.split(' '):
        if term in tl:
          score_wordplay+=10

    if not allow_clue: 
      score_clue=-10

    #debug=True
    # True or 
    if debug: print(f"Calculated : {score_clue=}, {score_wordplay=} for '{txt}'")
    if score_clue>score_wordplay:
      clue_prev = found.get('clue', '')
      #if len(clue_prev)<len(txt_no_nums) and clue_prev in txt_no_nums:  # Accept if the clue that has been found is longer, and is within the new version
      if len(clue_prev)==0 or clue_prev in txt_no_nums:  # Accept if no clue has been found or previous one is within the new version
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
  return  # 'found' probably modified in-place

                       
def XXXadd_spans_to_found(found, span_arr, debug=False):
  if debug: print("Looking in spans", span_arr)
  str_arr=[]
  for span in span_arr:
    if isinstance(span, str):
      str_arr.append( span )
      continue
    if isinstance(span, NavigableString):
      str_arr.append( span.text )
      continue
    # TODO: EXPAND TO THE CASE WHERE A SPAN HAS AN INTERNAL SPAN...
    #         See: teacow/2021_06_07_financial-times-16805-by-hamilton.html
    #print(f"{span.get('style', '')=} {span.get('class', '')=}")  # a str and a list[str]
    if 'underline' in span.get('style', '') or 'definition' in ' '.join(span.get('class', '')):
      str_arr.append( '{' + span.text.strip() + '}' )
    else:
      str_arr.append( span.text.strip() )
  spans_combined = ' '.join([s for s in str_arr]).strip()
  add_text_snippets_to_found(found, spans_combined, allow_clue=True, debug=debug)

def XXXmatch_in_component(component, debug=False):
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



def add_linear_to_found(found, linear, debug=False):
  if debug: print("Looking in linear", linear)
  str_arr=[]
  for d in linear:
    if d.get('is_underlined', False):
      str_arr.append( '{' + d['txt'].strip() + '}' )
    else:
      str_arr.append( d['txt'].strip() )
  str_combined = ' '.join([s for s in str_arr]).strip()
  add_text_snippets_to_found(found, str_combined, allow_clue=True, debug=debug)


def match_in_component_recursive(component, debug=False):
  found = dict()
  if component is None or isinstance(component, (str, )):
    return found 
  # Read the internals, add to linear array of dicts with 'txt', and 'underline' as required
  def make_linear(component, found, is_underlined=False, debug=debug):
    linear = []
    for e in component:
      gather_segment=False
      base = dict(is_underlined=is_underlined)
      if isinstance(e, (Comment,)):
        pass
      elif isinstance(e, NavigableString): # Pure text
        if len(e.string.strip())>0:
          base['txt']=e.string.strip()
          linear.append( base )
        #continue
      elif e.name=='span':
        u = 'underline' in e.get('style', '') or 'definition' in ' '.join(e.get('class', ''))
        linear = linear + make_linear(e, found, is_underlined=u or is_underlined)
      elif e.name=='u':
        linear = linear + make_linear(e, found, is_underlined=True)
      elif e.name=='strong' or e.name=='b' or e.name=='em' or e.name=='i':
        linear = linear + make_linear(e, found, is_underlined=is_underlined)
      elif e.name=='td':  #  TD is a little questionable...  # or e.name=='td'  # TR even more so
        linear = linear + make_linear(e, found, is_underlined=is_underlined)
      elif e.name=='br':
        gather_segment=True
        
      if gather_segment and len(linear)>0:
        add_linear_to_found(found, linear, debug=debug)
        linear=[]
        
    if len(linear)>0:
      add_linear_to_found(found, linear, debug=debug)
      
    return linear
  linear = make_linear(component, found)
  
  #print(linear)
  # ...
  return found



def get_most_important_node_arr(content, debug=False):
  node_list_by_found=dict()
  for component in content.descendants:
    if len(str(component).strip())==0: continue
      
    #found = match_in_component(component)
    found = match_in_component_recursive(component)
   
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
      #score+=5
      #if 'num' in k: score +=2
      #if 'pattern' in k: score +=5
      #if 'answer' in k: score +=5
      #if 'wordplay' in k: score +=5
      score+=3
      if 'num' in k: score *= 4
      if 'pattern' in k: score *= 4
      if 'answer' in k: score *= 2
      if 'wordplay' in k: score *= 2
    score*=len(arr)
    #most_useful_found[k]=score
    if debug: print(f"{len(arr)}: {score=} :: {k}")
    if score>max_score:
      max_score=score
      max_arr=arr
  return max_arr

def build_problem_arr(clue_starts, content_next, debug=False):
  problem_arr=[]
  for i,c in enumerate(clue_starts):
    # Determine when to give up on this clue..
    clue_ends = content_next # After the list (only when i is at end of clue_starts list)
    if i+1<len(clue_starts):
      clue_ends = clue_starts[i+1]
    found = dict()
    
    while c is not None:
      #found_new = match_in_component(c, debug=debug)
      found_new = match_in_component_recursive(c, debug=debug)
      
      if len(found_new)>0:
        if debug: print(found_new)
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
          if debug: print(f"Saving : {problem}")
          problem_arr.append(problem)
          found=dict()
          break
        c = c.next_sibling  # Don't go inside, if we found something
      else:
        c = c.next_element  # Try next element
      if c==clue_ends:
        break
    if debug: print("--- Try next element ---")
  return problem_arr

def parse_content(content):
  clue_starts = get_most_important_node_arr(content)
  problem_arr = build_problem_arr(clue_starts, content.next_sibling)
  return problem_arr
  