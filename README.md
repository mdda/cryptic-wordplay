Dataset building tools for Cryptic Crossword Clue solutions as they appear on sites such as:
* [FifteenSquared](https://www.fifteensquared.net/)
* [TimeForTheTimes](https://timesforthetimes.co.uk/)

Included in the repo are scrapers that are known to be effective for :
* the above two sites,
* across a number of the authors, each of which have submitted (over the years) their 
wordplay breakdowns of many cryptic crosswords
* in formats that look nice, but often strain the limits of HTML taste...

Since permission has not been sought from these websites (yet), 
the full dataset is not downloadable from here.  
Scripts will be provided so that it can be gathered automatically.

For now, though, there is a sample dataset in the `./prebuilt` directory, with two splits : "train" and "val".
Intentionally, the "test" version of the wordplay data is not provided, so 
that it won't be incorporated into web trawls (which could contaminate LLM training sets).
The splits performed here make use of the "val" and "test" wordlists derived from [Cryptonite](https://github.com/aviaefrat/cryptonite) - 
a dataset that we're keen to use as the guide to our splits (again to reduce the risk of training set contamination).


> This repo will be fully ready in time for our presentation of the paper:
> "Proving that Cryptic Crossword Clue Answers are Correct" 
> at the ICML 2024 Workshop on LLMs and Cognition in Vienna on 27-July-2024.


## Installation

```python
p='./wordplay/cryptic-wordplay'
if p not in sys.path:
  sys.path.append(p)

import wordplay
print( wordplay.config )
```

## Dataset Format

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


## Download

For a sample of the data that corresponds to the data used in our initial papers, look in: `./prebuilt/`

Note also the comment above about the `cryptonite`-respecting splits - please either 
(i) don't even consider creating the 'test' split; or (ii) be careful not to let a 'test' split onto the internet.


## Citation

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
