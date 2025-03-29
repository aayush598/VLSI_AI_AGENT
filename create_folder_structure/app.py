import streamlit as st
import os
from pathlib import Path
from database import get_all_project_names, get_project_structure
from folder_creator import create_folders

st.title("RTL Folder Structure Creator")

# Fetch saved projects
project_names = get_all_project_names()

if not project_names:
    st.warning("No saved projects found.")
else:
    selected_project = st.selectbox("Select a project:", project_names)

    if st.button("Show Folder Structure"):
        folder_structure = get_project_structure(selected_project)

        if folder_structure:
            st.subheader("Folder Structure:")
            st.json(folder_structure, expanded=True)

            # Store the structure in session state
            st.session_state["selected_structure"] = folder_structure

            # Show button to create folder structure
            st.session_state["show_create_button"] = True

# Persist the "Create Folder Structure" button using session state
if "show_create_button" in st.session_state and st.session_state["show_create_button"]:
    if st.button("Create Folder Structure"):
        st.session_state["show_folder_input"] = True  # Show folder input field

# Persist the folder selection input field
if "show_folder_input" in st.session_state and st.session_state["show_folder_input"]:
    st.subheader("Select Folder Location")

    col1, col2 = st.columns([3, 1])  # Two-column layout

    with col1:
        folder_path = st.text_input("Enter or Paste Folder Path:", key="folder_path_input")

    with col2:
        validate_path = st.button("Validate Path")  # Validation button

    # Show validation status immediately
    if validate_path:
        if folder_path:
            folder = Path(folder_path)

            if folder.exists() and folder.is_dir():
                st.success(f"Selected Folder: {folder_path}")
                st.session_state["valid_folder"] = True  # Store state

            else:
                st.error("Invalid folder path. Please enter a valid directory.")
                st.session_state["valid_folder"] = False  # Reset if invalid

# Show confirmation button only if path is valid
if st.session_state.get("valid_folder", False):
    if st.button("Confirm and Create Structure"):
        created_path = create_folders(folder_path, st.session_state["selected_structure"])
        st.success(f"Folder structure created at: {created_path}")

        # Reset session state after completion
        st.session_state.clear()
