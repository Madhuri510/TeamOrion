
#--------------------------------Import Libraries--------------------------------------#
import streamlit as st
import requests
from pyvis.network import Network
import streamlit.components.v1 as components
import openai
import os
from neo4j import GraphDatabase
import numpy as np
import re
import subprocess
import json
from PIL import Image
import base64
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import spacy

#Import Package
nlp = spacy.load("en_core_web_sm")

#Store Responses
if "response_history" not in st.session_state:
    st.session_state["response_history"] = []

#------------------------- Environment Variables ------------------------------------#
# Load sensitive information securely from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")  
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "gf6xb4kgeZKSS8p")

# Initialize Neo4j driver
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Load and encode the Orion Belt background image
image_path = "/Users/vedant/LLM Project 690/Streamlit app/Orion_Belt1.jpg"  # Replace with the path to your image file
orion_image = Image.open(image_path)


#----------------------------------- Store History -------------------------------------#
@st.cache_data
def get_base64_of_bin_file(image):
    with open(image, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache_data
def cached_neo4j_data(query):
    return get_neo4j_data(query)

# Encode the image as a base64 string
orion_base64 = get_base64_of_bin_file(image_path)


#-------------------------------- Theme & Styling ----------------------------------------#
# Custom CSS for styling
st.markdown(
    """
    <style>
    .centered-content {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    /* Flex container for input and button */
    .input-container {
        display: flex;
        align-items: center;
        gap: 10px;
        max-width: 600px;
        width: 100%;
    }

    /* Styling for the input box */
    input[type="text"] {
        flex: 1;
        padding: 12px;
        font-size: 16px;
        border-radius: 25px;
        background-color: #333333;
        border: none;
        color: white;
    }
    input[type="text"]::placeholder {
        color: #8F8F8F;
    }

    /* Styling for the submit button */
    .submit-btn {
        padding: 12px 20px;
        font-size: 16px;
        border-radius: 25px;
        background-color: #1a73e8;
        color: white;
        border: none;
        cursor: pointer;
    }
    .submit-btn:hover {
        background-color: #145dbf;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header with Team Title and Background Image
st.markdown(
    f"""
    <div style="
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        color: white;
        padding: 20px;
        background-image: url('data:image/jpg;base64,{orion_base64}');
        background-size: cover;
        background-position: left;
        border-radius: 8px;
        margin-top: -30px;
    ">
        TEAM ORION ✨
    </div>
    """,
    unsafe_allow_html=True
)


#------------------Prreprocess Queries to extract cypher queries into summaries----------------------------#

def extract_entities(user_query):
    """Extract entities from user input using NLP."""
    doc = nlp(user_query)
    entities = [ent.text for ent in doc.ents] + [chunk.text for chunk in doc.noun_chunks]
    return list(set(entities))

def generate_combined_cypher_query(entities):
    """Generate a Cypher query dynamically based on extracted entities."""
    entity_conditions = " OR ".join([f"n.id = '{entity}'" for entity in entities])
    query = f"""
    MATCH (n:Entity)-[r]-(related)
    WHERE {entity_conditions}
    RETURN n.id AS source_id, type(r) AS relationship, related.id AS target_id
    """
    return query

def fetch_neo4j_results(query):
    """Fetch results from the Neo4j database for the given query."""
    with neo4j_driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

def summarize_results(results):
    """Summarize the results from Neo4j into a structured format."""
    summary = []
    for record in results:
        summary.append({
            "source_id": record.get('source_id', ''),
            "relationship": record.get('relationship', ''),
            "target_id": record.get('target_id', '')
        })
    return summary

def process_user_query(user_query):
    """Process the user query by extracting entities, fetching data, and summarizing results."""
    try:
        # Step 1: Extract entities
        entities = extract_entities(user_query)
        if not entities:
            raise ValueError("No entities found in the user query.")
        print("Extracted Entities:", entities)

        # Step 2: Generate Cypher query
        cypher_query = generate_combined_cypher_query(entities)
        print("Generated Cypher Query:", cypher_query)

        # Step 3: Fetch and summarize Neo4j results
        results = fetch_neo4j_results(cypher_query)
        if not results:
            return "No results found in the database."
        summarized_data = summarize_results(results)
        return summarized_data

    except ValueError as ve:
        print(f"Error: {ve}")
        return str(ve)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return str(e)



# --------------------------------- LLM Functions ------------------------------------ #
# Define the function for OpenAI response
def get_answer_from_openai(neo4j_context, user_query):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant with access to Neo4j graph data."},
            {"role": "user", "content": f"Using the following graph data:\n{neo4j_context} and your own knowledge\n\nAnswer the query: '{user_query}'"}
        ],
        max_tokens=1500,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None,
    )

    # Stream and collect the completion response
    full_response = ""
    for chunk in response:
        if 'content' in chunk['choices'][0]['delta']:
            content = chunk['choices'][0]['delta']['content']
            full_response += content  # Collect the response for further use if needed
    return full_response


def escape_special_characters(text):
    # Escape single quotes and handle parentheses as needed for shell compatibility
    text = text.replace("'", "\\'")
    text = re.sub(r"[()]", "", text)
    return text

def get_answer_from_llama(neo4j_context, user_query):
    # Escape special characters in the graph data and query
    safe_neo4j_context = escape_special_characters(neo4j_context)
    safe_user_query = escape_special_characters(user_query)
    
    # Create the combined prompt
    full_prompt = f"Using the following graph data:\n{safe_neo4j_context} and your own knowledge\n\nAnswer the query: '{safe_user_query}'"
    
    # Run the command and capture output
    command = f"echo \"{full_prompt}\" | ollama run llama3.2"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Check for any errors
    if result.stderr:
        print("Error:", result.stderr)
    else:
        print("Output:", result.stdout)
    
    return result.stdout.strip()

def get_answer_from_meditron(neo4j_context, user_query):
    safe_neo4j_context = escape_special_characters(neo4j_context)
    safe_user_query = escape_special_characters(user_query)
    full_prompt = f"Using the following graph data:\n{safe_neo4j_context}  and your own knowledge\n\nAnswer the query: '{safe_user_query}'"
    command = f"echo \"{full_prompt}\" | ollama run meditron:latest"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stderr:
        print("Error:", result.stderr)
    return result.stdout.strip()

def get_answer_from_biomistral(neo4j_context, user_query):
    safe_neo4j_context = escape_special_characters(neo4j_context)
    safe_user_query = escape_special_characters(user_query)
    full_prompt = f"Using the following graph data:\n{safe_neo4j_context}  and your own knowledge\n\nAnswer the query: '{safe_user_query}'"
    command = f"echo \"{full_prompt}\" | ollama run cniongolo/biomistral:latest"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stderr:
        print("Error:", result.stderr)
    return result.stdout.strip()

def get_answer_from_medllama2(neo4j_context, user_query):
    safe_neo4j_context = escape_special_characters(neo4j_context)
    safe_user_query = escape_special_characters(user_query)
    full_prompt = f"Using the following graph data:\n{safe_neo4j_context}  and your own knowledge\n\nAnswer the query: '{safe_user_query}'"
    command = f"echo \"{full_prompt}\" | ollama run medllama2:latest"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stderr:
        print("Error:", result.stderr)
    return result.stdout.strip()




# ----------------------------------------- Sidebar for Model Selection ------------------------------------- #
st.sidebar.header("Model Selection")
model_choice = st.sidebar.radio(
    "Choose the model to use:",
    ("OpenAI GPT-4-turbo", "Llama 3.2", "Meditron", "BioMistral", "MedLlama2")
)


# ----------------------------------------Page heading ---------------------------------------------- #
st.markdown("<h1 style='text-align: center; color: #e2dddf;'>Knowledge Graph and LLM Query Interface</h1>", unsafe_allow_html=True)

# Centered input and button
st.markdown("<div class='centered-content'>", unsafe_allow_html=True)
st.markdown("<div class='input-container'>", unsafe_allow_html=True)

# Input field and submit button in flex layout
user_query = st.text_input("Enter your query:", placeholder="Type your query here...", label_visibility="collapsed", key="user_query_input")


# ----------------------------------------------------- Submit --------------------------------------------- #

if st.button("🚀 Submit Query", key="submit_query"):
    if user_query:
        try:
            # Process the user query
            summarized_data = process_user_query(user_query)

            if isinstance(summarized_data, str):  # Handle error message
                st.write(summarized_data)
            else:
                # Format the summarized data for display or prompt usage
                formatted_context = "\n".join([
                    f"{record['source_id']} -[{record['relationship']}]-> {record['target_id']}"
                    for record in summarized_data
                ])
                st.write("Formatted Context from Summarized Results:")
                st.write(formatted_context)

                # Use the formatted context in a prompt
                if model_choice == "OpenAI GPT-4-turbo":
                    answer = get_answer_from_openai(formatted_context, user_query)
                elif model_choice == "Llama 3.2":
                    answer = get_answer_from_llama(formatted_context, user_query)
                elif model_choice == "Meditron":
                    answer = get_answer_from_meditron(formatted_context, user_query)
                elif model_choice == "BioMistral":
                    answer = get_answer_from_biomistral(formatted_context, user_query)
                elif model_choice == "MedLlama2":
                    answer = get_answer_from_medllama2(formatted_context, user_query)

                # Display the result
                st.subheader(f"Generated Response (Model: {model_choice})")
                st.write(f"**Query:** {user_query}")
                st.write(answer)

                # Add the new query and response to the session state
                st.session_state.response_history.append({
                    "query": user_query,
                    "response": answer
                })

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a query to get a response.")
st.markdown("</div></div>", unsafe_allow_html=True)  # Close input-container and centered-content divs


# ------------------------------------------ Sidebar History --------------------------------------- #
st.sidebar.subheader("📜 Response History")
if st.session_state.response_history:
    for i, entry in enumerate(st.session_state.response_history):
        if st.sidebar.button(f"View Response {i+1}: {entry['query'][:20]}..."):
            st.subheader("**Query**")
            st.write(entry['query'])
            st.subheader("**Generated Response**")
            st.write(entry['response'])



# ------------------------------------------- Footer ------------------------------------------- #
st.markdown("<hr style='border:1px solid #b97bff'>", unsafe_allow_html=True)
st.markdown("<footer style='text-align: center; color: #888;'>Made with ❤️ using Streamlit</footer>", unsafe_allow_html=True)