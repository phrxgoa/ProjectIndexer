import os
import re
import json

# Regex patterns for different type and member definitions in C# files
patterns = {
    'classes': re.compile(r'\bclass\s+(\w+)'),
    'structs': re.compile(r'\bstruct\s+(\w+)'),
    'interfaces': re.compile(r'\binterface\s+(\w+)'),
    'enums': re.compile(r'\benum\s+(\w+)'),
    # Regex for methods: matches common C# method definitions with access modifier, return type, and parameters.
    'methods': re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:[\w\<\>\[\]]+\s+)+(\w+)\s*\([^)]*\)\s*(?:\{|=>)')
}

def extract_types_and_members_from_file(file_path):
    """
    Extracts classes, structs, interfaces, enums, and methods from a file.
    Returns a dictionary with lists for each type and member found.
    """
    results = {
        'classes': [],
        'structs': [],
        'interfaces': [],
        'enums': [],
        'methods': []
    }
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        for key, pattern in patterns.items():
            matches = pattern.findall(content)
            if matches:
                results[key] = matches
    return results

def index_project_structure(root_dir):
    """
    Walks through the directory tree starting at root_dir.
    Extracts type definitions and members from each C# file and creates a structured index.
    """
    project_index = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.cs'):
                file_path = os.path.join(subdir, file)
                relative_path = os.path.relpath(file_path, root_dir)
                details = extract_types_and_members_from_file(file_path)
                # Include in the index only if any type or member was found
                if any(details.values()):
                    project_index[relative_path] = details
    return project_index

if __name__ == "__main__":
    # Adjust this path as needed to point to your project directory.
    root_directory = "C:\\MyRepos\\GitHub\\SomeFolder\\ProjectRoot"
    index = index_project_structure(root_directory)
    # Export file renamed to ProjectIndex.json
    export_filename = 'ProjectIndex.json'
    with open(export_filename, 'w', encoding='utf-8') as index_file:
        json.dump(index, index_file, indent=4)
    print(f"Project structure indexed successfully and exported to {export_filename}.")