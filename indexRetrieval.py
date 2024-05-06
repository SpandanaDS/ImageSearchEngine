import streamlit as st
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.query import And, Term, Every
from whoosh.analysis import StemmingAnalyzer
from collections import Counter
import math
import json

# Define a custom QueryParser class for correct tokenization and matching
class CustomQueryParser(QueryParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, query_string, normalize=True):
        stem_analyzer = StemmingAnalyzer()
        tokens = [token.text for token in stem_analyzer(query_string)]
        return Every(self.fieldname) if not tokens else And([Term(self.fieldname, token) for token in tokens])


# Function to load images data from JSON file
def load_images_data(json_file):
    with open(json_file, 'r') as f:
        images_data = json.load(f)
    return images_data

def calculate_relevance_score(result, query, textual_surrogates):
    textual_surrogate = textual_surrogates[result['image_id']]['textual_surrogate']
    tokens_query = query.split()
    tokens_textual_surrogate = textual_surrogate.split() if isinstance(textual_surrogate, str) else []
    
    # Calculate relevance score based on the number of common tokens
    relevance_score = len(set(tokens_query) & set(tokens_textual_surrogate))
    return relevance_score

# Streamlit web interface
st.title("Image Search Engine")

# Input query from user
query_str = st.text_input("Enter your search query:")

# Create or open the index directory
index_dir = "image_index"
ix = open_dir(index_dir)

if st.button("Search"):
    # Parse the query with the custom QueryParser
    query_parser = CustomQueryParser("textual_surrogate", schema=ix.schema)
    query = query_parser.parse(query_str)

    # Search the index
    searcher = ix.searcher()
    results = searcher.search(query, limit=None)

    # Load textual surrogates
    textual_surrogates = load_images_data('textual_surrogates.json')
    
    # Calculate relevance scores for each result
    relevance_scores = {result['image_id']: calculate_relevance_score(result, query_str, textual_surrogates) for result in results}
    
    # Sort results by relevance score
    sorted_results = sorted(results, key=lambda result: relevance_scores[result['image_id']], reverse=True)

    # Display search results in a grid layout
    st.write(f"Total Results: {len(sorted_results)}")
    cols = st.columns(3)  # Adjust the number of columns as needed
    for i, result in enumerate(sorted_results):
        with cols[i % 3]:
            st.image(result['url'])
    
    # Close the searcher
    searcher.close()
