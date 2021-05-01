# Wikia/Wikipedia-NER-and-EL-Dataset-Creator
* You can create datasets from Wikia/Wikipedia that can be used for *both of* entity recognition and Entity Linking.

* Sample Dataset is available [here](https://drive.google.com/drive/folders/1gvqrj9f4IVi3lscwsa_EdAp0I4CpNTAe?usp=sharing). See also [preprocessed data examples](#preprocessed-data-example).

# Preprocessed ja-wiki dataset.

* [Here](https://drive.google.com/file/d/11_SUXM5wba1fSjF7eaTFO8ISk53nEwXk/view?usp=sharing)

## Environment Setup for Preprocessing.
```
$ conda create -n allennlp python=3.7
$ conda activate allennlp
$ pip install -r requirements.txt
$ (install wikiextractor==3.0.5 from source https://github.com/attardi/wikiextractor for activate --json option.)
```
## Dataset Preparation 
### For Wikia
* Download [worldname]_pages_current.xml from wikia statistics page to `./dataset/`.

  * For example, if you are interested in Virtual Youtuber, download `virtualyoutuber_pages_current.xml` dump from [here](https://virtualyoutuber.fandom.com/wiki/Special:Statistics).

### For Wikipedia
* Download Wikipedia-dump from [here(en)](https://dumps.wikimedia.org/enwiki/) or [here(ja)](https://dumps.wikimedia.org/jawiki/) and unzip bzip2 file.

## Sample Script for Creating EL Dataset. 
```
$ sh ./scripts/vtuber.sh
```

### Parameters for Creating Dataset
* `-augmentation_with_title_set_string_match` (Default:`True`)

  * When this parameter is `True`, first we construct title set from entire pages in one wikia `.xml`. Then, when string matches in this title set, we treat these mentions as annotated ones.
  
* `-in_document_augmentation_with_its_title` (Default:`True`)

  * When this parameter is `True`, we add another annotation to dataset with distant supervision from title, where the mention appears.
  
  * For example, [the page of *Anakin Skywalker*](https://starwars.fandom.com/wiki/Anakin_Skywalker) mentions him without anchor link, as *Anakin* or *Skywalker*.
  
  * With this parameter on, we treat these mentions as annotated ones.
  
* `-spacy_model` (Default: `en_core_web_md`)
  
  * Specify spaCy model for sentence boundary detection.

## License
* Dataset was constructed using Wikias from FANDOM and is licensed under the Creative Commons Attribution-Share Alike License (CC-BY-SA).

## Preprocessed data example from [Wikia](https://www.wikia.org/).
* [data](https://drive.google.com/drive/folders/1gvqrj9f4IVi3lscwsa_EdAp0I4CpNTAe?usp=sharing)

### `[world]_annotation.json`
| key                             | its_content                                                                          | 
| ------------------------------- | ------------------------------------------------------------------------------------ | 
| `document_title`                  | Page title where the annotation exists.                                              | 
| `anchor_sent`                     | Anchored sentence with `<a>` and `</a>`. This anchor can be used for Entity Linking. | 
| `annotation_doc_entity_title`     | Which entity to be linked if the mention is disambiguated. Redirects are also considered.                           | 
| `mention`                         | Surface form as it is in sentence where the mention appeared.                        | 
| `original_sentence`               | Sentence without anchors.                                                            | 
| `original_sentence_mention_start` | Mention span start position in original sentence.                                    | 
| `original_sentence_mention_end`   | Mention span end position in original sentence.                                      | 


* For instance, a real-world example is shown from [virtualyoutuber wikia](https://virtualyoutuber.fandom.com/).
```python3
[
    {
        "document_title": "Melissa Kinrenka",
        "anchor_sent": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of <a> Nijisanji </a>.",
        "annotation_doc_entity_title": "Nijisanji",
        "mention": "Nijisanji",
        "original_sentence": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
        "original_sentence_mention_start": 75,
        "original_sentence_mention_end": 84
    },
    {
        "document_title": "Melissa Kinrenka",
        "anchor_sent": "<a> Melissa Kinrenka </a> (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
        "annotation_doc_entity_title": "Melissa Kinrenka",
        "mention": "Melissa Kinrenka",
        "original_sentence": "Melissa Kinrenka (メリッサ・キンレンカ) is a Japanese Virtual YouTuber and member of Nijisanji.",
        "original_sentence_mention_start": 0,
        "original_sentence_mention_end": 16
    },
    ...
]
...

```
### `[world]_title2doc.json`
* Redirect-resolved title and its descriptions after sentence split are available.
```
{
    "Furen E Lustario": [
        "Furen E Lustario (フレン・E・ルスタリオ) is a female Japanese Virtual YouTuber and member of Nijisanji.",
        "A female knight of the Corvus Empire.",
        "Introduction Video.",
        "Furen's introduction.",
        "Personality.",
        "Furen lacks a surprising amount of common sense.",
        "It has been displayed in at least two streams that she cannot tell from left to right.",
        ...
    ],
    "Ibrahim": [
        "Ibrahim (イブラヒム) is a male Japanese Virtual YouTuber and a member of Nijisanji.",
        "A former oil tycoon from the Corvus Empire.",
        "Since the value of oil has fallen, he now makes a living from a hot spring that he accidentally dug up.",
        "History.",
        "Background.",
        "Ibrahim made his YouTube debut on 1 February 2020.",
        ...
    ],
    ...
}
```

## WIP

* Multiprocessing for English document.

  * Currently, parallel processing is only supported in the preprocessing of Japanese wikipedia.

* Add Entity Type to title2doc.json for each entity.