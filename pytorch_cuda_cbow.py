# -*- coding: utf-8 -*-
"""cbow

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gQcApjbLRoNtVMl2uVG7mMkFfc0q_TGb
"""

import string

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

df = pd.read_csv('combined_datasets.csv', index_col=None)
NUM_SENTENCES = len(df['0'])
sentences = df['0'].astype(str)

f = lambda x: x.translate(None,'!"%&\'()*+,-./:;<=>?[\\]^_`{|}~')
sentences = sentences.apply(f)


def raw_words(corpus):
    stop_words = ['is', 'a', 'will', 'be']
    words = []
    for sentence in corpus:
        sentence = sentence.split()
        words.extend(sentence)
    words = set(words)
    for stop in stop_words:
        if stop in words:
            words.remove(stop)
    words = list(words)
    wordToint = {}
    for (index, word) in enumerate(words):
        wordToint[word] = index

    return wordToint


def remove_stop_words(corpus):
    stop_words = ['is', 'a', 'will', 'be']
    clean_data = []
    for sentence in corpus:
        sen = sentence.split()
        for word in stop_words:
            while word in sen:
                sen.remove(word)

        clean_data.append(sen)
    return clean_data


def generate_data(sentences, wordToint):
    data = []
    for sentence in sentences:
        for i in range(2, len(sentence) - 2):
            try:
                context = [wordToint[sentence[i - 2]], wordToint[sentence[i - 1]], wordToint[sentence[i + 1]],
                           wordToint[sentence[i + 2]]]
                target = wordToint[sentence[i]]
                data.append((context, target))
            except:
                print(sentence)

    return data


wordToint = raw_words(sentences)
NUM_OF_WORDS = len(wordToint)

VOCAB_SIZE = len(wordToint)
NUM_LABELS = 2
EMBEDDING_DIM = 24

sentences = remove_stop_words(sentences)
data = generate_data(sentences, wordToint)


class CBOW(nn.Module):

    def __init__(self, VOCAB_SIZE, EMBEDDING_DIM):
        super(CBOW, self).__init__()
        self.embeddings = nn.Embedding(VOCAB_SIZE, EMBEDDING_DIM, sparse=True)
        self.linear1 = nn.Linear(EMBEDDING_DIM, VOCAB_SIZE)

    def forward(self, inputs):
        lookup_embeds = self.embeddings(inputs)
        embeds = lookup_embeds.sum(dim=0)
        out = self.linear1(embeds)
        out = F.log_softmax(out)
        return out


model = CBOW(VOCAB_SIZE, EMBEDDING_DIM)
model.cuda()
loss_function = nn.NLLLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

for epoch in range(5):
    total_loss = 0
    for (context, target) in data:
        context_vector = torch.cuda.LongTensor(context)
        context_vector = Variable(context_vector)
        model.zero_grad()
        log_probs = model(context_vector).view(-1, VOCAB_SIZE).cuda()
        loss = loss_function(input=log_probs, target=torch.tensor(target).view(-1).cuda())
        loss.backward()
        optimizer.step()

        total_loss += loss.data


    print("Step: %i loss: %d\n" % (epoch, total_loss))

f = open('vectors_pytorch.txt', 'w')
f.write('{} {}\n'.format(NUM_OF_WORDS, EMBEDDING_DIM))
vectors = model.embeddings.weight.data
for word, i in wordToint.items():
    f.write('{} {}\n'.format(word, ' '.join(map(str, list(vectors[i, :])))))
f.close()
