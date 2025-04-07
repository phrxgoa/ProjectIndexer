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

def extract_types_and_members_from_file_for_python(file_path: str, extract_imports: bool = False) -> Python_Result:
    result = Python_Result()
    
    # Ignore non-Python files and test files
    if not file_path.endswith('.py') or 'venv' in file_path or '__pycache__' in file_path:
        return result
    if '_test.py' in file_path or 'test_' in file_path:
        return result


    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
        
    # Initialize Tree-sitter parser
    parser = Parser(language=PYTHON_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))

    # Tree-sitter queries
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

    # Process classes
    for index, class_nodes_dict in CLASS_QUERY.matches(tree.root_node):
        class_node = class_nodes_dict['class_def'][0]
        class_info = {
            'name': class_node.child_by_field_name('name').text.decode('utf8')
        }
        
        # Get base classes
        bases_node = class_nodes_dict.get('bases', [None])[0]
        if bases_node:
            class_info['bases'] = [b.text.decode('utf8') for b in bases_node.children if b.type != '(' and b.type != ')']
        
        # Get methods
        methods = []
        body_node = class_node.child_by_field_name('body')
        for method_index, method_nodes_dict in FUNCTION_QUERY.matches(body_node):
            method_node = method_nodes_dict['function_def'][0]
            method_name = method_node.child_by_field_name('name').text.decode('utf8')
            params = method_node.child_by_field_name('parameters').text.decode('utf8')
            return_type = method_node.child_by_field_name('return_type')
            return_type_str = f" -> {return_type.text.decode('utf8')}" if return_type else " -> None"
            
            # Get decorators
            decorators = []
            if method_node.prev_named_sibling and method_node.prev_named_sibling.type == 'decorator':
                decorator_node = method_node.prev_named_sibling
                while decorator_node and decorator_node.type == 'decorator':
                    decorators.append(decorator_node.text.decode('utf8'))
                    decorator_node = decorator_node.prev_named_sibling
            
            method_sig = f"{' '.join(reversed(decorators))} {method_name}{params}{return_type_str}"
            methods.append(method_sig.strip())
        
        if methods:
            class_info['methods'] = methods
        
        result.py_classes.append(class_info)

    # Process top-level functions
    for index, function_nodes_dict in FUNCTION_QUERY.matches(tree.root_node):
        # Skip if the function is inside a class
        if 'class_def' in function_nodes_dict:
            continue
        function_node = function_nodes_dict['function_def'][0]
        if function_node.parent and function_node.parent.type == 'class_definition':
            continue
            
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
        
        func_sig = f"{' '.join(reversed(decorators))} {func_name}{params}{return_type_str}"
        result.py_functions.append(func_sig.strip())

    # Process imports if requested
    if extract_imports:
        for index, import_nodes_dict in IMPORT_QUERY.matches(tree.root_node):
            import_node = list(import_nodes_dict.values())[0][0]
            import_text = import_node.text.decode('utf8')
            result.py_imports.append(import_text)

    return result