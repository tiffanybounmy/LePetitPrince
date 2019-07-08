################################################################
# General GLOVE Language Model
#
################################################################
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if root not in sys.path:
    sys.path.append(root)


from tqdm import tqdm
import pandas as pd
import numpy as np
from .tokenizer import tokenize
from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.models import KeyedVectors
from gensim.models import Word2Vec
from utilities.settings import Paths
from . import utils


paths = Paths()


class Glove(object):

    def __init__(self, embedding_size=300, training_set='wikipedia', path2model=None, language='english'):
        super(Glove, self).__init__()
        if not path2model:
            default_model = os.path.join(paths.path2derivatives, 'fMRI/models', language, 'glove_6B_300d.bin')
            if os.path.isfile(default_model):
                self.model = Word2Vec.load(default_model)
            self.load_default_model(language, default_model)
        else:
            try:
                self.model = Word2Vec.load(path2model)
            except:
                self.model = None
        self.param = {'model_type':'GLOVE', 'embedding-size':embedding_size, 'training_set':training_set, 'language':language}
    

    def load_default_model(self, language, saving_path):
        glove_input_file = os.path.join(paths.path2data, 'text', language, 'glove_training', 'glove.6B.300d.txt')
        word2vec_output_file = os.path.join(paths.path2data, 'text', language, 'glove_training', 'glove.6B.300d.txt.word2vec')
        if not os.path.isfile(word2vec_output_file):
            assert os.path.isfile(glove_input_file) 
            glove2word2vec(glove_input_file, word2vec_output_file)
        self.model = KeyedVectors.load_word2vec_format(word2vec_output_file, binary=False)
        self.model.save(saving_path)


    def __name__(self):
        return '_'.join([self.param['model_type'], 'language', self.param['language'], 'embedding-size', str(self.param['embedding-size']),'training_set', self.param['training_set']])


    def generate(self, path, language):
        parameters = sorted(parameters)
        columns_activations = ['embedding-{}'.format(i) for i in range(self.param['embedding-size'])]
        activations = []
        iterator = tokenize(path, language)
        for item in tqdm(iterator):
            activations.append(self.model[item])
        return pd.DataFrame(np.vstack(activations), columns=columns_activations)
    