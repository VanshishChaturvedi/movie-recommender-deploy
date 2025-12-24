import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem.porter import PorterStemmer
import pickle

def convert(obj):
    result = []
    for i in ast.literal_eval(obj):
        result.append(i["name"])
    return result

def convert3(obj):
    result = []
    counter = 0
    for i in ast.literal_eval(obj):
        if counter < 3:
            result.append(i["name"])
            counter += 1
        else:
            break
    return result

def fetch_director(obj):
    result = []
    for i in ast.literal_eval(obj):
        if i["job"] == "Director":
            result.append(i["name"])
            break
    return result

def stem(text):
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

print("Loading data...")
movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')

print("Renaming columns...")
movies.rename(columns={'id': 'movie_id'}, inplace=True)

print("Merging data...")
movies = movies.merge(credits, on=['movie_id', 'title'])

print("Selecting columns...")
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]

print("Dropping nulls...")
movies.dropna(inplace=True)

print("Processing columns...")
movies['genres'] = movies['genres'].apply(convert)
movies['keywords'] = movies['keywords'].apply(convert)
movies['cast'] = movies['cast'].apply(convert3)
movies['crew'] = movies['crew'].apply(fetch_director)

movies['overview'] = movies['overview'].apply(lambda x: x.split())
movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['cast'] = movies['cast'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['crew'] = movies['crew'].apply(lambda x: [i.replace(" ", "") for i in x])

movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']

new_df = movies[['movie_id', 'title', 'tags']]
new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
new_df['tags'] = new_df['tags'].apply(lambda x: x.lower())

print("Stemming tags...")
ps = PorterStemmer()
new_df['tags'] = new_df['tags'].apply(stem)

print("Vectorizing...")
cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tags']).toarray()

print("Calculating similarity...")
similarity = cosine_similarity(vectors)

print("Saving pickle files...")
pickle.dump(new_df, open('movies.pkl', 'wb'))
pickle.dump(similarity, open('similarity.pkl', 'wb'))

print("Done!")
