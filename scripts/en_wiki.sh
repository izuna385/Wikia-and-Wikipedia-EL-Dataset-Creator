wget -P ./dataset/ https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2 ;
bunzip2 ./dataset/enwiki-latest-pages-articles-multistream.xml.bz2 ;
python -m wikiextractor.WikiExtractor ./dataset/enwiki-latest-pages-articles-multistream.xml --links --json ;
python3 create_dataset.py -language en -dirpath_after_wikiextractor_preprocessing ./text/ -augmentation_with_title_set_string_match False -in_document_augmentation_with_its_title False -multiprocessing True ;