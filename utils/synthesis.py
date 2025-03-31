import streamlit as st
import os
import sqlite3
import subprocess
import json
from PIL import Image

def get_project_list():
    """Fetch project names from the rtl_folder_structures.db database."""
    conn = sqlite3.connect("database/folder_structure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT project_name FROM folder_structures")
    projects = [row[0] for row in cursor.fetchall()]
    conn.close()
    return projects

def get_folder_structure(project_name):
    """Fetch folder structure from the rtl_folder_structures.db database based on project name."""
    conn = sqlite3.connect("database/folder_structure.db")
    cursor = conn.cursor()
    cursor.execute("SELECT folder_structure FROM folder_structures WHERE project_name=?", (project_name,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def find_verilog_files(folder_structure, root_path):
    """Find all Verilog files based on the stored folder structure."""
    verilog_files = []
    for directory in folder_structure.get("directories", []):
        dir_path = os.path.join(root_path, directory["name"])
        for file in directory["files"]:
            if file.endswith(".v") or file.endswith(".sv"):
                file_path = os.path.join(dir_path, file)
                if os.path.exists(file_path):
                    verilog_files.append(file_path)
    return verilog_files

def run_synthesis(folder_path, project_name):
    """Run synthesis using Yosys and save the image output."""
    output_folder = os.path.join(folder_path, "synthesized_image")
    os.makedirs(output_folder, exist_ok=True)
    
    folder_structure = get_folder_structure(project_name)
    if not folder_structure:
        return "No folder structure found."
    
    verilog_files = find_verilog_files(folder_structure, folder_path)
    if not verilog_files:
        return "No Verilog files found for synthesis."
    
    for vfile in verilog_files:
        base_name = os.path.splitext(os.path.basename(vfile))[0]
        output_image = os.path.join(output_folder, f"{base_name}.png")
        yosys_script = f"""
        read_verilog {vfile}
        synth
        show -format png -prefix {output_folder}/{base_name}
        """
        script_path = os.path.join(folder_path, "synthesis.ys")
        
        with open(script_path, "w") as f:
            f.write(yosys_script)
        
        result = subprocess.run(["yosys", "-s", script_path], capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error in synthesizing {vfile}: {result.stderr}"
    
    return output_folder

def display_images(output_folder):
    """Display synthesized images in UI."""
    if not os.path.exists(output_folder):
        st.warning("No synthesized images found.")
        return
    
    image_files = [f for f in os.listdir(output_folder) if f.endswith(".png")]
    if not image_files:
        st.warning("No synthesized images found.")
    else:
        for img_file in image_files:
            img_path = os.path.join(output_folder, img_file)
            if os.path.exists(img_path):
                st.image(img_path, caption=img_file, use_column_width=True)