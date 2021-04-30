wget -P ./dataset/ http://s3.amazonaws.com/wikia_xml_dumps/v/vi/virtualyoutuber_pages_current.xml.7z ;
py7zr x ./dataset/virtualyoutuber_pages_current.xml.7z ;
mv virtualyoutuber_pages_current.xml  ./dataset/ ;
python -m wikiextractor.WikiExtractor ./dataset/virtualyoutuber_pages_current.xml --links --json ;
python3 create_dataset.py -world virtualyoutuber -stopwords_for_augmentation virtual,Virtual,youtuber,Youtuber;