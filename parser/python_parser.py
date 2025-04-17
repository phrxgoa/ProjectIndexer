import os
from tree_sitter import Parser, Query
from . import PYTHON_LANGUAGE

class Python_Result:
    def __init__(self):
        self.py_classes = []
        self.py_functions = []
        self.py_imports = []

    def __to_dict__(self):
        result = {}
        if self.py_classes:
            result['py_classes'] = self.py_classes
        if self.py_functions:
            result['py_functions'] = self.py_functions
        if self.py_imports:
            result['py_imports'] = self.py_imports
        return result

# Tree-sitter queries as class-level constants
CLASS_QUERY = Query(PYTHON_LANGUAGE, """
    (class_definition
        name: (identifier) @class_name
        body: (block) @class_body) @class_def
""")

FUNCTION_QUERY = Query(PYTHON_LANGUAGE, """
    (function_definition
        name: (identifier) @function_name
        parameters: (parameters) @params
        return_type: (type)? @return_type
        body: (block) @function_body) @function_def
""")

IMPORT_QUERY = Query(PYTHON_LANGUAGE, """
    (import_statement) @import
    (import_from_statement) @import_from
""")

def _should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped based on path patterns."""
    return (not file_path.endswith('.py') or 
            'venv' in file_path or 
            '__pycache__' in file_path or
            '_test.py' in file_path or 
            'test_' in file_path or
            'node_modules' in file_path)

def _read_source_code(file_path: str) -> str:
    """Read and return the contents of a Python source file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def _process_class(class_node, class_nodes_dict) -> dict:
    """Process a class node and return class information."""
    class_info = {
        'name': class_node.child_by_field_name('name').text.decode('utf8')
    }
    
    # Get base classes
    bases_node = class_nodes_dict.get('bases', [None])[0]
    if bases_node:
        class_info['bases'] = [b.text.decode('utf8') for b in bases_node.children 
                             if b.type != '(' and b.type != ')']
    
    # Get methods
    methods = []
    body_node = class_node.child_by_field_name('body')
    for method_index, method_nodes_dict in FUNCTION_QUERY.matches(body_node):
        method_node = method_nodes_dict['function_def'][0]
        methods.append(_process_function(method_node))
    
    if methods:
        class_info['methods'] = methods
    
    return class_info

def _process_function(function_node) -> str:
    """Process a function node and return its signature."""
    func_name = function_node.child_by_field_name('name').text.decode('utf8')
    params = function_node.child_by_field_name('parameters').text.decode('utf8')
    return_type = function_node.child_by_field_name('return_type')
    return_type_str = f" -> {return_type.text.decode('utf8')}" if return_type else " -> None"
    
    # Get decorators
    decorators = []
    if function_node.prev_named_sibling and function_node.prev_named_sibling.type == 'decorator':
        decorator_node = function_node.prev_named_sibling
        while decorator_node and decorator_node.type == 'decorator':
            decorators.append(decorator_node.text.decode('utf8'))
            decorator_node = decorator_node.prev_named_sibling
    
    return f"{' '.join(reversed(decorators))} {func_name}{params}{return_type_str}".strip()

def _process_imports(tree_root_node, result: Python_Result) -> None:
    """Process import statements and add them to the result."""
    for index, import_nodes_dict in IMPORT_QUERY.matches(tree_root_node):
        import_node = list(import_nodes_dict.values())[0][0]
        result.py_imports.append(import_node.text.decode('utf8'))

def extract_types_and_members_from_file_for_python(file_path: str, extract_imports: bool = False) -> Python_Result:
    """
    Extract Python class, function, and import information from a file.
    
    Args:
        file_path: Path to the Python file to analyze
        extract_imports: Whether to extract import statements (default: False)
    
    Returns:
        Python_Result object containing extracted information
    """
    result = Python_Result()
    
    if _should_skip_file(file_path):
        return result
    
    source_code = _read_source_code(file_path)
    parser = Parser(language=PYTHON_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))
    
    # Process classes
    for index, class_nodes_dict in CLASS_QUERY.matches(tree.root_node):
        class_node = class_nodes_dict['class_def'][0]
        result.py_classes.append(_process_class(class_node, class_nodes_dict))
    
    # Process top-level functions
    for index, function_nodes_dict in FUNCTION_QUERY.matches(tree.root_node):
        function_node = function_nodes_dict['function_def'][0]
        if (function_node.parent and 
            function_node.parent.type == 'class_definition'):
            continue
            
        result.py_functions.append(_process_function(function_node))
    
    # Process imports if requested
    if extract_imports:
        _process_imports(tree.root_node, result)
    
    return result