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

| key                             | its_content                                                                          | 
| ------------------------------- | ------------------------------------------------------------------------------------ | 
| document_title                  | Page title where the annotation exists.                                              | 
| anchor_sent                     | Anchored sentence with `<a>` and `</a>`. This anchor can be used for Entity Linking. | 
| annotation_doc_entity_title     | Which entity to be linked if the mention is disambiguated.                           | 
| mention                         | Surface form as it is in sentence where the mention appeared.                        | 
| original_sentence               | Sentence without anchors.                                                            | 
| original_sentence_mention_start | Mention span start position in original sentence.                                    | 
| original_sentence_mention_end   | Mention span end position in original sentence.                                      | 


* For instance, a real-world example is shown from [virtualyoutuber wikia](https://virtualyoutuber.fandom.com/).
```python3
    {
        "doc_title": "Melissa Kinrenka",
        "annotation": [
            {
                "0": {
                    "document_title": "Melissa Kinrenka",
                    "anchor_sent": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of <a> Nijisanji </a>.",
                    "annotation_doc_entity_title": "Nijisanji",
                    "mention": "Nijisanji",
                    "original_sentence": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
                    "original_sentence_mention_start": 75,
                    "original_sentence_mention_end": 84
                },
                "1": {
                    "document_title": "Melissa Kinrenka",
                    "anchor_sent": "<a> Melissa Kinrenka </a> (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
                    "annotation_doc_entity_title": "Melissa Kinrenka",
                    "mention": "Melissa Kinrenka",
                    "original_sentence": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
                    "original_sentence_mention_start": 0,
                    "original_sentence_mention_end": 16
                }
            },
...

```