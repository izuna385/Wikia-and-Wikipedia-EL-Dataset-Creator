# Wikia-NER-and-EL-Dataset-Creator

## Dataset
* Download *.xml from wikia statistics page to './dataset/.

  * https://virtualyoutuber.fandom.com/wiki/Special:Statistics

## Preprocess
* `python -m wikiextractor.WikiExtractor ./dataset/virtualyoutuber_pages_current.xml --links --json`

## Run
* `python3 create_dataset.py`

## License
Dataset was constructed using Wikias from FANDOM and is licensed under the Creative Commons Attribution-Share Alike License (CC-BY-SA).