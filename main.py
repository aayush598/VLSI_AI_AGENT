import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
import json
import re

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini API client
client = genai.Client(api_key=API_KEY)

def generate_rtl_structure(user_input):
    prompt = f"Generate a JSON structure for RTL code files based on: {user_input}. Provide only JSON output without any extra text."
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    clean_response = post_process_response(response.text)
    return clean_response

def modify_structure(existing_structure, user_modification):
    prompt = f"Modify the following RTL folder structure based on the request:\n{existing_structure}\nUser request: {user_modification}. Provide only JSON output."
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    clean_response = post_process_response(response.text)
    return clean_response

def post_process_response(response_text):
    # Remove unwanted characters and Markdown formatting
    response_text = re.sub(r"```[a-zA-Z]*", "", response_text)  # Remove ```json, ```python, etc.
    response_text = response_text.strip("` ")  # Remove backticks and spaces
    
    try:
        json_data = json.loads(response_text)
        return json.dumps(json_data, indent=4)
    except json.JSONDecodeError:
        return "{}"  # Return empty JSON if parsing fails

st.title("RTL Folder Structure Generator")
st.markdown("### Generate and Modify RTL Project Structures")

user_input = st.text_area("Enter RTL project details:", height=100)

if st.button("Generate Structure"):
    if user_input:
        folder_structure = generate_rtl_structure(user_input)
        st.session_state["folder_structure"] = json.loads(folder_structure)
    else:
        st.warning("Please enter project details before generating.")

if "folder_structure" in st.session_state:
    st.subheader("Generated RTL Folder Structure:")
    st.json(st.session_state["folder_structure"], expanded=True)
    
    user_modification = st.text_area("Modify the structure based on:", height=100)
    
    if st.button("Modify Structure"):
        if user_modification:
            modified_structure = modify_structure(json.dumps(st.session_state["folder_structure"]), user_modification)
            st.session_state["folder_structure"] = json.loads(modified_structure)
            st.subheader("Modified RTL Folder Structure:")
            st.json(st.session_state["folder_structure"], expanded=True)
        else:
            st.warning("Please enter modification details.")

# Ensure the latest generated structure is always used
if "folder_structure" in st.session_state and isinstance(st.session_state["folder_structure"], dict):
    latest_structure = json.dumps(st.session_state["folder_structure"], indent=4)
    st.session_state["latest_structure"] = latest_structure
