#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import helpers
import config
import wikipedia_chairs
import time

from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
#from nltk import tokenizer.tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer

#ngram_freq_folder = 'C:/Users/anjovis/desktop/nlp2017_group3/data/letters/'
ngram_freq_folder = 'D:/data/letters/'
#ngram_freq_folder = 'F:/google-bigram-cooccurrence/downloads/google_ngrams/letters/'
xml_test_data = 'C:/Users/anjovis/Desktop/nlp2017_group3/chair.xml'
#xml_test_data = 'C:/Users/eemel/Desktop/nlp2017_group3/corpus_small.xml'
# initialize nltk language processing functions
stop = set(stopwords.words('english'))
stemmer = SnowballStemmer('english')
tokenizer = RegexpTokenizer(r'\w+')  # remove all punctuation


ltime = time.localtime()
output_file = 'output_on_{}_{}_{}_at_{}_{}_{}.txt'.format(ltime.tm_mday, ltime.tm_mon,
                                                   ltime.tm_year,
                                                   ltime.tm_hour, ltime.tm_min, ltime.tm_sec)

data_dump = 'dump_on_{}_{}_{}_at_{}_{}_{}.txt'.format(ltime.tm_mday, ltime.tm_mon,
                                                   ltime.tm_year,
                                                   ltime.tm_hour, ltime.tm_min, ltime.tm_sec)

# the stopwords
'''
        stop = 
        {'yourself', 'again', 'should', 'over', 'with', 'd', 'the', 'once', 'ours', 't', 'herself', 'those', 'o', 'ain',
         'how', 'into', 'on', 'be', 'but', 'is', 'other', 'a', 'which', 's', 'mightn', 'here', 'by', 'some', 'no', 
         'between', 'its', 'up', 'below', 'only', 'aren', 'mustn', 'it', 'her', 'own', 'been', 'while', 'further', 
         'weren', 'yourselves', 'our', 'did', 'not', 'both', 'after', 'we', 'has', 'of', 'y', 'out', 'so', 'under', 
         'theirs', 'during', 'don', 'in', 'isn', 'this', 'me', 'down', 'then', 'too', 'if', 'before', 'about', 'where', 
         'any', 'these', 'such', 'against', 'most', 'when', 'hasn', 'being', 'or', 'for', 'same', 'than', 'few', 
         'because', 'them', 'just', 'until', 'won', 'haven', 'didn', 'myself', 'why', 'an', 'am', 'i', 'through', 'nor', 
         'needn', 'who', 'does', 'couldn', 'shan', 'yours', 'hadn', 'do', 'will', 'they', 'itself', 'doesn', 're', 
         'his', 'wasn', 'wouldn', 'you', 'above', 'very', 'my', 'were', 'at', 'ma', 'him', 'whom', 'there', 'she', 
         'that', 'ourselves', 'from', 'shouldn', 'now', 'have', 'doing', 'what', 'and', 'll', 'your', 'hers', 'was', 
         'as', 'all', 've', 'themselves', 'he', 'more', 'can', 'having', 'himself', 'their', 'to', 'each', 'm', 'off', 
         'are', 'had'}
# no would
'''


def disambiguate_with_wordnet_google_ngram(disambiguated_word, context, verbose=False):
    ''' Every word in overlap is scored using google-bigram data.'''

    # form the files that are to be searched
    files = helpers.get_files(ngram_freq_folder)
    # print('The number of files:', len(files))

    # Sense with the highest score is considered best. Score = occurences of the word pair / number of items in overlap
    scores = []
    # get every word sense from WordNet
    for sense in wn.synsets(disambiguated_word):
        #print(' ')
        #print(sense)
        examples = []
        for example in sense.examples():
            examples += tokenizer.tokenize(example)
        # print(sense.definition())
        definition = tokenizer.tokenize(sense.definition())

        # get hyponyms and hypernyms for the sense to get larger overlap
        hypernyms = []
        for hypernym in sense.hypernyms():
            hypernyms += tokenizer.tokenize(hypernym.definition())
            for example in hypernym.examples():
                hypernyms += tokenizer.tokenize(example)

        hyponyms = []
        for hyponym in sense.hyponyms():
            hyponyms += tokenizer.tokenize(hyponym.definition())
            for example in hyponym.examples():
                hyponyms += tokenizer.tokenize(example)

        # just concatenate the definition and all the examples
        signature = definition + examples + hypernyms + hyponyms

        # allow only one same word in the signature
        signature = list(set(signature))
        #print(signature)

        signature = [w for w in signature if w not in config.stop_extended]  # these stopwords not stemmed


        #print('signature: ', signature)

        # retain the information of the original word in stemming
        # signature format: [(stem1, word1), (stem2, word2)...]
        # stem the words in signature
        signature = [(stemmer.stem(word), word) for word in signature]

        # remove defined stopwords based on the stemmed word
        without_stopwords = []  # helper variable
        for pair in signature:
            if pair[0].lower() in stop:
                continue
            else:
                without_stopwords.append(pair)

        signature = without_stopwords

        #print('signature: ', signature)

        # form overlap between the context and the current sense
        overlap = []
        for w1 in context:
            for w2 in signature:
                # TODO Handle which one of the correct words is added: context or signature
                if w1[0] == w2[0]:
                    # Append the original non-stemmed word. Words are not stemmed in ngram-coocurence data.
                    overlap.append(w1[1])  # Use context base-word on default.

        if verbose:
            print('Sense: ', sense, 'Overlap: ', overlap)


        # form score from the overlapped words
        score = 0
        for word in overlap:
            # get occurrences for every word with the disambiguated_word
            # divided by len(signature) not to give more weight because of a lengthy definition
            score = score + get_word_occurrences(word, disambiguated_word, files)

        scores.append([score, sense])  # TODO generalize score

        with open(data_dump, 'a') as dump:
            data = 'Sense:  {}\nOverlap: {}\nScore: {}\n'. format(sense, overlap, score)
            dump.write(data)

        # print(scores)


    # loop through the scores to get the maximum

    predicted_sense = [0, 'Frequencies weren\'t found.']
    for i in scores:
        if i[0] > predicted_sense[0]:
            predicted_sense = i

    #print('Final sense: ', predicted_sense)

    return predicted_sense

def disambiguate_with_wikipedia(disambiguated_word, context, verbose=False):
    ''' Lesk-based method. Sense with the largest overlap is considered the right one.'''
    # form the files that are to be searched
    files = helpers.get_files(ngram_freq_folder)
    # print('The number of files:', len(files))

    # Sense with the highest score is considered best. Score = occurences of the word pair
    scores = []
    # get every word sense from WordNet

    senses = wikipedia_chairs.senses
    for item in senses:

        signature = tokenizer.tokenize(item[1])

        # allow only one same word in the signature

        signature = list(set(signature))
        # print(signature)

        signature = [w for w in signature if w not in config.stop_extended]  # these stopwords not stemmed

        # print('signature: ', signature)

        # retain the information of the original word in stemming
        # signature format: [(stem1, word1), (stem2, word2)...]
        # stem the words in signature
        signature = [(stemmer.stem(word), word) for word in signature]

        # remove defined stopwords based on the stemmed word
        without_stopwords = []  # helper variable
        for pair in signature:
            if pair[0].lower() in stop:
                continue
            else:
                without_stopwords.append(pair)

        signature = without_stopwords

        #print('signature: ', signature)

        # form overlap between the context and the current sense
        overlap = []
        for w1 in context:
            for w2 in signature:
                # TODO Handle which one of the correct words is added: context or signature
                if w1[0] == w2[0]:
                    # Append the original non-stemmed word. Words are not stemmed in ngram-coocurence data.
                    overlap.append(w1[1])  # Use context base-word on default.

        score = len(overlap)

        if verbose:
            print('Sense: ', item[0], 'Overlap: ', overlap)

        with open(data_dump, 'a') as dump:
            data = 'Sense:  {}\nOverlap: {}\nScore: {}\n'.format(item, overlap, score)
            dump.write(data)

            # print(scores)

        scores.append([score, item[0]])  # TODO generalize score
        # loop through the scores to get the maximum

    predicted_sense = [0, 'Frequencies weren\'t found.']
    for i in scores:
        if i[0] > predicted_sense[0]:
            predicted_sense = i

    return predicted_sense


def disambiguate_with_wikipedia_google_ngram(disambiguated_word, context, verbose=False):

    # form the files that are to be searched
    files = helpers.get_files(ngram_freq_folder)
    # print('The number of files:', len(files))

    # Sense with the highest score is considered best. Score = occurences of the word pair
    scores = []
    # get every word sense from WordNet

    senses = wikipedia_chairs.senses
    for item in senses:

        signature = tokenizer.tokenize(item[1])

        # allow only one same word in the signature

        signature = list(set(signature))
        # print(signature)

        signature = [w for w in signature if w not in config.stop_extended]  # these stopwords not stemmed

        # print('signature: ', signature)

        # retain the information of the original word in stemming
        # signature format: [(stem1, word1), (stem2, word2)...]
        # stem the words in signature
        signature = [(stemmer.stem(word), word) for word in signature]

        # remove defined stopwords based on the stemmed word
        without_stopwords = []  # helper variable
        for pair in signature:
            if pair[0].lower() in stop:
                continue
            else:
                without_stopwords.append(pair)

        signature = without_stopwords

        #print('signature: ', signature)

        # form overlap between the context and the current sense
        overlap = []
        for w1 in context:
            for w2 in signature:
                # TODO Handle which one of the correct words is added: context or signature
                if w1[0] == w2[0]:
                    # Append the original non-stemmed word. Words are not stemmed in ngram-coocurence data.
                    overlap.append(w1[1])  # Use context base-word on default.

        score = 0
        for word in overlap:
            # get occurrences for every word with the disambiguated_word
            # divided by len(signature) not to give more weight because of a lengthy definition
            score = score + get_word_occurrences(word, disambiguated_word, files)

        if verbose:
            print('Sense: ', item[0], 'Overlap: ', overlap)

        with open(data_dump, 'a') as dump:
            data = 'Sense:  {}\nOverlap: {}\nScore: {}\n'.format(item, overlap, score)
            dump.write(data)

            # print(scores)

        scores.append([score, item[0]])  # TODO generalize score
        # loop through the scores to get the maximum

    predicted_sense = [0, 'Frequencies weren\'t found.']
    for i in scores:
        if i[0] > predicted_sense[0]:
            predicted_sense = i

    # print('Final sense: ', predicted_sense)

    return predicted_sense


def get_word_occurrences(word1, word2, files):
    '''
    :param word1: either the word that is to be disambiguated or word from the overlap
    :param word2: either the word that is to be disambiguated or word from the overlap
    :param files: A list of strings that represent the filenames.
    :return:
    '''

    first_two_letters = word2.lower()[:2]  # apparently every pair of letters exists
    # search only the relevant files
    # from 'googlebooks-eng-all-2gram-20120701-do.gz_1' to 'do'
    word2_files = [file for file in files if file.split('-')[-1].split('.')[
        0] == first_two_letters]  # from 'googlebooks-eng-all-2gram-20120701-do.gz_1' to do
    # print('Files to be processed:', files)

    # check "word2 word1 co-occurence"
    cooccurrences = check_word_occurence(word1, word2, word2_files)

    # check "word1 word2 co-occurence" aka. the other half of the bi-gram
    first_two_letters = word1.lower()[:2]
    word1_files = [file for file in files if file.split('-')[-1].split('.')[
        0] == first_two_letters]

    cooccurrences += check_word_occurence(word2, word1, word1_files)

    return cooccurrences


def check_word_occurence(word1, word2, files):
    '''
        Format in files: yourself_ADJ	Calm_ADJ	47
                         word1        word2   co-occurrences
    '''
    cooccurrences = 0
    for file in files:
        #print(file)
        with open(ngram_freq_folder + file, 'r', encoding='utf-8', errors='ignore') as f:

            for line in f.readlines():
                tokens = line.rstrip().split('\t')

                if tokens[0] == word1 and tokens[1] == word2:
                    cooccurrences = int(tokens[2])
                    # print(word1, word2, cooccurrences)
                    # only one instance of a word pair in a file
                    return cooccurrences

    return cooccurrences


if __name__ == "__main__":

    test_dict = helpers.parse_xml(xml_test_data)

    correct_senses = 0
    all_senses = 0
    no_overlap = 0
    results = []

    with open(output_file, 'a') as results:
        results.write(config.file_text + '\n')

    # loop the every word from xml file
    for word in test_dict['corpus']['lexelt']:
        # loop every instance in the current lexeme
        for instance in word['instance']:

            try:
                correct_sense = instance['answer']['@senseid']
            except TypeError:  # skip instances with multiple answers
                continue

            # don't count words that we don't know the senses for, only 3 possible senses, see config.py
            if correct_sense not in config.wn17_to_wikipedia:
                continue

            word_to_be_disambiguated = instance['context']['head']

            context = instance['context']['#text']

            print(instance['answer']['@instance'])
            with open(data_dump, 'a') as dump:
                data = instance['answer']['@instance'] + '\n'
                dump.write(data)

            # TODO remove tags and quotes from context. Not so relevant because they won't be in the signature anyway.
            # can be produce errors by giving weight to senses that happen to have the keyword
            # format context to a list
            context = tokenizer.tokenize(context)
            context = list(set(context))  # only one instance allowed

            if word_to_be_disambiguated in config.plurals:
                word_to_be_disambiguated = word_to_be_disambiguated[:-1]  # remove the last letter

            combinations = [word_to_be_disambiguated, word_to_be_disambiguated.lower(), word_to_be_disambiguated.capitalize(),
                            word_to_be_disambiguated + 's', word_to_be_disambiguated.lower() + 's',
                            word_to_be_disambiguated.capitalize() + 's']

            # remove the word to be disambiguated: it doesn't provide any information for the context
            context = [w for w in context if w not in combinations]

            context = [w for w in context if w not in config.stop_extended]  # these stopwords not stemmed

            # stem the words but retain the information of the original word
            context = [(stemmer.stem(word), word) for word in context]

            # remove defined stopwords based on the stemmed word
            without_stopwords = []  # helper variable
            for pair in context:
                if pair[0].lower() in stop:
                    continue
                else:
                    without_stopwords.append(pair)

            context = without_stopwords


            predicted_sense = disambiguate_with_wikipedia_google_ngram(word_to_be_disambiguated, context, verbose=True)

            all_senses += 1
            if predicted_sense == [0, 'Frequencies weren\'t found.']:
                no_overlap += 1
                continue

            print('word_to_be_disambiguated: ', word_to_be_disambiguated)
            print('predicted_sense:', predicted_sense)
            print('correct_sense:', correct_sense)


            print('predicted_sense[1]', predicted_sense[1])
            print('config.wn17_to_wikipedia[correct_sense]', config.wn17_to_wikipedia[correct_sense])
            if predicted_sense[1] == config.wn17_to_wikipedia[correct_sense]:
                print('correct sense')
                correct_senses += 1

            print('current progress: ', all_senses)
            print('')

            data = '{}; predicted_sense: {}; correct_sense: {};\n\n'.format(instance['answer']['@instance'],
                                                                            predicted_sense, correct_sense)
            with open(data_dump, 'a') as dump:
                dump.write(data)
                dump.write('Accuracy: {} ; {} / {}'.format(correct_senses / all_senses, correct_senses, all_senses))
                dump.write('\n__________________________________________________________________________________\n')

            with open(output_file, 'a') as results:
                results.write(data)

    print(correct_senses, '/', all_senses, 'correct')
    print('Accuracy: ', correct_senses / all_senses)

    with open(output_file, 'a') as results:
        data = 'Accuracy: {} ; {} / {}'.format(correct_senses / all_senses, correct_senses, all_senses)
        results.write(data)
        results.write('The amount of no_overlap: {}'.format(no_overlap))





