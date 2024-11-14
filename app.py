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

if "response_history" not in st.session_state:
    st.session_state["response_history"] = []

# Load sensitive information securely from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")  
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Load and encode the Orion Belt background image
image_path = "/Users/vedant/LLM Project 690/Streamlit app/Orion_Belt1.jpg"  # Replace with the path to your image file
orion_image = Image.open(image_path)

@st.cache_data
def get_base64_of_bin_file(image):
    with open(image, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Encode the image as a base64 string
orion_base64 = get_base64_of_bin_file(image_path)

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

def get_neo4j_data(query, parameters=None):
    with neo4j_driver.session() as session:
        result = session.run(query, parameters)
        return [record.data() for record in result]

# Define your Neo4j query
neo4j_query = """
MATCH (n)-[r]->(m)
RETURN n.id AS source_id, n.type AS source_type, type(r) AS relationship, m.id AS target_id, m.type AS target_type
LIMIT 400
"""

# Retrieve data from Neo4j
neo4j_data = get_neo4j_data(neo4j_query)

neo4j_context = "\n".join([
    f"{record['source_id']} ({record['source_type']}) -[{record['relationship']}]-> {record['target_id']} ({record['target_type']})"
    for record in neo4j_data
])


# Define the function for OpenAI response
def get_answer_from_openai(neo4j_context, user_query):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant with access to Neo4j graph data."},
            {"role": "user", "content": f"Using the following graph data:\n{neo4j_context}\n\n{user_query}"}
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
    full_prompt = f"Using the following graph data:\n{safe_neo4j_context}\n\nAnswer the query: '{safe_user_query}'"
    
    # Run the command and capture output
    command = f"echo \"{full_prompt}\" | ollama run llama3.2"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Check for any errors
    if result.stderr:
        print("Error:", result.stderr)
    else:
        print("Output:", result.stdout)
    
    return result.stdout.strip()

# Sidebar for Model Selection
st.sidebar.header("Model Selection")
model_choice = st.sidebar.radio("Choose the model to use:", ("OpenAI GPT-4-turbo", "Llama 3.2"))


# Page heading
st.markdown("<h1 style='text-align: center; color: #e2dddf;'>Knowledge Graph and LLM Query Interface</h1>", unsafe_allow_html=True)

# Centered input and button
st.markdown("<div class='centered-content'>", unsafe_allow_html=True)
st.markdown("<div class='input-container'>", unsafe_allow_html=True)

# Input field and submit button in flex layout
user_query = st.text_input("Enter your query:", placeholder="Type your query here...", label_visibility="collapsed", key="user_query_input")
if st.button("🚀 Submit Query", key="submit_query"):
    if user_query:
        # Call the appropriate model based on user selection
        if model_choice == "OpenAI GPT-4-turbo":
            answer = get_answer_from_openai(neo4j_context, user_query)
        elif model_choice == "Llama 3.2":
            answer = get_answer_from_llama(neo4j_context, user_query)

        # Display the result
        st.subheader(f"Generated Response (Model: {model_choice})")
        st.write(f"**Query:** {user_query}")
        st.write(answer)

        # Add the new query and response to the session state
        st.session_state.response_history.append({
            "query": user_query,
            "response": answer
        })
    else:
        st.write("Please enter a query to get a response.")
st.markdown("</div></div>", unsafe_allow_html=True)  # Close input-container and centered-content divs


st.sidebar.subheader("📜 Response History")
if st.session_state.response_history:
    for i, entry in enumerate(st.session_state.response_history):
        if st.sidebar.button(f"View Response {i+1}: {entry['query'][:20]}..."):
            st.subheader("**Query**")
            st.write(entry['query'])
            st.subheader("**Generated Response**")
            st.write(entry['response'])

# Footer
st.markdown("<hr style='border:1px solid #b97bff'>", unsafe_allow_html=True)
st.markdown("<footer style='text-align: center; color: #888;'>Made with ❤️ using Streamlit</footer>", unsafe_allow_html=True)

