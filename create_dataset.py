#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import codecs
import re
from parameters import WikiaPreprocessParams
from glob import glob
import os
import json
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote
import copy
from tqdm import tqdm
import nltk
from sentencizer import nlp_returner, pysbd_sentencizer, nltk_sentencizer
import html
import six
import pdb
from xml.etree.cElementTree import iterparse
from konoha import SentenceTokenizer
nltk.download('brown')
from nltk import FreqDist
from nltk.corpus import brown
import logging
from marisa_trie import Trie, RecordTrie
from multiprocessing import Pool
import multiprocessing as multi

frequency_word_list = FreqDist(i.lower() for i in brown.words())
COMMON_WORDS = [w_and_freq[0] for w_and_freq in frequency_word_list.most_common()[:10000]]
logger = logging.getLogger(__name__)
DEFAULT_IGNORED_NS = ('wikipedia:', 'file:', 'portal:', 'template:', 'mediawiki:', 'user:',
                      'help:', 'book:', 'draft:', 'module:', 'timedtext:')
NAMESPACE_RE = re.compile(r"^{(.*?)}")

class Preprocessor:
    def __init__(self, args):
        self.args = args
        self.all_titles = self._all_titles_collector()
        self.redirects = _extract_pages(self.args.path_for_raw_xml)
        self.nlp = nlp_returner(args=self.args)

        self.entity_dict = Trie(self.all_titles)

        self.redirect_dict = RecordTrie('<I', [
            (title, (self.entity_dict[dest_title],))
            for (title, dest_title) in self.redirects if dest_title in self.entity_dict
        ])

    def entire_annotation_retriever(self):
        dirpath_after_wikiextractor_preprocessing = self.args.dirpath_after_wikiextractor_preprocessing
        file_paths = glob(dirpath_after_wikiextractor_preprocessing+'**/*')

        if self.args.debug:
            file_paths = file_paths[:16]

        entire_annotations = list()
        doc_title2sents = {}

        debug_idx = 0

        if self.args.multiprocessing:
            n_cores = multi.cpu_count()
            with Pool(n_cores) as pool:
                imap = pool.imap_unordered(self._one_wikifile_process, file_paths)
                result = list(tqdm(imap, total=len(file_paths)))
        else:
            for file in tqdm(file_paths):
                with open(file, 'r') as f:
                    for idx, line in tqdm(enumerate(f)): # TODO: multiprocessing
                        line = line.strip()
                        line = json.loads(line)
                        title = _normalize_title(html.unescape(line['title']))
                        one_page_text = html.unescape(line['text'])
                        annotations, sents = self._one_page_text_preprocessor(title=title, text=one_page_text)
                        sents = self._section_anchor_remover(sents)
                        entire_annotations += annotations
                        if sents != list():
                            doc_title2sents.update({title: sents})
                        debug_idx += 1

                        if self.args.debug and debug_idx == 500:
                            break
                    else:
                        continue
                    break # for debug

            print('all annotations:', len(entire_annotations))

            with open(self.args.annotated_dataset_dir + self.args.world +'_annotation.json', 'w') as f:
                json.dump(entire_annotations, f, ensure_ascii=False, indent=4, sort_keys=False, separators=(',', ': '))

            with open(self.args.annotated_dataset_dir + self.args.world +'_title2doc.json', 'w') as g:
                json.dump(doc_title2sents, g, ensure_ascii=False, indent=4, sort_keys=False, separators=(',', ': '))

    def _one_wikifile_process(self, file_path):
        partial_annotations = list()
        partial_doc_title2sents = {}

        with open(file_path, 'r') as f:
            for idx, line in tqdm(enumerate(f)):  # TODO: multiprocessing
                line = line.strip()
                line = json.loads(line)
                title = _normalize_title(html.unescape(line['title']))
                one_page_text = html.unescape(line['text'])
                annotations, sents = self._one_page_text_preprocessor(title=title, text=one_page_text)
                sents = self._section_anchor_remover(sents)
                partial_annotations += annotations
                if sents != list():
                    partial_doc_title2sents.update({title: sents})
        d_json = {'annotations': partial_annotations, 'doc_title2sents': partial_doc_title2sents}
        new_path = file_path.replace(self.args.dirpath_after_wikiextractor_preprocessing,
                                     self.args.annotated_dataset_dir).split('/')
        suffix = new_path[3]
        new_path = '/'.join(new_path[:3])
        if not os.path.exists(self.args.annotated_dataset_dir):
            os.mkdir(self.self.args.annotated_dataset_dir)
        if not os.path.exists(new_path):
            os.mkdir(new_path)
        new_path += '/'
        new_path += suffix
        new_path += '.json'

        with open(new_path, 'w') as dj:
            json.dump(d_json, dj, ensure_ascii=False, indent=4, sort_keys=False, separators=(',', ': '))

        return 1

    def _all_titles_collector(self):
        dirpath_after_wikiextractor_preprocessing = self.args.dirpath_after_wikiextractor_preprocessing
        file_paths = glob(dirpath_after_wikiextractor_preprocessing+'**/*')
        titles = list()

        if self.args.debug:
            file_paths = file_paths[:200]

        for file in tqdm(file_paths):
            with open(file, 'r') as f:
                for line in f:
                    line = line.strip()
                    line = json.loads(line)
                    title = line['title']
                    if '/Gallery' not in title and 'List of' not in title:
                        titles.append(title)

        return list(set(titles))

    def _one_page_text_preprocessor(self, text: str, title: str):
        sections_and_sentences = self._single_newline_to_sentences(text)

        # sections_and_sentences = self._no_sentence_remover(sections_and_sentences)
        sections_and_sentences = self._section_anchor_remover(sections_and_sentences)
        sections_and_sentences = [self._external_link_remover_from_one_sentence(sentence=sentence)
                                  for sentence in sections_and_sentences]
        # coref_link_counts_in_one_page = self._coref_link_counts(sections_and_sentences)
        annotations = list()
        sentences_in_one_doc = list()
        for sentence in sections_and_sentences:
            a_tag_remain_text, entities = self._from_anchor_tags_to_entities(text=sentence)
            a_tag_no_remaining_text, positions = self._convert_a_tag_to_start_and_end_position(text_which_may_contain_a_tag=a_tag_remain_text)
            annotation_json, sents = self._sentence_splitter_with_hyperlink_annotations(title, a_tag_no_remaining_text, positions, entities)
            if self.args.augmentation_with_title_set_string_match:
                annotation_json = self._from_entire_titles_distant_augmentaton(annotation_json=annotation_json, sents=sents, document_title=title)

            if self.args.in_document_augmentation_with_its_title:
                annotation_json = self._indocument_augmentation_with_its_title(annotation_json=annotation_json, sents=sents, document_title=title)

            # TODO: Coreference resolusion
            # if self.args.coref_augmentation:
            #     annotation_json = self._coref_augmentation(annotation_json, title, sents)

            sentences_in_one_doc += sents

            if annotation_json != {}:
                for _, annotation in annotation_json.items():
                    annotations.append(annotation)

        return annotations, sentences_in_one_doc

    def _coref_augmentation(self, annotation_json, title, sents):
        ''' add annotations from she/he/her/his match'''
        return annotation_json

    def _indocument_augmentation_with_its_title(self, annotation_json, sents, document_title):
        lower_document_title = copy.copy(document_title).lower().split(' ')
        its_partial_name = [name for name in lower_document_title if not name in COMMON_WORDS]
        capitalized = [name.capitalize() for name in its_partial_name if not name.capitalize() in self.args.stopwords_for_augmentation]

        if len(capitalized) == 0:
            return annotation_json

        for sent in sents:
            match_result_with_distant_supervision = re.finditer('|'.join(capitalized), sent)

            for result in match_result_with_distant_supervision:
                span = result.span()
                mention = sent[span[0]:span[1]]
                start, end = span[0], span[1]

                same_annotation_flag = 0
                for idx, original_annotation_from_doc in annotation_json.items():
                    mention_from_annotation = original_annotation_from_doc['mention']
                    span_start_from_annotation = original_annotation_from_doc['original_sentence_mention_start']
                    span_end_from_annotation = original_annotation_from_doc['original_sentence_mention_end']
                    if mention in mention_from_annotation and span_start_from_annotation <= start and end <= span_end_from_annotation:
                        same_annotation_flag += 1
                        break

                if same_annotation_flag:
                    continue

                if sent[start] == ' ':
                    sent_annotated = sent[:start] + '<a>' + sent[start: end] + ' </a>' + sent[end:]
                else:
                    sent_annotated = sent[:start] + '<a> ' + sent[start: end] + ' </a>' + sent[end:]

                annotation_json.update({len(annotation_json):
                                            {
                'document_title': document_title,
                'anchor_sent': sent_annotated,
                'annotation_doc_entity_title': document_title,
                'mention': sent[span[0]:span[1]],
                'original_sentence': sent,
                'original_sentence_mention_start': span[0],
                'original_sentence_mention_end': span[1]
                                            }})
        return annotation_json

    def _from_entire_titles_distant_augmentaton(self, annotation_json, sents, document_title):
        '''
        Augment annotations from title collections. Strict string match is used here.
        :param annotation_json:
        :param sents:
        :param document_title:
        :return:
        '''
        regex_pattern_for_all_titles = '|'.join(self.all_titles)
        for sent in sents:

            match_result_with_distant_supervision = re.finditer(regex_pattern_for_all_titles, sent)

            for result in match_result_with_distant_supervision:
                span = result.span()
                mention = sent[span[0]:span[1]]
                start, end = span[0], span[1]

                if end != len(sent) and sent[end] not in [" ", "'"]:
                    continue

                same_annotation_flag = 0
                for idx, original_annotation_from_doc in annotation_json.items():
                    mention_from_annotation = original_annotation_from_doc['mention']
                    span_start_from_annotation = original_annotation_from_doc['original_sentence_mention_start']
                    span_end_from_annotation = original_annotation_from_doc['original_sentence_mention_end']
                    if mention_from_annotation == mention and start == span_start_from_annotation and end == span_end_from_annotation:
                        same_annotation_flag += 1
                        # print('duplicated distant supervised annotation: skipped')
                        break

                if same_annotation_flag:
                    continue

                if sent[start] == ' ':
                    sent_annotated = sent[:start] + '<a>' + sent[start: end] + ' </a>' + sent[end:]
                else:
                    sent_annotated = sent[:start] + '<a> ' + sent[start: end] + ' </a>' + sent[end:]

                annotation_json.update({len(annotation_json):
                                            {
                'document_title': document_title,
                'anchor_sent': sent_annotated,
                'annotation_doc_entity_title': self.get_entity(mention), # Redirects are resolved.
                'mention': sent[span[0]:span[1]],
                'original_sentence': sent,
                'original_sentence_mention_start': span[0],
                'original_sentence_mention_end': span[1]
                                            }})

        return annotation_json


    def _sentence_splitter_with_hyperlink_annotations(self, title:str, a_tag_no_remaining_text: str, positions: list,
                                                      entities: list):
        if self.args.language == 'en':
            if self.args.multiprocessing:
                raise Exception('Currently not implemented.')
                # sents = nltk_sentencizer(a_tag_no_remaining_text)
            else:
                doc = self.nlp(a_tag_no_remaining_text)
                sents = [sentence.text for sentence in doc.sents]

            # Currently spacy can't be applyed to multiprocessing, so we gonna use pysbd or nltk when multiprocessing.
            # But they have some bug. Space is added at the end of each split sentence.
            # sents = pysbd_sentencizer(a_tag_no_remaining_text)

        elif self.args.language == 'ja':
            t = SentenceTokenizer()
            sents = t.tokenize(a_tag_no_remaining_text)
        else:
            raise ValueError("sentencizer for {} is currently not implemented".format(self.args.language))

        annotation_id2its_annotations = {}
        sent_initial_length = 0

        for sent in sents:
            if self.args.language == 'en':
                sent_length = len(sent) + 1
            elif self.args.language == 'ja':
                sent_length = copy.copy(len(sent))
            else:
                raise ValueError("sentencizer for {} is currently not implemented".format(self.args.language))
            initial_char_idx = copy.copy(sent_initial_length)
            end_char_idx = initial_char_idx + sent_length

            to_be_considered_annotations = list()
            for annotation ,entity in zip(positions, entities):
                start = annotation[0]
                end = annotation[1]
                if initial_char_idx <= start and end <= end_char_idx:
                    to_be_considered_annotations.append((start - sent_initial_length, end - sent_initial_length, entity))

            for shift_annotation in to_be_considered_annotations:
                start = shift_annotation[0]
                end = shift_annotation[1]
                entity = shift_annotation[2]

                if entity == 'Infobox':
                    continue

                try:
                    if self.args.language == 'ja':
                        sent_annotated = sent[:start] + '<a>' + sent[start: end] + '</a>' + sent[end:]
                    elif sent[start] == ' ':
                        sent_annotated = sent[:start] + '<a>' + sent[start: end] + ' </a>' + sent[end:]
                    else:
                        sent_annotated = sent[:start] + '<a> ' + sent[start: end] + ' </a>' + sent[end:]
                except:
                    print('annotation error')
                    continue

                # TODO: add assertionError
                annotation_id2its_annotations.update({len(annotation_id2its_annotations): {
                    'document_title': title,
                    'anchor_sent': sent_annotated,
                    'annotation_doc_entity_title': entity,
                    'mention': sent[start:end],
                    'original_sentence': sent,
                    'original_sentence_mention_start': start,
                    'original_sentence_mention_end': end,
                }})

            sent_initial_length += sent_length

        return annotation_id2its_annotations, sents

    def _convert_a_tag_to_start_and_end_position(self, text_which_may_contain_a_tag: str):
        a_tag_regex = "<a>(.+?)</a>"
        pattern = re.compile(a_tag_regex)

        a_tag_remaining_text = copy.copy(text_which_may_contain_a_tag)
        mention_positions = list()

        while '<a>' in a_tag_remaining_text:
            result = re.search(pattern=pattern, string=a_tag_remaining_text)
            if result == None:
                break

            original_start, original_end = result.span()
            a_tag_removed_start = copy.copy(original_start)
            a_tag_removed_end = copy.copy(original_end) - 7

            mention = result.group(1)

            original_text_before_mention = a_tag_remaining_text[:original_start]
            original_text_after_mention = a_tag_remaining_text[original_end:]

            one_mention_a_tag_removed_text = original_text_before_mention + mention + original_text_after_mention
            assert mention == one_mention_a_tag_removed_text[a_tag_removed_start: a_tag_removed_end]

            mention_positions.append((a_tag_removed_start, a_tag_removed_end))
            a_tag_remaining_text = copy.copy(one_mention_a_tag_removed_text)

        return a_tag_remaining_text, mention_positions

    def _from_anchor_tags_to_entities(self, text: str):
        '''
        :param text: text which contains <a> tag
        :return: {'text': text,
        'entites': [{'start': 0, 'end': 3, 'mention': 'Furen'}, ...]}

        sample text
        'She used to be the second most subscribed Virtual Youtuber on Youe after <a href="Kizuna%20AI">Kizuna AI</a> until <a href="Gawr%20Gura">Gawr Gura</a> and others surpassed her in 2020.'

        return
        'She used to be the second most subscribed Virtual Youtuber on Youe after <a>Kizuna AI</a> until <a>Gawr Gura</a> and others surpassed her in 2020.', ['Kizuna AI', 'Gawr Gura']
        '''
        soup = BeautifulSoup(text, "html.parser")

        entities = list()
        for link in soup.find_all("a"):
            try:
                entity = unquote(link.get("href"))
                entities.append(self.get_entity(entity)) # Redirects are resolved.
                del link['href']
            except Exception as e:
                print("exception args:", e.args)
                continue

        return str(soup), entities


    def _coref_link_counts(self, sentences):
        entire_hyperlink_counts = 0
        for sentence in sentences:
            soup = BeautifulSoup(sentence, "html.parser")
            link_counts_in_one_sentence = len(soup.find_all("a"))
            entire_hyperlink_counts += link_counts_in_one_sentence

            coref_dict = {'he':0, 'she': 0, 'his': 0, 'her': 0}

            for word in sentence.lower().split(' '):
                if word.strip() in coref_dict:
                    coref_dict[word.strip()] += 1

            coref_link_sum = sum([v for v in coref_dict.values()])
            entire_hyperlink_counts += coref_link_sum

        return entire_hyperlink_counts

    def _external_link_remover_from_one_sentence(self, sentence: str):
        '''
        https://stackoverflow.com/questions/19080957/how-to-remove-all-a-href-tags-from-text
        https://senablog.com/python-bs4-modification/
        :param sentence:
        :return:
        '''

        soup = BeautifulSoup(sentence, "html.parser")

        for link in soup.find_all("a"):
            try:
                if "http" in link.get("href"):
                    link.unwrap()
            except:
                continue

        return str(soup)

    def _double_newline_replacer(self, text):
        return text.replace('\n\n', '\n')

    def _single_newline_to_sentences(self, text):
        return text.split('\n')

    def _no_sentence_remover(self, sentences):
        new_sentences = list()
        for sentence in sentences:
            if sentence.strip() == '':
                continue
            new_sentences.append(sentence)

        return new_sentences

    def _section_anchor_remover(self, sentences):
        new_sentences = list()
        for sentence in sentences:
            if sentence.replace(' ','').endswith('ns>'):
                continue
            if sentence.replace(' ','').endswith('model>'):
                continue
            if sentence.replace(' ','').endswith('format>'):
                continue
            if sentence.replace(' ','').endswith('timestamp>'):
                continue
            if sentence.replace(' ','').endswith('contributor>'):
                continue
            if sentence.replace(' ','').endswith('username>'):
                continue
            if sentence.replace(' ','').endswith('comment>'):
                continue
            if sentence.replace(' ','').endswith('revision>'):
                continue
            if sentence.replace(' ','').endswith('parentid>'):
                continue
            if sentence.endswith(' />') and sentence.startswith('<mainpage-'):
                continue
            if len(sentence.strip()) <= 2:
                continue
            if sentence.replace(' ','').endswith('minor') and sentence.replace(' ','').startswith('<minor'):
                continue
            new_sentences.append(sentence)

        return new_sentences

    def get_entity_index(self, title, resolve_redirect=True):
        '''
        Derived from https://github.com/wikipedia2vec/wikipedia2vec/blob/master/wikipedia2vec/dictionary.pyx
        '''
        if resolve_redirect:
            try:
                index = self.redirect_dict[title][0][0]
                return index
            except KeyError:
                pass
        try:
            index = self.entity_dict[title]
            return index

        except KeyError:
            return -1

    def get_entity(self, title, resolve_redirect=True, default=None):
        '''
        Derived from https://github.com/wikipedia2vec/wikipedia2vec/blob/master/wikipedia2vec/dictionary.pyx
        '''
        index = self.get_entity_index(title, resolve_redirect=resolve_redirect)
        if index == -1:
            return default
        else:
            dict_index = index
            title = self.entity_dict.restore_key(dict_index)
            return title


# obtained from https://github.com/RaRe-Technologies/gensim/blob/develop/gensim/corpora/wikicorpus.py
def _extract_pages(in_file):
    elems = (elem for (_, elem) in iterparse(in_file, events=(b'end',)))
    elem = next(elems)

    tag = six.text_type(elem.tag)
    namespace = _get_namespace(tag)
    page_tag = '{%s}page' % namespace
    text_path = './{%s}revision/{%s}text' % (namespace, namespace)
    title_path = './{%s}title' % namespace
    redirect_path = './{%s}redirect' % namespace

    redirects = list()

    for elem in tqdm(elems):
        if elem.tag == page_tag:
            title = elem.find(title_path).text
            text = elem.find(text_path).text or ''
            redirect = elem.find(redirect_path)
            if redirect is not None:
                redirect = _normalize_title(_to_unicode(redirect.attrib['title']))

            # yield _to_unicode(title), _to_unicode(text), redirect
            if redirect != None:
                redirects.append([title, redirect])

            elem.clear()

    return redirects

'''
Derived from https://github.com/wikipedia2vec/wikipedia2vec/blob/master/wikipedia2vec/dictionary.pyx
'''
def _to_unicode(s):
    if isinstance(s, str):
        return s
    return s.decode('utf-8')

def _normalize_title(title):
    return (title[0].upper() + title[1:]).replace('_', ' ')

def _get_namespace(tag):
    match_obj = NAMESPACE_RE.match(tag)
    if match_obj:
        namespace = match_obj.group(1)
        if not namespace.startswith('http://www.mediawiki.org/xml/export-'):
            raise ValueError('%s not recognized as MediaWiki dump namespace' % namespace)
        return namespace
    else:
        return ''

if __name__ == '__main__':
    P = WikiaPreprocessParams()
    params = P.opts
    preprocessor = Preprocessor(args=params)
    preprocessor.entire_annotation_retriever()