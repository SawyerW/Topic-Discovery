#!/usr/bin/env python
import keras
import os
from keras.callbacks import LearningRateScheduler, ModelCheckpoint
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
import pandas as pd
import re
import csv
from keras.utils.vis_utils import model_to_dot
from IPython.display import SVG
from keras.layers import Input, LSTM, RepeatVector,TimeDistributed,Dense,Dropout,Embedding,Masking
from keras.models import Model
from collections import defaultdict
from itertools import count
from functools import partial
from collections import defaultdict
from keras.models import Sequential
from collections import defaultdict
from keras.preprocessing import text
import nltk
import sys
import gensim
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
import numpy as np
from nltk import word_tokenize
from nltk import download
from nltk.corpus import stopwords
from sklearn.preprocessing import Normalizer
from keras.optimizers import Adam, RMSprop, SGD
from Get_Amazon_reviews_vectors import write_vec_to_csv
from collections import deque
from keras import optimizers
nltk.download('punkt')
nltk.download('stopwords')
stop_words = stopwords.words('english')
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
reload(sys)
sys.setdefaultencoding('utf8')
def get_data():
    targets = ['cameras','laptops','mobilephone','tablets','TVs','video_surveillance']
    path =['/home/flippped/thesis_project/Reviews/Amazon_300_500/camera_no',
           '/home/flippped/thesis_project/Reviews/Amazon_300_500/laptop_no',
           '/home/flippped/thesis_project/Reviews/Amazon_300_500/mobilephone_no',
           '/home/flippped/thesis_project/Reviews/Amazon_300_500/tablets_no',
           '/home/flippped/thesis_project/Reviews/Amazon_300_500/TVs_no',
           '/home/flippped/thesis_project/Reviews/Amazon_300_500/video_surveillance_no']
    data = []
    target=[]
    filename = []
    data_to_sentences = []
    for j in  xrange(len(path)):

        print path[j]
        #for i in path[j]:
        for file in os.listdir(path[j]):

            with open(os.path.join(path[j], file), 'r') as f:
                 document = f.read().lower()
                 target.append(targets[j])
                 filename.append(file)
                 data.append(document)
    for i in range(len(data)):
        data_to_sentences.append((tokenizer.tokenize(data[i])))
    # print data[1]
    # print data_to_sentences[1]
    #print len(target)
    return data_to_sentences,target,filename
def preprocess(text):
    print text
    doc = []
    for i in text:
        doc.append(' '.join(re.findall(r"[\w']+|[,]", i)))
    print doc
    # doc = word_tokenize(doc)
    #doc = keras.preprocessing.text.Tokenizer(num_words=None,lower=True, split=" ").fit_on_texts(doc)
    #print doc
    #doc = [word for word in doc if word.isalpha()]
    doc = [word for word in doc if word not in stop_words]
    #print doc
    return doc
def get_corpus():
    #stemmer = PorterStemmer()
    data,target,filename = get_data()
    corpus_train_tmp = [preprocess(text) for text in data]
    corpus_sentences, data, target, filenames = filter_docs(corpus_train_tmp,data,target, filename, lambda doc: (len(doc) != 0))
    # for i in corpus_train:
    #     print i
    return corpus_sentences, target, filenames
def filter_docs(corpus, texts, labels, filenames, condition_on_doc):
    """
    Filter corpus, texts and labels given the function condition_on_doc which takes
    a doc.
    The document doc is kept if condition_on_doc(doc) is true.
    """

    number_of_docs = len(corpus)

    for i in range(4):
        tmp = texts
        if i == 0:
            corpus = [corpus for (corpus,tmp) in zip(corpus,tmp) if len(tmp) > 0]
        if i == 1:
            labels = [labels for (labels, tmp) in zip(labels, tmp) if len(tmp) > 0]
        if i == 2:
            filenames = [filenames for (filenames, tmp) in zip(filenames, tmp) if len(tmp) > 0]
        if i == 3:
            texts = [texts for (texts, tmp) in zip(texts, tmp) if len(tmp) > 0]

    # if texts is not None:
    #     texts = [text for (text, doc) in zip(texts, corpus)
    #                     if condition_on_doc(doc)]
    # print "********************************************"
    # print texts
    # print doc
    # print corpus
    # print "***********************************************"
    # labels = [i for (i, doc) in zip(labels, corpus) if condition_on_doc(doc)]
    # corpus = [doc for (corpus, labels) in zip(corpus,labels) if condition_on_doc(doc)]
    # filenames = [filename for (filename,doc) in zip(filenames, corpus) if condition_on_doc(doc)]
    print("{} docs removed".format(number_of_docs - len(corpus)))

    return (corpus, texts, labels, filenames)
def string_to_integer(strings):
    string_to_number = {string: i for i, string in enumerate(set(strings), 1)}
    test = [(string_to_number[string], string) for string in strings]
    # string_to_number = defaultdict(partial(next, count(1)))
    # test = [(string_to_number[string], string) for string in strings]
    return test
def preprocess_embedding():
    corpus_train, target, filenames = get_corpus()
    sentences = []
    sent_counter = []
    # transform document into sentences
    for i in range(len(corpus_train)):
        counter = 0
        for j in corpus_train[i]:
            counter +=1
            sentences.append(j)
        # count sentences number in one document
        sent_counter.append(counter)
    tmp_len = []
    for i in sent_counter:
        tmp_len.append(i)
    max_tmp_len = max(tmp_len)
    print corpus_train
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(sentences)
    sequences = tokenizer.texts_to_sequences(sentences)

    word_index = tokenizer.word_index
    print('Found %s unique tokens.' % len(word_index))

    MAX_SEQUENCE_LENGTH = max_tmp_len
    data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

    word2vec_model = gensim.models.KeyedVectors.load_word2vec_format('/home/flippped/Windows/Linux_Project/xiangmu/baseline/GoogleNews-vectors-negative300.bin.gz', binary=True)
    word2vec_model.init_sims(replace=True)

    # create one matrix for documents words
    EMBEDDING_DIM = 300
    embedding_matrix = np.zeros((len(word_index) + 1, EMBEDDING_DIM))
    print embedding_matrix.shape
    for word, i in word_index.items():
            try:
                embedding_vector = word2vec_model[str(word)]
                if embedding_vector is not None:
                    # words not found in embedding index will be all-zeros.
                    embedding_matrix[i] = embedding_vector

            except:
                continue


    return data,target,filenames,embedding_matrix, word_index, sent_counter

def lstm_words():
    data,  targets, filenames, embedding_matrix, word_index, sent_counter = preprocess_embedding()

    EMBEDDING_DIM = 300
    MAX_SEQUENCE_LENGTH = len(data[1])

    keras.callbacks.TensorBoard(log_dir='./Graph_lstm_embedding', histogram_freq=0,
                                write_graph=True, write_images=True)
    tbCallBack = keras.callbacks.TensorBoard(log_dir='./Graph_lstm_embedding', histogram_freq=10,
                                             embeddings_layer_names='layer_embedding',
                                             embeddings_freq=100,
                                             write_graph=True, write_images=True)
    embedding_layer = Embedding(len(word_index) + 1,
                                EMBEDDING_DIM,
                                weights=[embedding_matrix],
                                input_length=MAX_SEQUENCE_LENGTH,
                                trainable= False,
                                name='layer_embedding',mask_zero=True)

    # STep 1 Training
    sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
    embedded_sequences = embedding_layer(sequence_input)

    #x1 = LSTM(150, return_sequences=True,name='lstm_1')(embedded_sequences) # [ batchsize, timesteps, input_dimension ]

    # [batchsize, timesteps, output_dimension ]

    #x2 = LSTM(75, return_sequences=True,name='lstm_2')(x1)
    encoded = LSTM(300,name='lstm_1')(embedded_sequences)

    layer_repeat_1 = RepeatVector(MAX_SEQUENCE_LENGTH,name='layer_repeat_1')(encoded)
   # x4 = LSTM(75, return_sequences=True,name='lstm_4')(x3)
    #x5 = LSTM(150, return_sequences=True,name='lstm_5')(x3)
    decoded = LSTM(300, return_sequences=True,activation='softmax',name='lstm_2')(layer_repeat_1)

    sequence_autoencoder = Model(sequence_input, decoded)
    #print sequence_autoencoder.get_layer('lstm_6').output
    encoder = Model(sequence_input, encoded) # two functions that you learn

    lr = 0.001
    sgd = optimizers.SGD(lr=lr, momentum=0.0, decay=0.0, nesterov=True)
    # RMSprop = optimizers.RMSprop(lr=0.00001, rho=0.9, epsilon=1e-08, decay=0.0)
    sequence_autoencoder.compile(loss='cosine_proximity',
                  optimizer=sgd)#, metrics=['acc'])
    embedding_layer = Model(inputs=sequence_autoencoder.input,
                                     outputs=sequence_autoencoder.get_layer('layer_embedding').output)


    sequence_autoencoder.fit(data, embedding_layer.predict(data), epochs=10,callbacks=[tbCallBack])
    # Training is done

    # define the encoding function using the trained encoded weights

    #encoder = Model(sequence_input, encoded) # a function that you learn
    print '**************************************************'
    encoded_data = encoder.predict(data)
    print encoded_data
    print '**************************************************'
    print encoded_data.shape





    # model.compile(optimizer='rmsprop',
    #               loss='mse', )
    # model.fit(a, model.get_layer('lstm_6').output, nb_epoch=5)
    # model.save('test.h5')


# def enceonding(input):
#     # this is what the learning learns
#     encoded = weights * inputs
#
# def decoding(encoded):
#     reconscructed_iput = weights * encoded
#     return reconstructed_input

    return encoded_data, sent_counter,targets,filenames
def lstm_sentences():
    encoded_data, sent_counter,targets,filenames = lstm_words()
    max_sentences_no = max(sent_counter)
    zeros = np.zeros(300).tolist()
    encoded_data = deque(encoded_data)
    sent_back = []
    #get document sentences representations
    #the final matrix shape is (len(sent_counter),max_sentences_no,300)
    for i in range(len(sent_counter)):
        temp = []
        for k in range(max_sentences_no - sent_counter[i]):
            temp.append(zeros)
        for j in range(sent_counter[i]):
            temp.append(encoded_data.popleft())
        sent_back.append(temp)
    for i in sent_back[1]:
        print i
    # STep 1 Training
    sequence_input = Input(shape=(max_sentences_no,300))
    Mask_sequences = Masking(mask_value=0.)(sequence_input)

    # x1 = LSTM(150, return_sequences=True,name='lstm_1')(embedded_sequences) # [ batchsize, timesteps, input_dimension ]

    # [batchsize, timesteps, output_dimension ]

    # x2 = LSTM(75, return_sequences=True,name='lstm_2')(x1)
    encoded = LSTM(300, name='lstm_3')(Mask_sequences)

    layer_repeat_2 = RepeatVector(max_sentences_no, name='layer_repeat_2')(encoded)
    # x4 = LSTM(75, return_sequences=True,name='lstm_4')(x3)
    # x5 = LSTM(150, return_sequences=True,name='lstm_5')(x3)
    decoded = LSTM(300, return_sequences=True, activation='softmax', name='lstm_4')(layer_repeat_2)

    sequence_autoencoder = Model(sequence_input, decoded)
    # print sequence_autoencoder.get_layer('lstm_6').output
    encoder = Model(sequence_input, encoded)  # two functions that you learn


    sgd = optimizers.SGD(lr=0.001, momentum=0.05, decay=0.0, nesterov=True)
    # RMSprop = optimizers.RMSprop(lr=0.00001, rho=0.9, epsilon=1e-08, decay=0.0)
    sequence_autoencoder.compile(loss='cosine_proximity', optimizer=sgd)  # , metrics=['acc'])

    sequence_autoencoder.fit(sent_back, sent_back, epochs=10)#, callbacks=[tbCallBack])
    print encoder.predict(sent_back)

    csvname = 'Amazon_lstm_hierachical_autoencoder'
    write_vec_to_csv(encoder.predict(sent_back),targets,filenames, csvname)



def write_vec_to_csv(doc_vector_train, targets, filenames, csvname):
    # target_name_train = []
    # for i in xrange(len(targets)):
    #     target_name_train.append(newsgroups_train.target_names[newsgroups_train.target[i]])
    # print len(target_name_train)
    # print doc_vector_train_tsne.shape
    # print len(newsgroups_train.filenames)
    output_train = np.column_stack((targets, filenames, doc_vector_train))
    output_train = np.array(output_train)

    with open('reviews_300_500_' + csvname + '_.csv', 'w') as f:
        fieldnames = ['target_names', 'filenames']
        for i in xrange(len(doc_vector_train[1])):
            fieldnames.append('x' + str(i))
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # writer = csv.DictWriter(f)
        writer.writeheader()
        writer = csv.writer(f)

        writer.writerows(output_train)


def main():
    # get_data()
    # get_corpus()
    lstm_sentences()
    # lstm()
    # preprocess_embedding()
    # embedding()


if __name__ == "__main__":
    main()
