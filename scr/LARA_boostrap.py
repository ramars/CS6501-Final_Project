__author__ = 'zhangyin'

import numpy as np
import os
import nltk
from nltk.stem.porter import *
from nltk import FreqDist
import math

stemmer = PorterStemmer()
os.chdir("/Users/zhangyin/python projects/IR project")


def parse_to_sentence_UseVocab(content,Vocab,VocabDict):
    sent_word=[]
    sentences = nltk.sent_tokenize(content)
    for sent in sentences:
        words = nltk.word_tokenize(sent)
        temp = [stemmer.stem(w.lower()) for w in words if stemmer.stem(w.lower()) in Vocab]
        temp2 = [VocabDict.get(w) for w in temp]
        if len(temp2)>0:
            sent_word.append(temp2)
    return sent_word

# test code:
# sent = parse_to_sentence_UseVocab(content,Vocab)
# sent


class Stn:
    def __init__(self, stn, Vocab, VocabDict):
        self.stn = FreqDist(stn)
        self.unilength = len(self.stn)
        self.label = -1   # initialize the label

class Review:
    def __init__(self, review_data, Vocab, VocabDict):
        self.Overall = review_data.get("Overall")
        self.ReviewID = review_data.get("ReviewID")
        # self.Title = review_data.get("Title")
        # self.AuthorLocation = review_data.get("AuthorLocation")
        self.Author = review_data.get("Author")
        self.Date = review_data.get("Date")
        content = review_data.get("Content")
        stn_word = parse_to_sentence_UseVocab(content,Vocab,VocabDict)
        self.Stns = [Stn(stn, Vocab, VocabDict) for stn in stn_word]
        UniWord = {}
        for stn in self.Stns:
            UniWord = UniWord | stn.stn.keys()
        self.UniWord = np.array([w for w in UniWord])
        self.UniWord.sort()
        self.NumOfUniWord = len(self.UniWord)
    # def Update_Stns(self):
    #     self.Stns = [stn for stn in self.Stns if stn.label > -1]
    #     self.NumOfStns = len(self.Stns)
    #
    # def Update_NumOfWords(self):
    #     self.NumOfWords = 0
    #     for stn in self.Stns:
    #         self.NumOfWords = self.NumOfWords + stn.length


class Restaurant:
    def __init__(self, rest_data, Vocab, VocabDict):
        self.RestaurantID = rest_data.get('RestaurantInfo').get('RestaurantID')
        self.Name = rest_data.get('RestaurantInfo').get('Name')
        self.Price = rest_data.get('RestaurantInfo').get('Price')
        # self.Address = rest_data.get('RestaurantInfo').get('Address')
        # self.ImgURL = rest_data.get('RestaurantInfo').get('ImgURL')
        # self.HotelURL = rest_data.get('RestaurantInfo').get('HotelURL')
        self.Reviews = [Review(review, Vocab,VocabDict) for review in rest_data.get("Reviews") ] #hotel_data.get("Reviews")
        self.NumOfReviews = len(self.Reviews)


def compare_label(label,l):
    return label in l
    # if type(l) is list:
    #     return label in l
    # else:
    #     return label==l


def sent_aspect_match(stn,aspects):  ## one sent and all aspect terms, return hit counts for each aspect term
    count = np.zeros(len(aspects))
    i=0
    for a in aspects:
        for w in stn.stn.keys():
            if w in a:
                count[i]=count[i]+1
        i=i+1
    return count  # a list of length len(aspects)


class Corpus:
    def __init__(self, corpus, Vocab, Count, VocabDict):
        self.Vocab = Vocab
        self.VocabDict = VocabDict
        self.VocabTF = Count
        self.V = len(Vocab)
        self.Aspect_Terms = []
        self.Restaurants = [ Restaurant(rest, Vocab, VocabDict) for rest in corpus]
        self.NumOfRestaurants = len(corpus)



def To_One_List(lists):   # list of lists to one list , e.g. [[1,2],[3,4]] -> [1,2,3,4]
    L=[]
    for l in lists:
        L=L+l
    return L


def ChisqTest(N, taDF, tDF, aDF):
    A = taDF  ## term & aspect
    B = tDF - A  ## t & !a
    C = aDF - A
    D = N - A - B - C
    return N * ( A * D - B * C ) * ( A * D - B * C ) / aDF / ( B + D ) / tDF / ( C + D )

def collect_stat_for_each_review(review,aspect,Vocab):
    # review.num_stn_aspect_word = np.zeros((len(aspect),len(Vocab)))
    K = len(aspect)
    review.num_stn_aspect_word = np.zeros((K,review.NumOfUniWord))
    review.num_stn_aspect = np.zeros(K)
    # review.num_stn_word = np.zeros(len(Vocab))
    review.num_stn_word = np.zeros(review.NumOfUniWord)
    review.num_stn = 0
    for stn in review.Stns:
        if stn.label != -1:   ## remove unlabeled stns
            review.num_stn = review.num_stn + 1
            for l in stn.label:
                review.num_stn_aspect[l] = review.num_stn_aspect[l] + 1
            for w in stn.stn.keys():
                z = np.where(w == review.UniWord)[0]  # index
                review.num_stn_word[z] = review.num_stn_word[z] +1
            for l in stn.label:
                for w in stn.stn.keys():
                    z = np.where(w == review.UniWord)[0] # index
                    review.num_stn_aspect_word[l,z] = review.num_stn_aspect_word[l,z]+1
    # return num_stn_aspect_word,num_stn_aspect,num_stn_word,num_stn





class Bootstrapping:
    def sentence_label(self,corpus):   ### produce a label list
        if len(self.Aspect_Terms)>0:
            for rest in corpus.Restaurants:
                for review in rest.Reviews:
                    for stn in review.Stns:
                        count=sent_aspect_match(stn,self.Aspect_Terms)
                        if max(count)>0:
                            s_label = np.where(np.max(count)==count)[0].tolist()
                            stn.label = s_label # with tie
        else:
            return "Warning: No sentences or Aspect_Terms are recorded in this corpus"

    def calc_chi_sq(self,corpus):
        K=len(self.Aspect_Terms)
        V=len(corpus.Vocab)
        corpus.all_num_stn_aspect_word = np.zeros((K,V))
        corpus.all_num_stn_aspect = np.zeros(K)
        corpus.all_num_stn_word = np.zeros(V)
        corpus.all_num_stn = 0
        Chi_sq = np.zeros((K,V))
        if K>0:
            for rest in corpus.Restaurants:
                for review in rest.Reviews:
                    collect_stat_for_each_review(review,self.Aspect_Terms,corpus.Vocab)
                    corpus.all_num_stn = corpus.all_num_stn + review.num_stn
                    corpus.all_num_stn_aspect = corpus.all_num_stn_aspect + review.num_stn_aspect
                    for w in review.UniWord:
                        z = np.where(w == review.UniWord)[0][0] # index, since the matrix for review is small
                        corpus.all_num_stn_word[w] = corpus.all_num_stn_word[w] + review.num_stn_word[z]
                        corpus.all_num_stn_aspect_word[:,w] = corpus.all_num_stn_aspect_word[:,w] + review.num_stn_aspect_word[:,z]

            for k in range(K):
                for w in range(V):
                    Chi_sq[k,w] = ChisqTest(corpus.all_num_stn, corpus.all_num_stn_aspect_word[k,w], corpus.all_num_stn_word[w], corpus.all_num_stn_aspect[k])
            self.Chi_sq = Chi_sq
        else:
            print("Warning: No aspects were pre-specified")

def load_Aspect_Terms(analyzer,filepath,VocabDict):
    analyzer.Aspect_Terms=[]
    f = open(filepath, "r")
    for line in f:
        aspect = [VocabDict.get(stemmer.stem(w.strip().lower())) for w in line.split(",")]
        analyzer.Aspect_Terms.append(aspect)
    f.close()
    print("Aspect Keywords loading completed")

def Add_Aspect_Keywords(analyzer, p, NumIter,c):
    for i in range(NumIter):
        analyzer.sentence_label(c)
        analyzer.calc_chi_sq(c)
        t=0
        for cs in analyzer.Chi_sq:
            x = cs[np.argsort(cs)[::-1]] # descending order
            y = np.array([not math.isnan(v) for v in x]) # return T of F
            words = np.argsort(cs)[::-1][y] #
            aspect_num = 0
            for w in words:
                if w not in To_One_List(analyzer.Aspect_Terms):
                    analyzer.Aspect_Terms[t].append(w)
                    aspect_num = aspect_num +1
                if aspect_num > p:
                    break
            t=t+1
        print("complete iteration "+str(i+1)+"/"+str(NumIter))

def save_Aspect_Keywords_to_file(analyzer,filepath,Vocab):
    f = open(filepath, 'w')
    for aspect in analyzer.Aspect_Terms:
        for w in aspect:
            try:
                f.write(Vocab[w]+", ")
            except:
                pass
        f.write("\n\n\n")
    f.close()

def create_W_matrix_for_each_review(analyzer,review,corpus):
    Nd = len(review.UniWord)
    K=len(analyzer.Aspect_Terms)
    # V=len(corpus.Vocab)
    review.W = np.zeros((K,Nd))
    for k in range(K):
        for w in range(Nd):  ## w is index of UniWord_for_review
            # z = review.UniWord[w]
            if corpus.all_num_stn_aspect[k] > 0:
                review.W[k,w] = review.num_stn_aspect_word[k,w]/corpus.all_num_stn_aspect[k]

def create_all_W(analyzer,corpus):
    rest_num=0
    for rest in data.Restaurants:
        print("Creating W matrix for Restaurant "+str(rest_num))
        for review in rest.Reviews:
            create_W_matrix_for_each_review(analyzer,review,corpus)
        rest_num= rest_num+1

def produce_data_for_rating(analyzer,corpus,outputfolderpath):
    dir = outputfolderpath
    if not os.path.exists(dir):
        os.makedirs(dir)

    vocabfile = outputfolderpath+"vocab1.txt"
    f = open(vocabfile,"w")
    for w in corpus.Vocab:
        f.write(w+",")
    f.close()

    reviewfile = outputfolderpath+"review_data.txt"
    f = open(reviewfile, 'w')
    for rest in corpus.Restaurants:
        for review in rest.Reviews:
            f.write(review.Overall)
            f.write(":")
            f.write(str(review.UniWord.tolist()))
            f.write(":")
            f.write(str(review.W.tolist()))
            f.write("\n")
    f.close()

def summary_stats():
    return




##### run code #######

# import numpy as np
# (corpus,Vocab,Count,VocabDict)=np.load("./output/yelp_mp1_corpus.npy")

# def run_bootstrapping():
analyzer = Bootstrapping()
loadfilepath = "/Users/zhangyin/python projects/IR project/init_aspect_word.txt"
load_Aspect_Terms(analyzer,loadfilepath,VocabDict)

(corpus,Vocab,Count,VocabDict)=np.load("./output/yelp_mp1_corpus.npy")
data = Corpus(corpus, Vocab, Count,VocabDict)
# 15 mins



Add_Aspect_Keywords(analyzer, 5, 5, data)

savefilepath = 'temp_aspect_words_yelp_mp1.txt'
save_Aspect_Keywords_to_file(analyzer,savefilepath,Vocab)

create_all_W(analyzer,data)
outputfolderpath = "/Users/zhangyin/python projects/IR project/output_data_for_rating/"
produce_data_for_rating(analyzer,data,outputfolderpath)




# # loadfilepath = "/Users/zhangyin/python projects/IR project/aspect words clean.txt"
# analyzer.Aspect_Terms
#
# # analyzer.sentence_label(data)
# # analyzer.calc_chi_sq(data)
#
# analyzer.Aspect_Terms[0]
#
# savefilepath = 'temp_aspect_words_yelp_mp1.txt'
# save_Aspect_Keywords_to_file(analyzer,savefilepath,Vocab)
#
#
# create_all_W(analyzer,data)
#
# outputfolderpath = "/Users/zhangyin/python projects/IR project/output_data_for_rating/"
# produce_data_for_rating(analyzer,data,outputfolderpath)
#
# ####### for
# # import numpy as np
# # (corpus,Vocab,Count,VocabDict)=np.load("./output/yelp_mp1_corpus.npy")
# data = Corpus(corpus, Vocab, Count,VocabDict)
# analyzer = Bootstrapping()
# loadfilepath = "/Users/zhangyin/python projects/IR project/init_aspect_word.txt"
# load_Aspect_Terms(analyzer,loadfilepath,VocabDict)
# # analyzer.calc_chi_sq(data)
# Add_Aspect_Keywords(analyzer, 5, 5, data)
# create_all_W(analyzer,data)
# outputfolderpath = "/Users/zhangyin/Google Drive/CS6501/data_for_rating/"
# produce_data_for_rating(analyzer,data,outputfolderpath)
# #######



# For tripadvisor data
# A1=[VocabDict.get(stemmer.stem(w.lower())) for w in ["value","price","quality","worth"]]
# A2=[VocabDict.get(stemmer.stem(w.lower())) for w in ["room","suite","view","bed"]]
# A3=[VocabDict.get(stemmer.stem(w.lower())) for w in ["location","traffic","minute","restaurant"]]
# A4=[VocabDict.get(stemmer.stem(w.lower())) for w in ["clean","dirty","maintain","smell"]]
# A5=[VocabDict.get(stemmer.stem(w.lower())) for w in ["stuff","check","help","reservation"]]
# A6=[VocabDict.get(stemmer.stem(w.lower())) for w in ["service","food","breakfast","buffet"]]
# A7=[VocabDict.get(stemmer.stem(w.lower())) for w in ["business","center","computer","internet"]]
# data.Aspect_Terms=[A1,A2,A3,A4,A5,A6,A7]
