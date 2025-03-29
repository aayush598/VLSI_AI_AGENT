import os
import streamlit as st
import sqlite3
import json
from google import genai
from dotenv import load_dotenv
import re

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Initialize SQLite database
conn = sqlite3.connect("rtl_folder_structures.db", check_same_thread=False)
c = conn.cursor()

def get_available_projects():
    """Fetch available project names from the database."""
    c.execute("SELECT project_name FROM folder_structures")
    return [row[0] for row in c.fetchall()]

def get_project_details(project_name):
    """Retrieve project description and folder structure from the database."""
    c.execute("SELECT folder_structure FROM folder_structures WHERE project_name = ?", (project_name,))
    row = c.fetchone()
    if row:
        folder_structure = json.loads(row[0])
        return folder_structure
    return {}

def clean_code(response_text):
    """Remove unwanted markdown and language specifiers from Gemini response."""
    return re.sub(r'```[a-zA-Z]*', '', response_text).strip()

def generate_code_for_file(project_name, project_description, folder_structure, file_path):
    """Generate code for a given file using Gemini API."""
    prompt = f'''
    Generate a complete code file based on the following details:
    
    **Project Name:** {project_name}
    **Project Description:** {project_description}
    **Folder Structure:** {json.dumps(folder_structure, indent=4)}
    **File Path:** {file_path}
    
    Provide the full code without explanations or additional text.
    Only provide the code for the file path which is mentioned.
    Do not include the code which will be mentioned in the other file.
    '''
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return clean_code(response.text)

def generate_code(project_name, project_location):
    """Generate and overwrite code files in the selected folder structure."""
    folder_structure = get_project_details(project_name)
    project_description = """Provide a detailed description of the project here..."""  # You can modify this
    
    if not folder_structure:
        st.error("No folder structure found for the selected project.")
        return
    
    for directory in folder_structure.get("directories", []):
        dir_path = os.path.join(project_location, directory["name"])
        for file_name in directory.get("files", []):
            file_path = os.path.join(dir_path, file_name)
            st.write(f"Generating code for {file_path}...")
            code = generate_code_for_file(project_name, project_description, folder_structure, file_path)
            
            os.makedirs(dir_path, exist_ok=True)
            with open(file_path, "w") as f:
                f.write(code)
            
            st.success(f"Code generated and saved: {file_path}")

# Streamlit UI
st.title("RTL Code Generator with Gemini")

available_projects = get_available_projects()
project_name = st.selectbox("Select Project", available_projects)
project_location = st.text_input("Enter Folder Location")

if st.button("Confirm Selection"):
    st.session_state["confirmed_project"] = project_name
    st.session_state["confirmed_location"] = project_location
    st.success(f"Project: {project_name}\nLocation: {project_location}")
    
if "confirmed_project" in st.session_state and "confirmed_location" in st.session_state:
    if st.button("Generate Code"):
        generate_code(st.session_state["confirmed_project"], st.session_state["confirmed_location"])
