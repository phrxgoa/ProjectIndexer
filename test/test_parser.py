import time
from parser.python_parser import extract_types_and_members_from_file_for_python
from parser.csharp_parser import extract_types_and_members_from_file_for_csharp

def test_python_parser(file_path):
    print(f"\nTesting Python parser on: {file_path}")
    
    start_time = time.time()
    result = extract_types_and_members_from_file_for_python(file_path, extract_imports=True)
    elapsed_time = time.time() - start_time
    
    print(f"\nParsing completed in {elapsed_time:.4f} seconds")
    
    print("\nClasses found:")
    for cls in result.py_classes:
        print(f"- {cls['name']}")
        if 'bases' in cls:
            print(f"  Inherits from: {', '.join(cls['bases'])}")
        if 'methods' in cls:
            print(f"  Methods: {len(cls['methods'])}")
            for method in cls['methods']:
                print(f"    - {method}")

def test_csharp_parser(file_path):
    print(f"\nTesting C# parser on: {file_path}")
    
    start_time = time.time()
    result = extract_types_and_members_from_file_for_csharp(file_path)
    elapsed_time = time.time() - start_time
    
    print(f"\nParsing completed in {elapsed_time:.4f} seconds")
    
    print("\nClasses found:")
    for cls in result.classes:
        print(f"- {cls['name']}")
        if 'bases' in cls:
            print(f"  Inherits from: {cls['bases']}")
        if 'methods' in cls:
            print(f"  Methods: {len(cls['methods'])}")
            for method in cls['methods']:
                print(f"    - {method['name']}()")
                if 'modifiers' in method:
                    print(f"      Modifiers: {', '.join(method['modifiers'])}")
        
    print("Raw dictionary:")
    print(result.__to_dict__())

if __name__ == "__main__":
    test_python_parser("Project_Indexer.py")
    test_python_parser("parser/python_parser.py")
    test_csharp_parser("test/resources/test.cs")