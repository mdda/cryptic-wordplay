## Wordplay Dataset - (for Cryptic Crossword clues)

This repo includes the tools for building the **Wordplay Dataset** - 
a dataset of Cryptic Crossword Clue solutions 
created by enthusiastic solvers, 
each of which have submitted (over the years) their 
wordplay breakdowns of many cryptic crosswords to site such as:

* [https://FifteenSquared.net/](https://www.fifteensquared.net/)
* [https://TimeForTheTimes.co.uk/](https://timesforthetimes.co.uk/)

Included in the repo are _scrapers_ that are known to be effective for :
* the above two sites,
* across a number of the authors,
* which are robust to the wide variety of formats used
* by each author and over a long period of time.

Since permission has not been sought from these websites (yet), 
the full dataset is not downloadable from here. The code for extracting the wordplay lists from author pages
is included here in the `wordplay` module, and convenience scripts will soon be provided so that 
data can be gathered automatically (though it is not clear that more than the 5000 wordplay samples provided in the dataset sample in `./prebuilt` are essential to train a useful model - see below).


### LLM post-training warning

If you are looking for a post training set for an LLM : Look elsewhere!  
This dataset is intended for experimentation on reasoning tasks, 
and simply trying to use the dataset as training material 
would be as pointless as training on ARC Challenge tasks...  



## Download

There is a sample dataset with ~5400 training examples in the `./prebuilt` directory, with two splits : "train" and "val".

This sample has the following characteristics:
* Single author: `teacow` on [https://FifteenSquared.net/](https://FifteenSquared.net/author/teacow)
  + chosen for their clear and consistent `wordplay` annotations across more than 6 years of submission
* (Predominantly) Financial Times clue solutions - typically of difficulty similiar to the regular Times Cryptic
* Retrieved using `custom` (i.e. manually coded) scraping tools 
  + Should not suffer from partial captures

Even with 'only' 5K examples, this sample dataset has been found suffient to fine-tune ~7B models to guess at `definition` and `wordplay` pairs for new clues.  


### Splits

The splits used for this Wordplay Dataset are the same as those first given in [Cryptonite](https://github.com/aviaefrat/cryptonite) - and we attempt to enforce that choice in the dataset generation tools provided here.  For certainty, the "val" and "test" wordlists derived from Cryptonite are given
in `./prebuilt`.

Intentionally, the "test" version of the wordplay data is not provided, 
so that it won't be incorporated into web trawls (which could contaminate LLM training sets).

To preserve the integrity/usefulness of this Wordplay dataset, please: 
* don't even consider creating the 'test' split; and/or
* be careful not to let a copy of any 'test' split leak onto the internet.


### Dataset Format

Each line of the `jsonl` file contains the following fields:
* `clue` : The clue as given in the puzzle, but with the definition part(s) surrounded with '{}' brackets
* `pattern` : The number of letters in the answer - as given in the puzzle
* `ad` : {A,D} = Across / Down 
* `answer` : The uppercase answer that would be written in the grid - may contain spaces and '-'
* `wordplay` : Wordplay 'analysis', which can be in a wide variety of formats/styles
* `author` : this identifies the wordplay analysis author
* `setter` : name of the puzzle creator
* `publication` : where the puzzle originally appeared (simplistic)
* `is_quick` : whether the puzzle was a 'Quick' variant (simplistic)

Note that the lines in the dataset are order according to their extraction / scraping - so they
are grouped by author / in date order / in puzzle clue-order.  It is very likely that they 
require shuffling before use (or, practically speaking, an index list should be shuffled, so they
can be indexed into in a pre-defined 'random' order).

Each clue/answer/wordplay data item is also:
* Sanitised : 
  + For instance: if a given `wordplay` appears to be a `Double Definition`, it will start with that string exactly
* Sanity-checked:
  + Does the `answer` string match the `pattern` for the clue?
  + Are a majority of the letters in the `answer` present as upper-case characters in the `wordplay`?
  + Does the `clue` contain a span highlighted with '{}' as the definition (twice in the case of Double Definition wordplay)
* ... see [`./wordplay/__init__.py#L300`](/mdda/cryptic-wordplay/blob/main/wordplay/__init__.py#L300) for more details


## Installation

To use the scrapers directly, ensure its dependencies are installed:

```bash
pip install --upgrade pip
pip install requests bs4 OmegaConf
git clone https://github.com/mdda/cryptic-wordplay.git
```

Import the module (it looks up its own configuration from `./sites/config.yaml`, and caches website files in `./sites/SITENAME/`):

```python
p='./cryptic-wordplay'
if p not in sys.path:
  sys.path.append(p)

import wordplay
print( wordplay.config )
```

Note that the scrapers will cache index pages for the authors specified, and then cache the referenced
webpages.  Accesses are spaced apart so as not to inconvenience the sites' maintainers.

There are two kinds of scraping tools included: 
* The `custom` scrapers used for the sample dataset in `./prebuilt`
  + Specifically built to capture `div.fts-group` and `p[]` styles of HTML
* A more advanced `generic` scraper that (should) adaptively figure out how the list of clues/answers/wordplay annotations is formatted, and scrape those


### Assembling a dataset (train/val splits)

Example lines to gather several authors :

```bash
python create_dataset_with_splits.py  --author teacow --site fifteensquared --pages -1
python create_dataset_with_splits.py  --author pipkirby --site timesforthetimes --pages -1
python create_dataset_with_splits.py  --author chris-woods --site timesforthetimes --pages -1
```

Once _enough_ data has been generated, find the files within the directory structure:
```bash
for split in train val; do
  find sites | grep author_aggregate_${split}.jsonl | sort > list.${split}
done
```

* Edit the `list.train` and `list.val` files to select for the authors/sites required

Combine the `jsonl` files listed into `wordplay_DATE_SPLIT.jsonl` :
```bash
dt=`date --iso-8601=days`
for split in train val; do
  { xargs cat < list.${split} ; } | uniq > wordplay_${dt}_${split}.jsonl
done
```

Use the data wisely!



## Dataset Citation

Please cite this dataset as follows:
```latex
@software{Wordplay_dataset_repo,
  author = {Andrews, Martin},
  title = {{Wordplay Dataset}},
  url = {https://github.com/mdda/cryptic-wordplay},
  version = {0.0.1},
  year = {2024}
}
```

### Related Papers

The following paper(s) make use of the Wordplay dataset:

* ["Proving that Cryptic Crossword Clue Answers are Correct"](https://arxiv.org/abs/2407.08824) - Andrews & Witteveen (2024)
  + Accepted at the [ICML 2024 Workshop on LLMs and Cognition](https://llm-cognition.github.io/)
  + [Explainer Video on YouTube](https://www.youtube.com/watch?v=vLITb6XDTQ8)

