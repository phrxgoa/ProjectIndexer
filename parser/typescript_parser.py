import os
import tree_sitter
from . import TYPESCRIPT_LANGUAGE, TSX_LANGUAGE
from typing import List, Dict, Any, Optional

class TypeScript_Result:
    """Holds extracted data from a TypeScript/TSX file."""
    def __init__(self):
        self.classes: List[Dict[str, Any]] = []
        self.interfaces: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.enums: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []

    def __to_dict__(self):
        """Converts the result object to a dictionary."""
        # remove the start and end lines
        result_json = {}
        if self.classes:
            result_json['classes'] = self.classes
        if self.interfaces:
            result_json['interfaces'] = [interface.get("name") for interface in self.interfaces]
        if self.functions:
            result_json['functions'] = [f['function_signature'] for f in self.functions]
        if self.enums:
            result_json['enums'] = self.enums
        if self.imports:
            result_json['imports'] = self.imports
        return result_json

# Tree-sitter queries for TypeScript/TSX
QUERIES = {
    "imports": """
        (import_statement
            (import_clause
                (named_imports
                    (import_specifier
                        name: (identifier) @import.name))?
                (namespace_import (identifier) @import.namespace)?
                (identifier)? @import.default) ; Matches default import like 'import React from "react"'
            source: (string) @import.source)

        (import_statement
            source: (string) @import.source) ; Matches side-effect imports like 'import "./styles.css"'

        (import_statement
            (import_clause (identifier) @import.default) ; Matches 'import defaultExport from "module-name";'
            source: (string) @import.source)
    """,
    "classes": """
        (class_declaration
            name: (type_identifier) @class.name
            body: (class_body) @class.body)

        (export_statement
            declaration: (class_declaration
                name: (type_identifier) @class.name
                body: (class_body) @class.body))
    """,
    "interfaces": """
        (interface_declaration
          name: (type_identifier) @interface.name
          body: (interface_body) @interface.body)
        
        (export_statement
          (interface_declaration
            name: (type_identifier) @interface.name
            body: (interface_body) @interface.body))
    """,
    "functions": """
        (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.parameters
            return_type: (_)? @function.return_type
            body: (statement_block) @function.body)

        (export_statement
            declaration: (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.parameters
                return_type: (_)? @function.return_type
                body: (statement_block) @function.body))

        (method_definition
            name: (property_identifier) @function.name ; Treat methods as functions for now
            parameters: (formal_parameters) @function.parameters
            return_type: (_)? @function.return_type
            body: (statement_block) @function.body)

        ; Arrow functions assigned to variables (const myFunction = () => {})
        (lexical_declaration
            (variable_declarator
                name: (identifier) @function.name
                value: (arrow_function
                    parameters: (formal_parameters)? @function.parameters
                    return_type: (_)? @function.return_type
                    body: (_) @function.body)))

        (export_statement
            declaration: (lexical_declaration
                (variable_declarator
                    name: (identifier) @function.name
                    value: (arrow_function
                        parameters: (formal_parameters)? @function.parameters
                        return_type: (_)? @function.return_type
                        body: (_) @function.body))))
    """,
    "enums": """
        (enum_declaration
            name: (identifier) @enum.name
            body: (enum_body) @enum.body)

        (export_statement
            declaration: (enum_declaration
                name: (identifier) @enum.name
                body: (enum_body) @enum.body))
    """
}

def _should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped based on path patterns."""
    return (not file_path.endswith('.ts') and not file_path.endswith('.tsx') or
            'node_modules' in file_path or
            '__tests__' in file_path or
            'test_' in file_path or
            'test.tsx' in file_path or
            'test.ts' in file_path)

def _get_node_text(node: tree_sitter.Node) -> str:
    """Safely decode node text."""
    return node.text.decode('utf8').replace("\n","").replace(" ","") if node else ""

def _process_import(capture: Dict[str, tree_sitter.Node]) -> Dict[str, Any]:
    """Processes an import capture."""
    source = _get_node_text(capture.get("import.source")).strip('"\'')
    imported_items = []
    if "import.name" in capture:
        imported_items.append(_get_node_text(capture["import.name"]))
    if "import.namespace" in capture:
        imported_items.append(f"* as {_get_node_text(capture['import.namespace'])}")
    if "import.default" in capture:
         # Check if it's a default import name or part of named imports
        default_node = capture["import.default"]
        # Simple heuristic: if parent is import_clause and it's the first named child, it's likely the default import
        if default_node.parent and default_node.parent.type == 'import_clause' and default_node.prev_sibling is None:
             imported_items.append(f"default as {_get_node_text(default_node)}")
        elif default_node.type == 'identifier' and 'import.name' not in capture and 'import.namespace' not in capture:
             # Handles cases like 'import defaultExport from "module-name";'
             imported_items.append(f"default as {_get_node_text(default_node)}")


    return {
        "source": source,
        "imported_items": imported_items if imported_items else ["*"], # For side-effect imports or if logic fails
        "start_line": capture.get("import.source", list(capture.values())[0]).start_point[0] + 1,
        "end_line": capture.get("import.source", list(capture.values())[0]).end_point[0] + 1,
    }


def _process_class(capture: Dict[str, tree_sitter.Node]) -> Dict[str, Any]:
    """Processes a class capture."""
    name_node = capture.get("class.name")
    body_node = capture.get("class.body")
    return {
        "name": _get_node_text(name_node),
        "start_line": name_node.start_point[0] + 1 if name_node else 0,
        "end_line": body_node.end_point[0] + 1 if body_node else 0,
    }

def _process_interface(capture: Dict[str, tree_sitter.Node]) -> Dict[str, Any]:
    """Processes an interface capture."""
    name_node = capture.get("interface.name")
    body_node = capture.get("interface.body")
    return {
        "name": _get_node_text(name_node),
        "start_line": name_node.start_point[0] + 1 if name_node else 0,
        "end_line": body_node.end_point[0] + 1 if body_node else 0,
    }

def _process_function(capture: Dict[str, tree_sitter.Node]) -> Dict[str, Any] | None:
    """Processes a function or method capture."""
    name_node = capture.get("function.name")
    if not name_node:
        return None
    params_node = capture.get("function.parameters")
    body_node = capture.get("function.body")
    return_type_node = capture.get("function.return_type")

    # Determine start and end lines carefully
    start_node = name_node if name_node else list(capture.values())[0] # Fallback to first node
    end_node = body_node if body_node else start_node # Fallback to start node if no body

    name = _get_node_text(name_node)
    parameters = _get_node_text(params_node)
    return_type = _get_node_text(return_type_node.child(1)) if return_type_node and return_type_node.child_count > 1 else _get_node_text(return_type_node) # Attempt to get type after ':'

    function_signature = f"{name}{parameters}" + (f": {return_type}" if return_type else "")
    return {
        "function_signature":function_signature,
        "start_line": start_node.start_point[0] + 1,
        "end_line": end_node.end_point[0] + 1,
    }

def _process_enum(capture: Dict[str, tree_sitter.Node]) -> Dict[str, Any]:
    """Processes an enum capture."""
    name_node = capture.get("enum.name")
    body_node = capture.get("enum.body")
    return {
        "name": _get_node_text(name_node),
        "start_line": name_node.start_point[0] + 1 if name_node else 0,
        "end_line": body_node.end_point[0] + 1 if body_node else 0,
    }


def extract_types_and_members_from_file_for_typescript(file_path: str, extract_imports: bool = False) -> TypeScript_Result:
    """
    Parses a TypeScript or TSX file and extracts structural information.

    Args:
        file_path: The path to the TypeScript/TSX file.
        extract_imports: Whether to extract import statements.

    Returns:
        A TypeScript_Result object containing the extracted data.
    """
    result = TypeScript_Result()
    file_extension = os.path.splitext(file_path)[1].lower()
    
    print(f"Parsing file: {file_path} with extension {file_extension}")

    if _should_skip_file(file_path):
        return result

    language = TSX_LANGUAGE if file_extension == ".tsx" else TYPESCRIPT_LANGUAGE
    if not language:
        print(f"Tree-sitter language for {file_extension} not available.")
        return result # Should not happen if __init__ is correct

    parser = tree_sitter.Parser(language=language)

    with open(file_path, "rb") as file:
        source_code = file.read()

    tree = parser.parse(source_code)
    root_node = tree.root_node

    processing_map = {
        "classes": (_process_class, result.classes),
        "interfaces": (_process_interface, result.interfaces),
        "functions": (_process_function, result.functions),
        "enums": (_process_enum, result.enums),
    }
    if extract_imports:
        processing_map["imports"] = (_process_import, result.imports)


    for query_name, (process_func, result_list) in processing_map.items():
        query_string = QUERIES.get(query_name)
        if not query_string:
            continue

        query = language.query(query_string)
        captures: dict[str, list[tree_sitter.Node]] = query.captures(root_node)

        # Process captures, grouping by the start line of the primary node
        processed_captures = {}
        capture_items = captures.items()
        for capture_name, node_list in capture_items:
            # Use the start line of the node that defines the item (e.g., class name, function name)
            # Heuristic: Use the first node in the capture group if specific name isn't found
            for node in node_list:
                primary_node_key = f"{query_name}.name" if f"{query_name}.name" in QUERIES[query_name] else capture_name.split('.')[0] + '.' + capture_name.split('.')[1] # e.g. import.source
                start_line = node.start_point[0]

                # Find the most relevant node for the start line key
                relevant_node_for_key = node
                temp_captures = []
                for cn, n_list in capture_items:
                    # Check if the node is on the same line as the primary node
                    for n in n_list:
                        if n.start_point[0] == start_line:
                            temp_captures.append((n, cn))

                for n_temp, cn_temp in temp_captures:
                    if cn_temp == primary_node_key:
                        relevant_node_for_key = n_temp
                        break
                    # Fallback for imports where 'source' is key
                    if query_name == "imports" and cn_temp == "import.source":
                         relevant_node_for_key = n_temp
                         # Don't break, maybe find a name later

                key = relevant_node_for_key.start_point[0] # Group by the start line of the defining node

                if key not in processed_captures:
                    processed_captures[key] = {}
                processed_captures[key][capture_name] = node

        # Apply processing function to grouped captures
        for key in sorted(processed_captures.keys()):
            processed_item = process_func(processed_captures[key])
            if processed_item: # Ensure item was processed correctly
                 # Avoid duplicates based on name and start line for functions/classes etc.
                 is_duplicate = False
                 if query_name != "imports": # Imports can have same source
                     for existing_item in result_list:
                         if existing_item.get("name") == processed_item.get("name") and \
                            existing_item.get("start_line") == processed_item.get("start_line"):
                             is_duplicate = True
                             break
                 if not is_duplicate:
                    processed_item.pop("start_line", None)
                    processed_item.pop("end_line", None)
                    result_list.append(processed_item)
    return result
