import pickle
import json
import pandas as pd
import numpy as np

# Load existing data
print("Loading movies.pkl...")
movies_dict = pickle.load(open('movies.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

# Create a simplified list of movies for the frontend/backend
# We only need title and original_index (to look up in similarity matrix)
movie_list = []
for index, row in movies.iterrows():
    movie_list.append({
        "id": index, # This is the row index in the similarity matrix
        "title": row['title']
    })

print(f"Converting {len(movie_list)} movies to JSON...")
with open('movies.json', 'w') as f:
    json.dump(movie_list, f)

print("Verifying similarity.pkl size...")
# It should already be float16 from previous step
sim = pickle.load(open('similarity.pkl', 'rb'))
print(f"Similarity matrix shape: {sim.shape}, dtype: {sim.dtype}")

print("Done.")
