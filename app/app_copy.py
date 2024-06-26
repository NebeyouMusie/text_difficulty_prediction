# Import necessary libraries
import streamlit as st
import requests
import os
import transformers
import sentencepiece 
#try:
    #import sentencepiece
    #st.success('SentencePiece is successfully imported!')
#except ImportError as e:
    #st.error(f'Failed to import SentencePiece: {e}')
import torch
from transformers import CamembertTokenizer, CamembertForSequenceClassification, pipeline
import tokenizers
import streamlit.components.v1 as components
import traceback
from itertools import cycle  


# Initialize user data and levels
cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
default_user_data = {'default_user': {'level': 'A1', 'feedback_points': 0}}

# Function to ensure that user data is initialized in session state
def ensure_user_data():
    if 'users' not in st.session_state:
        st.session_state['users'] = default_user_data.copy()


# Fetch news articles from MediaStack
mediastack_api_key = '2ecbc982b44e1ae0338fb33482fe8813'
base_url = "http://api.mediastack.com/v1/news"
        
# Fetch news articles from mediastack API
def fetch_news(category):
    params = {
        'access_key': mediastack_api_key,
        'languages': "fr",
        'categories': category,
        'limit': 3  
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()['data']
    else:
        st.error('Failed to retrieve news articles.')
        return []

# Function to check if the image URL is valid
def is_valid_image_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200 and 'image' in response.headers['Content-Type']
    except requests.RequestException:
        return False



# Dummy function to assign levels to articles
def assign_article_levels(articles):
    level_cycle = cycle(cefr_levels)  # Create a cycle iterator from CEFR levels
    valid_articles = [article for article in articles if is_valid_image_url(article['image'])]
    for article in valid_articles:
        article['level'] = next(level_cycle)  # Assign levels in a cyclic manner
    return valid_articles



# Function to update user level based on feedback
def update_user_level(user_id, feedback):
    # Make sure user data is available
    ensure_user_data()

    # Access the user data safely from session state
    feedback_points = {'Too Easy': 1, 'Just Right': 0.5, 'Challenging': 0.5, 'Too Difficult': -1}
    user_data = st.session_state['users'][user_id]
    user_data['feedback_points'] += feedback_points[feedback]
    
    # Thresholds for level change
    upgrade_threshold = 3 # Points needed to move up a level
    downgrade_threshold = -3 # Points needed to move down a level

    # Accessing CEFR levels
    current_index = cefr_levels.index(user_data['level'])

    # Level Change
    if user_data['feedback_points'] >= upgrade_threshold:
        new_index = min(current_index + 1, len(cefr_levels) - 1)
        user_data['level'] = cefr_levels[new_index]
        user_data['feedback_points'] = 0 # Reset points after level change
    elif user_data['feedback_points'] <= downgrade_threshold:
        new_index = max(current_index - 1, 0)
        user_data['level'] = cefr_levels[new_index]
        user_data['feedback_points'] = 0 # Reset points after level change

    # Update the user data in session state
    st.session_state['users'][user_id] = user_data
        
    return user_data['level']



        
def main():

    if 'start' not in st.session_state:
        st.session_state['start'] = False  # This keeps track of whether the user has started the app
    
    if not st.session_state['start']:
        st.title('')
        st.title('')
        st.title('')
        st.markdown("<style>div.row-widget.stButton > button:first-child {margin: 0 auto; display: block;}</style>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            left_co, cent_co,last_co = st.columns(3)
            with cent_co:
                st.image("https://raw.githubusercontent.com/vgentile98/text_difficulty_prediction/main/app/baguette_logo.png")
            st.markdown("<h1 style='text-align: center; color: black;'>From 'Oui Oui' to Fluent</h1>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: black;'>Start your journey to master French now</h4>", unsafe_allow_html=True)
            if st.button("Je commence!"):
                st.session_state['start'] = True
                st.session_state['initial_assessment'] = True

    # Initial Assessment
    elif st.session_state.get('initial_assessment', False):
        st.title('Initial French Level Assessment')
        st.write("Select the most difficult sentence you understand:")

        sentences = [
            ("Le restaurant 'Bon appétit' recherche des serveurs pour l'été.", 'A1'),
            ("Chaque année, l'humanité consomme plus de ressources que la Terre ne peut en produire en un an.", 'A2'),
            ("Lorsqu'il y a un éclair avec des nuages et de la pluie, il risque d'y avoir de la foudre et du tonnerre.", 'B1'),
            ("Tous ces bouleversements impliquent des conséquences tragiques comme l'augmentation de l'effet de serre et le réchauffement climatique.", 'B2'),
            ("L'obésité frappe également l'Afrique subsaharienne, où vivent la plupart des populations sous-alimentées du monde (12,1 %), et l'Egypte (33%).", 'C1'),
            ("Auparavant, la duplication de l'ADN se faisait par clonage moléculaire : la séquence d'intérêt était insérée dans le génome d'une bactérie et l'on se servait du taux de croissance élevé du micro-organisme pour obtenir autant de clones de la séquence d'ADN.", 'C2')
        ]

        for idx, (sentence, level) in enumerate(sentences):
            if st.button(sentence, key=f"assessment_{idx}"):
                user_id = 'default_user'
                ensure_user_data()
                st.session_state['users'][user_id]['level'] = level
                st.session_state['initial_assessment'] = False
                
    else:
        st.title('Curated articles just for you')
        st.subheader('Read, learn, and grow at your own pace!')

        category = st.selectbox("What do you want to read about?", ['general', 'business', 'technology', 'entertainment', 'sports', 'science', 'health'], index=1)
        st.markdown("---")

        with st.sidebar:
            logo_url = "https://raw.githubusercontent.com/vgentile98/text_difficulty_prediction/main/app/baguette_logo.png"
            st.image(logo_url, width=200)
            user_id = 'default_user'
            ensure_user_data()
            user_level = st.session_state['users'][user_id]['level']
            st.subheader(f"Your current level: {user_level}")
            
        ensure_user_data()
    
        user_id = 'default_user'    
        user_level = st.session_state['users'][user_id]['level']

        articles = fetch_news(category)
        if articles:
            articles = assign_article_levels(articles)
            articles = [article for article in articles if article['level'] == user_level and is_valid_image_url(article['image'])]
            for idx, article in enumerate(articles):
                with st.container():
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.image(article['image'], width=300)
                    with col2:
                        st.markdown(f"<div style='border: 1px solid gray; border-radius: 4px; padding: 10px; text-align: center;'><strong>{article['level']}</strong></div>", unsafe_allow_html=True)
                    st.subheader(article['title'])
                    st.write(article['description'])
                    with st.expander("Read Now"):
                        components.iframe(article['url'], height=450, scrolling=True)
                        cols = st.columns(4)
                        feedback_options = ['Too Easy', 'Just Right', 'Challenging', 'Too Difficult']
                        for i, option in enumerate(feedback_options):
                            if cols[i].button(option, key=f"feedback_{idx}_{i}"):
                                new_level = update_user_level(user_id, option)
                                st.session_state['users'][user_id]['level'] = new_level
                                st.experimental_rerun()
                    st.markdown("---")
        else:
            st.write("No articles found. Try adjusting your filters.")


if __name__ == '__main__':
    main()
