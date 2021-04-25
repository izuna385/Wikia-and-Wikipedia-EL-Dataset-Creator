import argparse
import sys, json
from distutils.util import strtobool

class WikiaPreprocessParams:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Entity linker')
        parser.add_argument('-debug', action='store', default=False, type=strtobool)
        parser.add_argument('-original_dataset_dir', action='store', default='./dataset/', type=str)
        parser.add_argument('-world', action='store', default='virtualyoutuber', type=str)
        parser.add_argument('-dirpath_after_wikiextractor_preprocessing', action='store', default='./text/', type=str)
        parser.add_argument('-coref_augmentation', action='store', default=False, type=strtobool)
        parser.add_argument('-annotated_dataset_dir', action='store', default='./preprocessed/', type=str)

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