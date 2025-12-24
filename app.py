from flask import Flask, render_template, request, jsonify
import pickle
import json
import numpy as np
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Load Data
try:
    with open('movies.json', 'r') as f:
        movies_list = json.load(f) # List of dicts: {'id': 0, 'title': 'Avatar'}
        # Create a quick lookup dictionary
        movies_lookup = {m['title'].lower(): m['id'] for m in movies_list}
        movies_by_index = {m['id']: m['title'] for m in movies_list}

    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    print("Error: Data files not found.")
    movies_list = []
    movies_lookup = {}
    similarity = None

# Helper to fetch poster
def fetch_poster(title):
    api_key = "f49e77fe" 
    url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get('Poster') and data.get('Poster') != "N/A":
            return data.get('Poster')
    except:
        pass
    return "https://via.placeholder.com/500x750/111111/333333?text=No+Preview"

@app.route('/')
def index():
    # Pass just the titles for the autocomplete/dropdown
    titles = [m['title'] for m in movies_list]
    return render_template('index.html', movie_titles=titles)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    movie_name = data.get('movie')
    
    if not movie_name or movie_name.lower() not in movies_lookup:
        return jsonify({'error': 'Movie not found'}), 404

    try:
        idx = movies_lookup[movie_name.lower()]
        
        # Get similarity scores
        distances = similarity[idx]
        
        # Get top 5 recommendations (skip the first one as it is the movie itself)
        # We use argpartition for efficiency if array is large, or just sort
        # Since it's 4800, sort is fast enough.
        # Enumerate to keep index: (index, score)
        movie_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        recommendations = []
        titles_to_fetch = []
        
        for i in movie_indices:
            movie_idx = i[0]
            title = movies_by_index[movie_idx]
            titles_to_fetch.append(title)
            
        # Fetch posters in parallel
        with ThreadPoolExecutor() as executor:
            posters = list(executor.map(fetch_poster, titles_to_fetch))
            
        for i, title in enumerate(titles_to_fetch):
            recommendations.append({
                'title': title,
                'poster': posters[i],
                'search_url': f"https://www.google.com/search?q={urllib.parse.quote(title + ' movie')}"
            })
            
        return jsonify(recommendations)
        
    except Exception as e:
        print(e)
        return jsonify({'error': 'Something went wrong'}), 500

if __name__ == '__main__':
    app.run(debug=True)
