from nltk.tokenize import sent_tokenize 
from nltk.tokenize import word_tokenize
import os
import re
import inflect
from tqdm import tqdm


special_words = {
    'english': {
        'grown-ups': 'grownups',
        'grown-up': 'grownup',
        'hasn\'t': 'hasnt',
        'hasn‘t': 'hasnt'
    },
    'french': {

    }
}


def tokenize(path, language, path_like=True, train=False):
    print('Tokenizing...')
    if path_like:
        assert os.path.exists(path)
        path = open(path, 'r', encoding='utf8').read()

    if not train:
        print('Preprocessing...')
        text = preprocess(path, special_words, language)
        print('Preprocessed.')
    else:
        text = path
    # iterator = [unk_transform(item, vocab).lower() for item in text.split()]
    iterator = [item.lower() + '.' for item in tqdm(text.split('.'))] # vocab words not lowered
    print('Tokenized.')
    return iterator


def preprocess(text, special_words, language):
    text = text.replace('\n', '')
    text = text.replace('<unk>', 'unk')
    for word in special_words[language].keys():
        text = text.replace(word, special_words[language][word])
    transf = inflect.engine()
    numbers = re.findall('\d+', text)
    for number in numbers:
        text = text.replace(number, transf.number_to_words(number))
    punctuation = ['.', '\'', ',', ';', ':', '!', '?', '/', '-', '"', '‘', '’', '(', ')', '{', '}', '[', ']', '`', '“', '”', '—']
    for item in punctuation:
        text = text.replace(item, ' '+ item + ' ')
    text = text.replace('.  .  .', '...')
    ### tokenize without punctuation ###
    # for item in punctuation:
    #     text = text.replace(item, ' ')
    ### tokenize with punctuation ###
    # ### tokenize thanks to usual tools for text without strange characters ###
    # tokenized = sent_tokenize(text, language=language)
    # tokenized = [word_tokenize(sentence, language=language) + ['<eos>'] for sentence in tokenized]
    # iterator = [unk_transform(item, vocab).lower() for sublist in tokenized for item in sublist]
    return text