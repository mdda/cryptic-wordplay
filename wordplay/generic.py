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


