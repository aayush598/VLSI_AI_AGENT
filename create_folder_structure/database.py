import sqlite3
import json

DB_NAME = "rtl_folder_structures.db"

def get_all_project_names():
    """Fetch all saved project names from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT project_name FROM folder_structures")
    projects = [row[0] for row in c.fetchall()]
    conn.close()
    return projects

def get_project_structure(project_name):
    """Fetch the folder structure of the selected project."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT folder_structure FROM folder_structures WHERE project_name = ?", (project_name,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}
