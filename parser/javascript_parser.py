# parser/javascript_parser.py
import os
from tree_sitter import Parser, Query
from . import JAVASCRIPT_LANGUAGE

class JavaScript_Result:
    """Holds extracted data from a JavaScript file."""
    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.exports = []

    def __to_dict__(self):
        """Converts the result object to a dictionary."""
        result = {}
        if self.classes:
            result['classes'] = self.classes
        if self.functions:
            result['functions'] = [f['function_signature'] for f in self.functions]
        if self.imports:
            result['imports'] = self.imports
        if self.exports:
            result['exports'] = self.exports
        return result

# Tree-sitter queries for JavaScript
CLASS_QUERY_STR = """
    (class_declaration
        name: (identifier) @class.name
        body: (class_body) @class.body)

    (export_statement
        declaration: (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body))
"""

FUNCTION_QUERY_STR = """
    (function_declaration
        name: (identifier) @function.name
        parameters: (formal_parameters) @function.parameters
        body: (statement_block) @function.body)

    (export_statement
        declaration: (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.parameters
            body: (statement_block) @function.body))
            
    (method_definition
        name: (property_identifier) @function.name
        parameters: (formal_parameters) @function.parameters
        body: (statement_block) @function.body)
        
    (variable_declaration
        (variable_declarator
            name: (identifier) @function.name
            value: (arrow_function
                parameters: (formal_parameters) @function.parameters
                body: (_) @function.body)))

    (export_statement
        declaration: (variable_declaration
            (variable_declarator
                name: (identifier) @function.name
                value: (arrow_function
                    parameters: (formal_parameters) @function.parameters
                    body: (_) @function.body))))
"""

IMPORT_QUERY_STR = """
    (import_statement
        (import_clause
            (named_imports
                (import_specifier
                    name: (identifier) @import.name))?
            (namespace_import (identifier) @import.namespace)?
            (identifier)? @import.default)
        source: (string) @import.source)

    (import_statement
        source: (string) @import.source)
"""

EXPORT_QUERY_STR = """
    (export_statement
        (variable_declaration
            (variable_declarator
                name: (identifier) @export.name)))
                
    (export_statement
        (export_clause
            (export_specifier
                name: (identifier) @export.name)))
                
    (export_statement
        name: (identifier) @export.default
        "default")
"""

def _should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped based on path patterns."""
    return (not file_path.endswith('.js') or
            'node_modules' in file_path or
            'dist' in file_path or
            'build' in file_path or
            'test' in file_path)

def _get_node_text(node):
    """Safely decode node text."""
    return node.text.decode('utf8').strip() if node else ""

def _process_class(capture):
    """Process a class capture."""
    name_node = capture.get("class.name")
    return {
        "name": _get_node_text(name_node)
    }

def _process_function(capture):
    """Process a function capture."""
    name_node = capture.get("function.name")
    if not name_node:
        return None
    params_node = capture.get("function.parameters")
    
    name = _get_node_text(name_node)
    parameters = _get_node_text(params_node)
    
    return {
        "function_signature": f"{name}{parameters}"
    }

def _process_import(capture):
    """Process an import capture."""
    source = _get_node_text(capture.get("import.source")).strip('"\'')
    imported_items = []
    
    if "import.name" in capture:
        imported_items.append(_get_node_text(capture["import.name"]))
    if "import.namespace" in capture:
        imported_items.append(f"* as {_get_node_text(capture['import.namespace'])}")
    if "import.default" in capture and _get_node_text(capture["import.default"]):
        imported_items.append(f"default as {_get_node_text(capture['import.default'])}")
    
    return {
        "source": source,
        "imported_items": imported_items if imported_items else ["*"]
    }

def _process_export(capture):
    """Process an export capture."""
    if "export.name" in capture:
        return _get_node_text(capture["export.name"])
    if "export.default" in capture:
        return f"default: {_get_node_text(capture['export.default'])}"
    return None

def extract_types_and_members_from_file_for_javascript(file_path: str, extract_imports: bool = False) -> JavaScript_Result:
    """Extract types and members from a JavaScript file.
    
    Args:
        file_path: Path to the JavaScript file
        extract_imports: Whether to extract import statements
        
    Returns:
        JavaScript_Result: Object containing all extracted types and members
    """
    result = JavaScript_Result()
    
    if _should_skip_file(file_path):
        return result
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return result
    
    parser = Parser(language=JAVASCRIPT_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))
    root_node = tree.root_node
    
    # Process classes
    class_query = Query(JAVASCRIPT_LANGUAGE, CLASS_QUERY_STR)
    for match, capture_dict in class_query.captures(root_node):
        class_info = _process_class({capture_dict: match})
        if class_info:
            result.classes.append(class_info)
    
    # Process functions
    function_query = Query(JAVASCRIPT_LANGUAGE, FUNCTION_QUERY_STR)
    for match, capture_dict in function_query.captures(root_node):
        function_info = _process_function({capture_dict: match})
        if function_info:
            result.functions.append(function_info)
    
    # Process imports if requested
    if extract_imports:
        import_query = Query(JAVASCRIPT_LANGUAGE, IMPORT_QUERY_STR)
        for match, capture_dict in import_query.captures(root_node):
            import_info = _process_import({capture_dict: match})
            if import_info:
                result.imports.append(import_info)
    
        # Process exports
        export_query = Query(JAVASCRIPT_LANGUAGE, EXPORT_QUERY_STR)
        for match, capture_dict in export_query.captures(root_node):
            export_info = _process_export({capture_dict: match})
            if export_info:
                result.exports.append(export_info)
    
    return result