import argparse
import sys, json
from distutils.util import strtobool

class WikiaPreprocessParams:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Entity linker')
        parser.add_argument('-debug', action='store', default=False, type=strtobool)
        parser.add_argument('-spacy_model', action='store', default='en_core_web_md', type=str)
        parser.add_argument('-language', action='store', default='en', type=str)
        parser.add_argument('-world', action='store', default='virtualyoutuber', type=str)
        parser.add_argument('-path_for_raw_xml', action='store', default='./dataset/virtualyoutuber_pages_current.xml', type=str)
        parser.add_argument('-dirpath_after_wikiextractor_preprocessing', action='store', default='./text/', type=str)
        parser.add_argument('-augmentation_with_title_set_string_match', action='store', default=True, type=strtobool)
        parser.add_argument('-in_document_augmentation_with_its_title', action='store', default=True, type=strtobool)
        parser.add_argument('-annotated_dataset_dir', action='store', default='./preprocessed/', type=str)
        parser.add_argument('-stopwords_for_augmentation', action='store', default='virtual,Virtual,youtuber,Youtuber', type=str)

        self.opts = parser.parse_args(sys.argv[1:])
        print('\n===PARAMETERS===')
        for arg in vars(self.opts):
            print(arg, getattr(self.opts, arg))
        print('===PARAMETERS END===\n')

    def get_params(self):
        return self.opts

    def dump_params(self, experiment_dir):
        parameters = vars(self.get_params())
        with open(experiment_dir + 'parameters.json', 'w') as f:
            json.dump(parameters, f, ensure_ascii=False, indent=4, sort_keys=False, separators=(',', ': '))