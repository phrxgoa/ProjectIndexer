import os
import json
import argparse
from parser.parser import extract_types_and_members_from_file_for_csharp, extract_types_and_members_from_file_for_python

def index_project_structure(root_dir: str, extract_imports: bool = False):
    """
    Walks through the directory tree starting at root_dir.
    Extracts type definitions and members from each C# or Python file and creates a structured index.
    """
    project_index = {}
    print(f"Indexing project structure starting at: {root_dir}")
    # Walk through the directory tree
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            # Process only C# and Python files
            if not file.endswith('.cs') and not file.endswith('.py'):
                print(f"Skipping non-C# or non-Python file: {file}")
                continue
            # Construct the full file path and relative path
            file_path = os.path.join(subdir, file)
            relative_path = os.path.relpath(file_path, root_dir)
            if file.endswith('.cs'):
                # Extract C# types and members
                details = extract_types_and_members_from_file_for_csharp(file_path)
            elif file.endswith('.py'):
                # Extract Python types and members
                details = extract_types_and_members_from_file_for_python(file_path, extract_imports)
            # Include in the index only if any type or member was found
            project_index_details = details.__to_dict__()
            if any(project_index_details.values()):
                project_index[relative_path] = project_index_details
    return project_index

if __name__ == "__main__":
    # Specify pwd as default root directory and argument --path if provided
    root_directory = os.getcwd()  # Default to current working directory
    # Check if a path argument is provided 
    parser = argparse.ArgumentParser(description='Index project structure for C# and Python files.')
    parser.add_argument('--path', type=str, help='Path to the project directory to index')
    parser.add_argument('--imports', action='store_true', help='Extract imports from Python files', default=False)
    args = parser.parse_args()
    if args.path:
        root_directory = args.path
    # Check if the provided path exists
    if not os.path.exists(root_directory):
        print(f"Provided path does not exist: {root_directory}")
        exit(1)
    # Check if the provided path is a directory
    if not os.path.isdir(root_directory):
        print(f"Provided path is not a directory: {root_directory}")
        exit(1)
    # Index the project structure starting at the specified root directory  
    index = index_project_structure(root_directory, args.imports)
    # Export file renamed to ProjectIndex.json
    export_filename = 'ProjectIndex.json'
    with open(export_filename, 'w', encoding='utf-8') as index_file:
        json.dump(index, index_file, indent=4)
    print(f"Project structure indexed successfully and exported to {export_filename}.")