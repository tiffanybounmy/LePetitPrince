
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.append(root)



from LSTM import model, train, utils
import torch
import os

from utilities.settings import Params, Paths



def load():
    # mod is only used for name retrieving ! the actual trained model is retrieved in the last line
    mod = model.RNNModel('LSTM', 5, 200, 300, 1, dropout=0.1) # ntoken is chosen randomly, it will or has been determined furing training
    data_name = 'wiki_kristina'
    language = 'english'
    return utils.load(mod, data_name, language)


if __name__ == '__main__':
    params = Params()
    paths = Paths()
    mod = model.RNNModel('LSTM', 5, 200, 300, 1, dropout=0.1)
    data = os.path.join(paths.path2data, 'text', 'english', 'lstm_training')
    data_name = 'wiki_kristina'
    language = 'english'
    train.train(mod, data, data_name, language, eval_batch_size=params.pref.eval_batch_size, bsz=params.pref.bsz)