import time
from parser.python_parser import extract_types_and_members_from_file_for_python

def test_parser(file_path):
    print(f"\nTesting parser on: {file_path}")
    
    # Time the parsing
    start_time = time.time()
    result = extract_types_and_members_from_file_for_python(file_path, extract_imports=True)
    elapsed_time = time.time() - start_time
    
    print(f"\nParsing completed in {elapsed_time:.4f} seconds")
    
    # Print results
    print("\nClasses found:")
    for cls in result.py_classes:
        print(f"- {cls['name']}")
        if 'bases' in cls:
            print(f"  Inherits from: {', '.join(cls['bases'])}")
        if 'methods' in cls:
            print(f"  Methods: {len(cls['methods'])}")
    
    print("\nFunctions found:")
    for func in result.py_functions:
        print(f"- {func}")
    
    print("\nImports found:")
    for imp in result.py_imports:
        print(f"- {imp}")

if __name__ == "__main__":
    test_parser("Project_Indexer.py")
    test_parser("parser/python_parser.py")