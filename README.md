# Wikia-NER-and-EL-Dataset-Creator

## Dataset
* Download *.xml from wikia statistics page to './dataset/.

  * For example, if you are interested in Virtual Youtuber, download xml dump from [here](http://s3.amazonaws.com/wikia_xml_dumps/v/vi/virtualyoutuber_pages_current.xml.7z).

## Preprocess
* `python -m wikiextractor.WikiExtractor ./dataset/virtualyoutuber_pages_current.xml --links --json`

## Run
```
$ conda create -n allennlp python=3.7
$ conda activate allennlp
$ pip install -r requirements.txt
$ python3 create_dataset.py
```

## License
* Dataset was constructed using Wikias from FANDOM and is licensed under the Creative Commons Attribution-Share Alike License (CC-BY-SA).

## Preprocessed data example.
* [data](https://drive.google.com/drive/folders/1gvqrj9f4IVi3lscwsa_EdAp0I4CpNTAe?usp=sharing)

```python3


```