import spacy
from spacy.language import Language
from spacy.symbols import ORTH
import pysbd

@Language.component('set_custom_boundaries')
def set_custom_boundaries(doc):
    for token in doc[:-1]:
        if token.text in ('lit.', 'Lit.', 'lit', 'Lit'):
            doc[token.i].is_sent_start = False
    return doc

def nlp_returner(args):
    nlp = spacy.load(args.spacy_model)
    nlp.add_pipe('set_custom_boundaries', before="parser")
    nlp.tokenizer.add_special_case('lit.', [{ORTH: 'lit.'}])
    nlp.tokenizer.add_special_case('Lit.', [{ORTH: 'Lit.'}])

    return nlp

def pysbd_sentencizer(sentence: str):
    seg = pysbd.Segmenter(language="en", clean=False)
    return seg.segment(sentence)