#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import nltk
import pickle5 as pickle
import math
import re
from tqdm import tqdm
from nltk.stem import WordNetLemmatizer
from names_dataset import NameDatasetV1  # v1
from nltk.corpus import stopwords
from itertools import combinations
from scipy import spatial

nltk.download('all')

# ## Reading File and creating DataFrame

# In[ ]:


lemmatizer = WordNetLemmatizer()
names = NameDatasetV1()
stop_words = set(stopwords.words('english'))

# In[ ]:


tqdm.pandas()


# In[ ]:


def load_files():
    print("loading files...")
    with open("./data/wiki_dataframe_augmented_nltk_corpus_to_remove_non-english.pkl", "rb") as wiki_df:
        wiki_dataframe = pickle.load(wiki_df)
    inv_idx = pickle.load(open("./data/inv_idx_augmented_nltk_corpus_to_remove_non-english.pkl", "rb"))
    aol_query_log = pickle.load(open("./data/aol_query_log_data.pkl", "rb"))
    print("Done!")
    return [wiki_dataframe, inv_idx, aol_query_log]


wiki_dataframe, inv_idx, aol_query_log = load_files()


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


aol_queries = aol_query_log['Processed Query'].values


def identify_candidate_queries(query):
    print("Identifying Candidate Queries...")
    candidate_queries = set()
    for aol_query in aol_queries:
        print(".", end="")
        if len(aol_query.split()) > len(query.split()):
            if aol_query.startswith(query):
                candidate_queries.add(aol_query)
    print("Done!")
    return candidate_queries


# #### Ranking Candidate Suggestions
# ##### 𝑆𝑐𝑜𝑟𝑒(𝐶𝑄, 𝑞′) = \# 𝑜𝑓 𝑠𝑒𝑠𝑠𝑖𝑜𝑛𝑠 𝑖𝑛 𝑤ℎ𝑖𝑐ℎ 𝑞 𝑖𝑠 𝑚𝑜𝑑𝑖𝑓𝑖𝑒𝑑 𝑡𝑜 𝐶𝑄 ÷ \# 𝑜𝑓 𝑠𝑒𝑠𝑠𝑖𝑜𝑛𝑠 𝑖𝑛 𝑤ℎ𝑖𝑐ℎ 𝑞 𝑎𝑝𝑝𝑒𝑎𝑟𝑠

# In[ ]:


def rank_candidate_queries(original_query, candidates):
    print("Ranking Candidate Queries")
    candidate_scores = []
    num_sessions_containing_q = 0
    sessions_with_original_query = set(aol_query_log[aol_query_log['Query'] == original_query]['AnonID'])
    # print(sessions_with_original_query)
    # return sessions_with_original_query 
    num_sessions_containing_q = len(sessions_with_original_query)

    for candidate in tqdm(candidates):  # cut off at certain number of candidates?
        print(".", end="")
        sessions_with_candidate_query = set(aol_query_log[aol_query_log['Query'] == candidate]['AnonID'])
        sessions_with_both_queries = sessions_with_original_query & sessions_with_candidate_query
        if num_sessions_containing_q != 0:
            candidate_scores.append((candidate, len(sessions_with_both_queries) / num_sessions_containing_q))

    for candidate in candidates:  # supplementing the final list if the ranked results dont equal five
        if len(candidate_scores) >= 5:
            break
        candidate_scores.append((candidate, 0))  # candidate score of 0 is default rank
    return sorted(candidate_scores, key=lambda candidate_score: candidate_score[1], reverse=True)


# In[ ]:


def find_rank_candidate_queries(query):
    candidate_list = identify_candidate_queries(query)
    return rank_candidate_queries(query, candidate_list)


# ## Relevance Ranking

# ### Identifying Candidate Resources

# In[6]:


def identify_candidate_resources(query):
    print("Identifying Candidate Resources...")
    results = set()
    split_query = query.split()
    n = len(split_query)
    candidate_list = list()
    for term in split_query:
        print(".", end="")
        if len(inv_idx[term]) > 0:
            candidate_list.append(set(inv_idx[term].keys()))
    if len(candidate_list) > 0:
        results = set.intersection(*candidate_list)
    if len(results) <= 50:
        for combination in combinations(split_query, n - 1):
            print(".", end="")
            candidate_list = list()
            for term in combination:
                candidate_list.append(inv_idx[term])
            if len(candidate_list) > 0:
                results = set.intersection(*candidate_list)
            if len(results) > 50:
                break
            else:
                n -= 1
    return results


# ### TF-IDF
# #### 𝑇𝐹(𝑤, 𝑑) = 𝑓𝑟𝑒𝑞(𝑤, 𝑑) ÷ (𝑚𝑎𝑥_𝑑)
# #### 𝐼𝐷𝐹(𝑤) = 𝑙𝑜𝑔__2 (𝑁 ÷ 𝑛_𝑤)


# In[11]:


def tf_idf(split_query, document_id):
    score = 0
    for term in split_query:
        score += (inv_idx[term][document_id] / wiki_dataframe['most_frequent_term'][document_id - 1][0][1]) * math.log(
            (len(wiki_dataframe) / len(inv_idx[term])), 2)
    return score


# ### Ranking candidate resources

# In[9]:


def rank_candidate_resources(query, candidate_resources):
    print("Ranking Candidate Resources...")
    ranked_candidates = {}
    for document_id in candidate_resources:
        print(".", end="")
        ranked_candidates[document_id] = tf_idf(query.split(), document_id)
    return sorted(ranked_candidates.items(), key=lambda item: item[1], reverse=True)


# In[26]:


def find_and_rank_candidate_resources(query):
    candidates = identify_candidate_resources(query)
    return rank_candidate_resources(query, candidates)


# ### Snippet Generation

# In[27]:

def get_snippet(query, document_id):
    row = wiki_dataframe[wiki_dataframe['id'] == document_id + 1]
    snippet = (  # tuple in the form (title, sentences)
        row["title"].to_string(index=False),
        generate_sentence_snippets(query, document_id, int(row["title"].str.len())))
    return snippet


# In[23]:

def generate_sentence_snippets(query, document_id, len_title):
    pattern = '(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'
    top_two = []  # format is (sentence, cosine_similarity_score)
    vectorized_query = vectorize(query, document_id)
    for sentence in re.split(pattern, wiki_dataframe["content"][document_id][len_title:]):
        sentence = sentence.rstrip()[4:]  # 4 is for removal of \r\n\r\n for each sentence.
        lsentence = sentence.lower()

        sentence_score = cosine_similarity(vectorized_query, vectorize(lsentence, document_id))
        if len(top_two) < 2:
            top_two.append((sentence, sentence_score))
            top_two.sort(key=lambda item: item[1], reverse=True)
            continue

        for index, entry in enumerate(top_two):  # this loop should only run twice
            if sentence_score > entry[1]:
                top_two.insert(index, (sentence, sentence_score))
                continue
    return top_two[0][0], top_two[1][0]


# In[ ]:


def vectorize(phrase, document_id):
    arr = []
    for word in phrase.split():
        arr.append(tf_idf([word], document_id))
    return arr


# In[33]:


def cosine_similarity(vectorized_query, vectorized_sentence):
    lenf = max(len(vectorized_query), len(vectorized_sentence))
    for i in range(lenf + 1):
        if len(vectorized_query) == len(vectorized_sentence):
            break
        if len(vectorized_query) < i:
            vectorized_query.append(0.001)
        if len(vectorized_sentence) < i:
            vectorized_sentence.append(0.001)
    return 1 - spatial.distance.cosine(list(vectorized_sentence), list(vectorized_query))


# ### Putting Everything together

# In[ ]:


def search(query):
    print("Generating results...")
    ranked_candidate_resources = find_and_rank_candidate_resources(query)
    results = {}
    for resource in ranked_candidate_resources[:10]:
        print("resource", resource)
        title, sentences = get_snippet(query, resource[0])
        results[resource] = [title, sentences]
    ranked_candidate_queries = find_rank_candidate_queries(query)
    results["query_suggestions"] = []
    for query_suggestion in ranked_candidate_queries[:5]:
        results["query_suggestions"].append(query_suggestion[0])

    return results


search("sex")
