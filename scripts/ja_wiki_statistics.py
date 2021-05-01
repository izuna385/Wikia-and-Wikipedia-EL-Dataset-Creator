from glob import glob
from tqdm import tqdm
import pdb
import json
from multiprocessing import Pool
import multiprocessing as multi
PREPROCESSED_DOCS_DIRPATH = './preprocessed/'

def ja_wiki_statistics():
    json_paths = glob(PREPROCESSED_DOCS_DIRPATH+'**/*.json')

    mention_annotation_counts, not_null_annotation_counts = 0, 0
    entities = 0
    n_cores = multi.cpu_count()
    with Pool(n_cores) as pool:
        imap = pool.imap(jpath_2_partial_statistics, json_paths)
        result = list(tqdm(imap, total=len(json_paths)))

    for r in result:
        mention_annotation_counts += r[0]
        not_null_annotation_counts += r[1]
        entities += r[2]

    print('all mentions:', mention_annotation_counts)
    print('Not None mentions:', not_null_annotation_counts)
    print('entities (Redirect Resolved):', entities)

def jpath_2_partial_statistics(j_path):
    '''

    :param j_path:
    :return: mention_annotation_counts, not_null_annotation_counts, entities
    '''
    mention_annotation_counts, not_null_annotation_counts = 0, 0
    entities = 0

    annotations, doc_title2sents = jr(j_path)
    mention_annotation_counts += len(annotations)
    for annotation in annotations:
        if annotation['annotation_doc_entity_title'] != None:
            not_null_annotation_counts += 1
    entities += len(doc_title2sents)

    return mention_annotation_counts, not_null_annotation_counts, entities

def jr(j_path):
    with open(j_path, 'r') as f:
        j = json.load(f)

    return j['annotations'], j['doc_title2sents']

if __name__ == '__main__':
    ja_wiki_statistics()