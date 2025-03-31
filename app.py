import streamlit as st
from utils.folder_structure_generation import generate_rtl_structure, modify_structure, get_structure_by_name
from utils.folder_setup import create_folders, get_all_project_names, get_project_structure
from utils.code_generator import generate_code
from utils.linting import run_linting
from utils.synthesis import run_synthesis, get_project_list,display_images

# Streamlit App Configuration
st.set_page_config(page_title="RTL Project Manager", layout="wide")

# Navbar for navigation
menu = ["Folder Structure Generation", "Folder Setup", "Code Generation", "Linting", "Synthesis"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Folder Structure Generation":
    st.title("Generate or Modify RTL Folder Structure")
    
    option = st.radio("Choose an action:", ["Generate New Structure", "Modify Existing Structure"])
    
    if option == "Generate New Structure":
        user_input = st.text_area("Describe your project:")
        if st.button("Generate Structure"):
            structure = generate_rtl_structure(user_input)
            st.json(structure)
    
    elif option == "Modify Existing Structure":
        projects = get_all_project_names()
        project_name = st.selectbox("Select Project", projects)
        
        if project_name:
            current_structure = get_structure_by_name(project_name)
            st.subheader("Current Structure")
            st.json(current_structure, expanded=False)
            
            modified_structure = st.text_area("Modify the structure (JSON format):", value=str(current_structure))
            if st.button("Save Modifications"):
                try:
                    modify_structure(project_name, modified_structure)
                    updated_structure = get_structure_by_name(project_name)  # Fetch updated structure
                    st.success("Folder structure updated successfully.")
                    st.subheader("Updated Structure")
                    st.json(updated_structure, expanded=False)  # Show updated structure
                except Exception as e:
                    st.error(f"Error updating structure: {e}")

elif choice == "Folder Setup":
    st.title("Set Up Project Folder")
    projects = get_all_project_names()
    project_name = st.selectbox("Select Project", projects)
    base_path = st.text_input("Enter base directory:")
    if st.button("Create Folders"):
        structure = get_project_structure(project_name)
        if structure:
            project_path = create_folders(base_path, structure)
            st.success(f"Project folders created at {project_path}")
        else:
            st.error("No structure found for selected project.")

elif choice == "Code Generation":
    st.title("Generate RTL Code")
    projects = get_all_project_names()
    project_name = st.selectbox("Select Project", projects)
    project_location = st.text_input("Enter project location:")
    if st.button("Generate Code"):
        try:
            result = generate_code(project_name, project_location)
            st.success(result)
        except Exception as e:
            st.error(str(e))

elif choice == "Linting":
    st.title("Run Linting on RTL Code")
    
    projects = get_all_project_names()
    project_name = st.selectbox("Select Project", projects)
    
    if project_name:
        project_path = st.text_input("Enter project directory:")
        if st.button("Run Linter"):
            try:
                lint_results = run_linting(project_name, project_path)
                if isinstance(lint_results, str):
                    st.error(lint_results)
                else:
                    st.subheader("Linting Results")
                    for file_name, lint_output in lint_results:
                        if lint_output:
                            st.error(f"⚠ Issues in {file_name}")
                            st.code(lint_output, language="plaintext")
                        else:
                            st.success(f"✅ No issues found in {file_name}")
                st.success("Linting completed.")
            except Exception as e:
                st.error(str(e))


elif choice == "Synthesis":
    st.title("Run Synthesis on RTL Code")
    projects = get_project_list()
    project_name = st.selectbox("Select Project", projects)
    project_path = st.text_input("Enter project directory:")
    if st.button("Run Synthesis"):
        try:
            synthesis_results = run_synthesis(project_path, project_name)
            st.text_area("Synthesis Output:", synthesis_results, height=300)
            st.success("Synthesis completed.")
            display_images(synthesis_results)  # Display synthesized images
        except Exception as e:
            st.error(str(e))