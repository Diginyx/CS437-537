#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import string
import sys

import nltk
import pickle5 as pickle
import math
import re
import itertools
from tqdm import tqdm
from nltk.stem import WordNetLemmatizer
from names_dataset import NameDatasetV1  # v1
from nltk.corpus import stopwords
from itertools import combinations
from scipy import spatial
from collections import defaultdict
from nltk.corpus import wordnet
from itertools import combinations

# nltk.download('all')

# ## Reading File and creating DataFrame

# In[ ]:

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pycountry

lemmatizer = WordNetLemmatizer()
from names_dataset import NameDatasetV1  # v1

names = NameDatasetV1()

stop_words = set(stopwords.words('english'))
import pandas as pd

# In[ ]:


tqdm.pandas()


# In[ ]:


def load_files():
    print("loading files...")
    with open("./data/wiki_dataframe_augmented_nltk_corpus_to_remove_non-english.pkl", "rb") as wiki_df, \
            open("./data/inv_idx_augmented_nltk_corpus_to_remove_non-english.pkl", "rb") as inverted_index, \
            open("./data/aol_query_log_data.pkl", "rb") as aol:
        wiki_dataframe = pickle.load(wiki_df)
        inv_idx = pickle.load(inverted_index)
        aol_query_log = pickle.load(aol)

    companies_file = pd.read_csv('./data/companies_sorted.csv')
    companies_dataframe = pd.DataFrame(companies_file)
    companies = set(companies_dataframe['name'])
    # words = set(nltk.corpus.words.words())
    lower_cased_words = map(lambda word: word.lower(), nltk.corpus.words.words())
    lower_cased_words = set(list(lower_cased_words))
    for country in list(pycountry.countries):
        lower_cased_words.add(country.name.lower())
    for company in companies:
        lower_cased_words.add(str(company).lower())
    print("Done!")
    return [wiki_dataframe, inv_idx, aol_query_log, lower_cased_words]

wiki_dataframe, inv_idx, aol_query_log, lower_cased_words = load_files()


# ## Suggesting Queries

# In[ ]:

# lemmatization, lowercase, remove non alphanumeric, and stopword removal
def query_logs_preprocessing(row):
    print("preprocessing queries...")
    filtered_content = ""
    for token in nltk.word_tokenize(str(row['Query'])):
        token = lemmatizer.lemmatize(token).lower()
        if token not in stop_words and token.isalpha():
            filtered_content += token + " "
    print("Done!")
    return filtered_content[:-1]


# In[ ]:

aol_queries = aol_query_log['Query'].values


def identify_candidate_queries(query):
    print("Identifying Candidate Queries...")
    candidate_queries = defaultdict(int)
    potential = list()
    sessions_with_original_query = set(aol_query_log[aol_query_log['Query'] == query]['AnonID'])
    for anon_id in sessions_with_original_query:
        potential_queries = aol_query_log[aol_query_log['AnonID'] == anon_id]['Query']
        if len(potential_queries) > 1:
            potential.append(potential_queries)
    for aol_query in itertools.chain(*potential):
        if len(str(aol_query).split()) > len(query.split()):
            if aol_query.startswith(query):
                candidate_queries[aol_query] += 1
    print("Done!")
    return candidate_queries, len(sessions_with_original_query)


# #### Ranking Candidate Suggestions
# ##### ????????????????????(????????, ???????) = \# ???????? ???????????????????????????????? ???????? ?????????????????? ???? ???????? ???????????????????????????????? ???????? ???????? ?? \# ???????? ???????????????????????????????? ???????? ?????????????????? ???? ????????????????????????????

# In[ ]:


def rank_candidate_queries(original_query, candidates, num_sessions_containing_q):
    print("Ranking Candidate Queries")
    candidate_scores = []

    for candidate in tqdm(candidates):
        if num_sessions_containing_q != 0:
            candidate_scores.append((candidate, candidates[candidate] / num_sessions_containing_q))

    if len(candidate_scores) < 1:
        candidate_scores.append((original_query, 0))
    print("Done!")
    return sorted(candidate_scores, key=lambda candidate_score: candidate_score[1], reverse=True)


# In[ ]:


def find_rank_candidate_queries(query):
    candidate_list, num_sessions_containing_q = identify_candidate_queries(query)
    return rank_candidate_queries(query, candidate_list, num_sessions_containing_q)


# ## Relevance Ranking

# ### Identifying Candidate Resources

# In[6]:

def identify_candidate_resources(query):
    print("Identifying Candidate Resources...")
    results = set()
    split_query = query.split()
    synonyms = list()
    for term in split_query:
        synonyms.extend(wordnet.synsets(term))
    for word in synonyms:
        split_query.append(word.lemmas()[0].name())
    print(synonyms)
    split_query = list(set(split_query))
    print(split_query)
    n = len(split_query)
    candidate_list = list()
    for term in split_query:
        print(".", end="")
        if len(inv_idx[term]) > 0:
            candidate_list.append(set(inv_idx[term].keys()))
    if len(candidate_list) > 0:
        results = set.intersection(*candidate_list)
    if len(results) <= 50:
        for x in range(0,n):
            for combination in combinations(split_query, n - 1):
                print("combination: ", combination)
                print(".", end="")
                candidate_list = list()
                for term in combination:
                    if len(inv_idx[term]) > 0:
                        candidate_list.append(set(inv_idx[term].keys()))
                if len(candidate_list) > 0:
                    results = set.intersection(*candidate_list)
                if len(results) > 50:
                    return results, len(split_query)
            n -= 1
    # print(results)
    return results, len(split_query)


# ### TF-IDF
# #### ????????(????, ????) = ????????????????(????, ????) ?? (????????????_????)
# #### ????????????(????) = ????????????__2 (???? ?? ????_????)


# In[11]:


def tf_idf(split_query, document_id):
    score = 0  

    if document_id == 0:
        print("error in tf-idf function")
        return

    for term in split_query:
        if term not in inv_idx:
            continue
        score += (inv_idx[term][document_id] / wiki_dataframe['most_frequent_term'][document_id - 1][0][1]) * math.log(
            (len(wiki_dataframe) / len(inv_idx[term])), 2)
    return score


# ### Ranking candidate resources

# In[9]:


def rank_candidate_resources(query, candidate_resources, n):
    print("Ranking Candidate Resources...")
    ranked_candidates = {}
    for document_id in candidate_resources:
        print(".", end="")
        ranked_candidates[document_id] = tf_idf(query.split(), document_id) / n

    return sorted(ranked_candidates.items(), key=lambda item: item[1], reverse=True)


# In[26]:


def find_and_rank_candidate_resources(query):
    candidates, n = identify_candidate_resources(query)
    return rank_candidate_resources(query, candidates, n)


# ### Snippet Generation

# In[27]:

def get_snippet(query, document_id):
    row = wiki_dataframe[wiki_dataframe['id'] == document_id]
    snippet = (  # tuple in the form (title, sentences)
        row["title"].to_string(index=False),
        generate_sentence_snippets(query, document_id, int(row["title"].str.len())))
    return snippet


# In[23]:

def generate_sentence_snippets(query, document_id, len_title):
    pattern = '(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'
    top_two = []  # format is (sentence, cosine_similarity_score)
    vectorized_query = vectorize(query, document_id)
    for sentence in re.split(pattern, wiki_dataframe["content"][document_id - 1][len_title:]):
        sentence = sentence.replace("\r", "").replace("\n", "")  # 4 is for removal of \r\n\r\n for each sentence.
        lsentence = sentence.lower()

        sentence_score = cosine_similarity(query, lsentence, document_id)
        if len(top_two) < 2:
            top_two.append((sentence, sentence_score))
            top_two.sort(key=lambda item: item[1], reverse=True)
            continue

        for index, entry in enumerate(top_two):  # this loop should only run twice
            if sentence_score > entry[1]:
                top_two[index] = (sentence, sentence_score)
                top_two.sort(key=lambda item: item[1], reverse=True)
                break

    if len(top_two) < 2:
        result = (top_two[0][0], '')
    else:
        result = (top_two[0][0], top_two[1][0])
    return result


# In[ ]:


def vectorize(phrase, document_id):
    arr = []
    for word in phrase.split():
        arr.append(tf_idf([word], document_id))
    return arr


# In[33]:


def cosine_similarity(query, sentence, doc_id):
    colab_sent = set(query.split()).union(sentence.translate(string.punctuation).split())
    vectorized_query = []
    vectorized_sentence = []
    for word in colab_sent:
        if word in query:
            vectorized_query.append(tf_idf([word], doc_id))
        else:
            vectorized_query.append(0)
        if word in sentence:
            vectorized_sentence.append(tf_idf([word], doc_id))
        else:
            vectorized_sentence.append(0)
    return 1 - spatial.distance.cosine(list(vectorized_sentence), list(vectorized_query))


# ### Putting Everything together

# In[ ]:


def output_to_file(document_id):
    filename = 'output/output-' + str(document_id) + '.txt'
    file = open(filename, 'w+')
    file.write("Title: " + wiki_dataframe['content'][document_id - 1] + "\n")
    file.close()
    return filename


# In[ ]:

# lemmatization, lowercase, remove non alpha, remove non-english, remove numbers and stopword removal
rejected_content = []


def preprocess_query(query):
    filtered_content = []
    for token in nltk.word_tokenize(query):
        token = lemmatizer.lemmatize(token).lower()
        if names.search_first_name(token) or names.search_last_name(token) or (
                (token in lower_cased_words) and (token not in stop_words) and (token.isalpha())):
            filtered_content.append(token)
        else:
            rejected_content.append(token)

    return ' '.join(filtered_content)


def search(query):
    processed_query = preprocess_query(query)
    print("Generating results...")
    if processed_query:
        ranked_candidate_resources = find_and_rank_candidate_resources(processed_query)[0:10]
    else:
        ranked_candidate_resources = []
    search_results = []
    query_suggestions = []
    for resource in ranked_candidate_resources:
        title, sentences = get_snippet(processed_query, resource[0])
        search_results.append([resource[0], title, sentences, resource[1]])
    ranked_candidate_queries = find_rank_candidate_queries(query)
    for query_suggestion in ranked_candidate_queries[0:5]:
        query_suggestions.append(query_suggestion)
    return search_results, query_suggestions


if __name__ == '__main__':
    search_results, query_suggestions = search("sex")
    print("results:")
    print(search_results)
