import re

patterns_csharp = {
    'classes': re.compile(r'\bclass\s+(\w+)'),
    'structs': re.compile(r'\bstruct\s+(\w+)'),
    'interfaces': re.compile(r'\binterface\s+(\w+)'),
    'enums': re.compile(r'\benum\s+(\w+)'),
    # Regex for methods: matches common C# method definitions with access modifier, return type, and parameters.
    'methods': re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:[\w\<\>\[\]]+\s+)+(\w+)\s*\([^)]*\)\s*(?:\{|=>)')
}

class C_Sharp_Result:
    def __init__(self):
        self.classes = []
        self.structs = []
        self.interfaces = []
        self.enums = []
        self.methods = []
        
    def __to_dict__(self):
        return {
            'classes': self.classes,
            'structs': self.structs,
            'interfaces': self.interfaces,
            'enums': self.enums,
            'methods': self.methods
        }

def read_file_and_match(root_dir: str) -> C_Sharp_Result:
    """
    Reads a file and matches patterns to extract types and members.
    Returns an instance of results_class with the extracted information.
    """
    results = C_Sharp_Result()
    with open(root_dir, 'r', encoding='utf-8') as file:
        content = file.read()
        for key, pattern in patterns_csharp.items():
            # Find all matches for the current pattern
            matches = pattern.findall(content)
            if not matches:
                continue
            for match in matches:
                # Append the match to the corresponding list in the results object
                getattr(results, key).append(match)
                # If the match is a list, extend the list in the results object
                if isinstance(match, list):
                    getattr(results, key).extend(match)
    return results

def extract_types_and_members_from_file_for_csharp(file_path: str) -> C_Sharp_Result:
    """
    Extracts classes, structs, interfaces, enums, and methods from a C# file.
    Returns a C_Sharp_Result object with lists for each type and member found.
    """
    return read_file_and_match(file_path, '.cs', C_Sharp_Result)
