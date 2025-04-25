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
            result['functions'] = self.functions
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
        parameters: (formal_parameters) @function.parameters)

    (export_statement
        declaration: (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.parameters))
            
    (method_definition
        name: (property_identifier) @function.name
        parameters: (formal_parameters) @function.parameters)
        
    (variable_declaration
        (variable_declarator
            name: (identifier) @function.name
            value: (arrow_function
                parameters: (formal_parameters) @function.parameters)))

    (export_statement
        declaration: (variable_declaration
            (variable_declarator
                name: (identifier) @function.name
                value: (arrow_function
                    parameters: (formal_parameters) @function.parameters))))
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
        declaration: (identifier) @export.default
        "default")
"""

def _should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped based on path patterns."""
    return (not file_path.endswith('.js') or
            'node_modules' in file_path or
            'dist' in file_path or
            'build' in file_path)

def _get_node_text(node):
    """Safely decode node text."""
    if node is None:
        return ""
    try:
        return node.text.decode('utf8').strip()
    except:
        return ""

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
    
    print(f"Parsing JavaScript file: {file_path}")
    parser = Parser(language=JAVASCRIPT_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))
    root_node = tree.root_node
    
    print(f"Root node type: {root_node.type}, children: {len(root_node.children)}")
    
    # Process classes
    class_query = Query(JAVASCRIPT_LANGUAGE, CLASS_QUERY_STR)
    captures = class_query.captures(root_node)
    
    # Group captures by class node
    grouped_classes = {}
    for node, capture_name in captures:
        parent = node.parent
        while parent and not (parent.type == "class_declaration" or 
                             (parent.type == "export_statement" and 
                              parent.child_by_field_name("declaration") and 
                              parent.child_by_field_name("declaration").type == "class_declaration")):
            parent = parent.parent
        
        if parent:
            key = parent.id
            if key not in grouped_classes:
                grouped_classes[key] = {"parent": parent}
            
            if capture_name == "class.name":
                grouped_classes[key]["name"] = node
    
    # Process grouped classes
    for key, class_data in grouped_classes.items():
        if "name" in class_data:
            name_node = class_data["name"]
            class_info = {"name": _get_node_text(name_node)}
            result.classes.append(class_info)
            print(f"Found class: {class_info['name']}")
    
    # Process functions
    function_query = Query(JAVASCRIPT_LANGUAGE, FUNCTION_QUERY_STR)
    captures = function_query.captures(root_node)
    
    # Group captures by function node
    grouped_functions = {}
    for node, capture_name in captures:
        # Find the function parent node
        parent = node.parent
        while parent and not (parent.type in ["function_declaration", "method_definition", "arrow_function"] or
                             (parent.type == "export_statement" and 
                              parent.child_by_field_name("declaration") and 
                              parent.child_by_field_name("declaration").type == "function_declaration")):
            parent = parent.parent
            
        if parent:
            key = parent.id
            if key not in grouped_functions:
                grouped_functions[key] = {"parent": parent}
            
            if capture_name == "function.name":
                grouped_functions[key]["name"] = node
            elif capture_name == "function.parameters":
                grouped_functions[key]["parameters"] = node
    
    # Process grouped functions
    for key, function_data in grouped_functions.items():
        if "name" in function_data:
            name_node = function_data["name"]
            params_node = function_data.get("parameters")
            
            function_signature = f"{_get_node_text(name_node)}({_get_node_text(params_node)})"
            result.functions.append(function_signature)
            print(f"Found function: {function_signature}")
    
    # Process imports if requested
    if extract_imports:
        import_query = Query(JAVASCRIPT_LANGUAGE, IMPORT_QUERY_STR)
        captures = import_query.captures(root_node)
        
        # Group captures by import statement
        grouped_imports = {}
        for node, capture_name in captures:
            parent = node.parent
            while parent and parent.type != "import_statement":
                parent = parent.parent
                
            if parent:
                key = parent.id
                if key not in grouped_imports:
                    grouped_imports[key] = {"source": None, "names": []}
                
                if capture_name == "import.source":
                    grouped_imports[key]["source"] = _get_node_text(node).strip('"\'')
                elif capture_name in ["import.name", "import.default", "import.namespace"]:
                    name = _get_node_text(node)
                    if name:
                        prefix = ""
                        if capture_name == "import.default":
                            prefix = "default as "
                        elif capture_name == "import.namespace":
                            prefix = "* as "
                        grouped_imports[key]["names"].append(f"{prefix}{name}")
        
        # Process grouped imports
        for key, import_data in grouped_imports.items():
            if import_data["source"]:
                import_info = {
                    "source": import_data["source"],
                    "imported_items": import_data["names"] if import_data["names"] else ["*"]
                }
                result.imports.append(import_info)
                print(f"Found import: {import_info['source']} - {import_info['imported_items']}")
    
        # Process exports
        export_query = Query(JAVASCRIPT_LANGUAGE, EXPORT_QUERY_STR)
        captures = export_query.captures(root_node)
        
        # Group captures by export statement
        grouped_exports = {}
        for node, capture_name in captures:
            parent = node.parent
            while parent and parent.type != "export_statement":
                parent = parent.parent
                
            if parent:
                key = parent.id
                if key not in grouped_exports:
                    grouped_exports[key] = {}
                
                if capture_name in ["export.name", "export.default"]:
                    name = _get_node_text(node)
                    if name:
                        prefix = "default: " if capture_name == "export.default" else ""
                        export_info = f"{prefix}{name}"
                        result.exports.append(export_info)
                        print(f"Found export: {export_info}")
    
    print(f"Finished parsing {file_path}: Found {len(result.classes)} classes, {len(result.functions)} functions")
    return result