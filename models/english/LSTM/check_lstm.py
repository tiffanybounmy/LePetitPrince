import argparse
import torch
from data import Corpus



def check_lstm(model, data, save_path, words2generate=1000, temperatur=1.0, log_interval=100, cuda=False, seed=1111)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        if not cuda:
            print("WARNING: You have a CUDA device, so you should probably run with --cuda")

    device = torch.device("cuda" if cuda else "cpu")

    if temperature < 1e-3 :
        parser.error('--temperature has to be greater or equal to 1e-3')

    with open(model, 'rb') as f:
        model = torch.load(f).to(device)
    model.eval()

    corpus = Corpus(data)
    ntokens = len(Corpus.dictionary)
    hidden = model.init_hidden(1)
    input = torch.randint(ntokens, (1,1), dtype=torch.long).to(device)
    with open(save, 'w') as outf:
        with torch.no_grad(): # no tracking history
            for i in range(words):
                output, hidden = model(input, hidden)
                word_weights = output.squeeze().div(temperature).exp().cpu()
                word_idx = torch.multinomial(word_weights, 1)[0]
                input.fill_(word_idx)
                word = corpus.dictionary.idx2word[word_idx]

                outf.write(word + ('\n' if i % 20 == 19 else ' '))

                if i % log_interval == 0:
                    print('| Generated {}/{} words'.format(i, words))