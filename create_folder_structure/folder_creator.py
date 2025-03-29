import os
import json

def create_folders(base_path, folder_structure):
    """Recursively create the folder structure."""
    project_root = os.path.join(base_path, folder_structure["project_name"])
    
    if not os.path.exists(project_root):
        os.makedirs(project_root)

    for directory in folder_structure["directories"]:
        dir_path = os.path.join(project_root, directory["name"])
        os.makedirs(dir_path, exist_ok=True)

        for file in directory["files"]:
            file_path = os.path.join(dir_path, file)
            open(file_path, 'w').close()  # Create an empty file

        for subdir in directory["subdirectories"]:
            subdir_path = os.path.join(dir_path, subdir["name"])
            os.makedirs(subdir_path, exist_ok=True)

    return project_root
