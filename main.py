import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
import json
import re
import sqlite3

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini API client
client = genai.Client(api_key=API_KEY)

# Initialize SQLite database
conn = sqlite3.connect("rtl_folder_structures.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS folder_structures (
        project_name TEXT PRIMARY KEY,
        user_prompt TEXT,
        folder_structure TEXT
    )
""")
conn.commit()

def save_or_update_structure(project_name, user_input, folder_structure):
    """Saves a new project folder structure or updates an existing one."""
    c.execute("""
        INSERT INTO folder_structures (project_name, user_prompt, folder_structure) 
        VALUES (?, ?, ?) 
        ON CONFLICT(project_name) 
        DO UPDATE SET 
            user_prompt = excluded.user_prompt,
            folder_structure = excluded.folder_structure
    """, (project_name, user_input,  folder_structure))
    conn.commit()

def get_structure_by_name(project_name):
    """Retrieves the latest folder structure for a given project name."""
    c.execute("SELECT folder_structure FROM folder_structures WHERE project_name = ?", (project_name,))
    row = c.fetchone()
    return json.loads(row[0]) if row else {}

def generate_rtl_structure(user_input):
    prompt = f'''
    Generate a structured JSON output representing an RTL project folder hierarchy based on the following project description: "{user_input}". 

    The JSON output **must strictly follow this exact format** and contain only the specified keys:

    {{
        "project_name": "ProjectName",
        "directories": [
            {{
                "name": "src",
                "files": ["file1.v", "file2.sv"],
                "subdirectories": []
            }},
            {{
                "name": "tb",
                "files": ["testbench1.v", "testbench2.sv"],
                "subdirectories": []
            }}
        ],
        "metadata": {{
            "generated_by": "Gemini",
            "version": "1.0",
            "timestamp": "YYYY-MM-DD HH:MM:SS"
        }}
    }}

    **Key Constraints:**  
    - "project_name": A string representing the name of the RTL project.  
    - "directories": A list of dictionaries, each with:
      - "name": The directory name.
      - "files": A list of RTL-related files (e.g., `.v`, `.sv`).
      - "subdirectories": A list of nested directories (can be empty but must be present).  
    - "metadata": A dictionary containing:
      - "generated_by": Always "Gemini".
      - "version": Always "1.0".
      - "timestamp": The generation timestamp in "YYYY-MM-DD HH:MM:SS" format.  

    **Rules:**  
    1. The response **must strictly contain only the above keys and structure**. No additional keys, descriptions, or explanations.  
    2. Ensure that "directories" always has at least "src" and "tb" directories.  
    3. The "metadata" section must always be present.  
    4. **Return only valid JSON output**—no markdown, explanations, or additional formatting.  

    Provide the JSON output following these constraints. Do not include any preamble, explanations, or markdown formatting.
    '''

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    clean_response = post_process_response(response.text)
    validated_response = enforce_json_structure(clean_response)
    project_name = json.loads(validated_response).get("project_name", "Unnamed Project")
    save_or_update_structure(project_name, user_input, validated_response)
    return validated_response


def modify_structure(existing_structure, user_modification):
    prompt = f'''
        Modify the following RTL project folder structure based on this user request: "{user_modification}".

        **Existing JSON Structure:**  
        ```json
        {existing_structure}
        ```

        **Updated JSON must strictly follow this structure:**  
        ```json
        {{
            "project_name": "ProjectName",
            "directories": [
                {{
                    "name": "src",
                    "files": ["file1.v", "file2.sv"],
                    "subdirectories": []
                }},
                {{
                    "name": "tb",
                    "files": ["testbench1.v", "testbench2.sv"],
                    "subdirectories": []
                }}
            ],
            "metadata": {{
                "generated_by": "Gemini",
                "version": "1.0",
                "timestamp": "YYYY-MM-DD HH:MM:SS"
            }}
        }}
        ```

        **Key Constraints:**  
        - `"project_name"`: A string representing the name of the RTL project.  
        - `"directories"`: A list of dictionaries, each with:
            - `"name"`: The directory name.
            - `"files"`: A list of RTL-related files (e.g., `.v`, `.sv`).
            - `"subdirectories"`: A list of nested directories (can be empty but must be present).  
        - `"metadata"`: A dictionary containing:
            - `"generated_by"`: Always `"Gemini"`.
            - `"version"`: Always `"1.0"`.
            - `"timestamp"`: The generation timestamp in `"YYYY-MM-DD HH:MM:SS"` format.  

        **Rules:**  
        1. The response **must strictly contain only the above keys and structure**. No additional keys, descriptions, or explanations.  
        2. Ensure that `"directories"` always has at least `"src"` and `"tb"` directories.  
        3. The `"metadata"` section must always be present.  
        4. **Return only valid JSON output**—no markdown, explanations, or additional formatting.  
        5. Remember that the name of the project is already defined in the existing structure.
        6. Do not change the nmae of the project.

        Provide the JSON output following these constraints. Do not include any preamble, explanations, or markdown formatting.
    '''
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    clean_response = post_process_response(response.text)
    validated_response = enforce_json_structure(clean_response)
    project_name = json.loads(validated_response).get("project_name", "Unnamed Project")
    save_or_update_structure(project_name, user_input, validated_response)
    return validated_response


def post_process_response(response_text):
    """ Cleans AI response to extract pure JSON. """
    response_text = re.sub(r"```[a-zA-Z]*", "", response_text)  # Remove ```json, ```python, etc.
    response_text = response_text.strip("` ")  # Remove backticks and spaces
    
    try:
        json_data = json.loads(response_text)
        return json.dumps(json_data, indent=4)
    except json.JSONDecodeError:
        return "{}"  # Return empty JSON if parsing fails

def enforce_json_structure(json_text):
    """ Ensures the JSON output follows the fixed key-value structure. """
    try:
        data = json.loads(json_text)

        # Define strict format
        structured_data = {
            "project_name": data.get("project_name", "Unnamed Project"),
            "directories": data.get("directories", []),
            "metadata": {
                "generated_by": "Gemini",
                "version": "1.0",
                "timestamp": data.get("metadata", {}).get("timestamp", "YYYY-MM-DD HH:MM:SS")
            }
        }

        return json.dumps(structured_data, indent=4)
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

project_name = st.text_input("Enter project name to fetch structure:")

if st.button("Fetch Structure"):
    if project_name:
        fetched_structure = get_structure_by_name(project_name)
        st.session_state["folder_structure"] = fetched_structure
    else:
        st.warning("Please enter a project name to fetch.")

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
