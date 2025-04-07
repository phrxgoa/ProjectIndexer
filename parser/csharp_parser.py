import os
from tree_sitter import Parser, Query
from . import CSHARP_LANGUAGE

# Query definitions as class-level constants
CLASS_QUERY_STR = """
    (class_declaration
        name: (identifier) @class_name
        (base_list)? @bases
        body: (declaration_list) @class_body) @class_def
"""

STRUCT_QUERY_STR = """
    (struct_declaration
        name: (identifier) @struct_name
        (base_list)? @bases
        body: (declaration_list) @struct_body) @struct_def
"""

INTERFACE_QUERY_STR = """
    (interface_declaration
        name: (identifier) @interface_name
        (base_list)? @bases
        body: (declaration_list) @interface_body) @interface_def
"""

ENUM_QUERY_STR = """
    (enum_declaration
        name: (identifier) @enum_name
        body: (enum_member_declaration_list) @enum_body) @enum_def
"""

METHOD_QUERY_STR = """
    (method_declaration
        (type)? @return_type
        name: (identifier) @method_name
        (parameter_list) @params
        body: (block)? @method_body) @method_def
"""

class C_Sharp_Result:
    def __init__(self):
        self.classes = []
        self.structs = []
        self.interfaces = []
        self.enums = []
        
    def __to_dict__(self):
        result = {}
        if self.classes:
            result['classes'] = self.classes
        if self.structs:
            result['structs'] = self.structs
        if self.interfaces:
            result['interfaces'] = self.interfaces
        if self.enums:
            result['enums'] = self.enums
        return result
    
def process_method_node(method_node):
    """Process a method node and extract its information.
    
    Args:
        method_node: The tree-sitter node representing a method
        
    Returns:
        dict: Method information including name, parameters, return type and modifiers
    """
    if not method_node:
        return None
        
    method_info = {}
    method_info['name'] = method_node.child_by_field_name('name').text.decode('utf8')
    
    raw_parameters = method_node.child_by_field_name('parameters')
    parameters = ','.join([p.text.decode('utf8') for p in raw_parameters.children if p.type == 'parameter'])
    if len(parameters) > 0:
        method_info['parameters'] = parameters
        
    type = method_node.child_by_field_name('type')
    if type:
        method_info['return_type'] = type.text.decode('utf8')
        
    modifiers_node = method_node.child_by_field_name('modifiers')
    if modifiers_node:
        method_info['modifiers'] = [m.text.decode('utf8') for m in modifiers_node.children]
    return method_info

def _read_and_validate_file(file_path: str) -> str:
    """Read and validate a C# source file.
    
    Args:
        file_path: Path to the C# file
        
    Returns:
        str: The file content if valid, None otherwise
    """
    try:
        if not file_path.endswith('.cs'):
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        return source_code if source_code else None
            
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def _initialize_parser(source_code: str) -> tuple:
    """Initialize the tree-sitter parser and parse the source code.
    
    Args:
        source_code: The C# source code to parse
        
    Returns:
        tuple: (Parser, Tree) objects
    """
    parser = Parser(language=CSHARP_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))
    return parser, tree

def _process_class(struct_node, method_query, result):
    """Process a class node and extract its information.
    
    Args:
        class_node: The tree-sitter node representing a class
        method_query: The method query object
        result: The C_Sharp_Result object to populate
        
    Returns:
        dict: Class information including name, bases and methods
    """
    class_info = {
        'name': struct_node.child_by_field_name('name').text.decode('utf8')
    }
    
    bases_node = struct_node.child_by_field_name('bases')
    if bases_node:
        bases = [b.text.decode('utf8') for b in bases_node.children if b.type != ':']
        class_info['bases'] = "".join(bases)
    
    methods = []
    body_node = struct_node.child_by_field_name('body')
    for _, method_nodes_dict in method_query.matches(body_node):
        method_node = method_nodes_dict['method_def'][0]
        method_info = process_method_node(method_node)
        methods.append(method_info)
        
    if methods:
        class_info['methods'] = methods
        
    return class_info

def _process_struct(struct_node, method_query, result):
    """Process a struct node and extract its information.
    
    Args:
        struct_node: The tree-sitter node representing a struct
        method_query: The method query object
        result: The C_Sharp_Result object to populate
        
    Returns:
        dict: Struct information including name and methods
    """
    struct_info = {
        'name': struct_node.child_by_field_name('name').text.decode('utf8')
    }
    
    methods = []
    body_node = struct_node.child_by_field_name('body')
    for _, method_nodes_dict in method_query.matches(body_node):
        method_node = method_nodes_dict['method_def'][0]
        method_info = process_method_node(method_node)
        methods.append(method_info)
        
    if methods:
        struct_info['methods'] = methods
        
    return struct_info

def _process_interface(interface_node):
    """Process an interface node and extract its name.
    
    Args:
        interface_node: The tree-sitter node representing an interface
        
    Returns:
        dict: Interface information with name
    """
    return {
        'name': interface_node.child_by_field_name('name').text.decode('utf8')
    }

def _process_enum(enum_node):
    """Process an enum node and extract its name.
    
    Args:
        enum_node: The tree-sitter node representing an enum
        
    Returns:
        dict: Enum information with name
    """
    return {
        'name': enum_node.child_by_field_name('name').text.decode('utf8')
    }

def extract_types_and_members_from_file_for_csharp(file_path: str) -> C_Sharp_Result:
    """Extract types and members from a C# source file.
    
    Args:
        file_path: Path to the C# file
        
    Returns:
        C_Sharp_Result: Object containing all extracted types and members
    """
    result = C_Sharp_Result()
    
    # Read and validate file
    source_code = _read_and_validate_file(file_path)
    if not source_code:
        return result
    
    # Initialize parser and parse source code
    parser, tree = _initialize_parser(source_code)
    
    # Create queries
    class_query = CSHARP_LANGUAGE.query(CLASS_QUERY_STR).matches(tree.root_node)
    struct_query = Query(CSHARP_LANGUAGE, STRUCT_QUERY_STR).matches(tree.root_node)
    interface_query = Query(CSHARP_LANGUAGE, INTERFACE_QUERY_STR).matches(tree.root_node)
    enum_query = Query(CSHARP_LANGUAGE, ENUM_QUERY_STR).matches(tree.root_node)
    # this one doesn't match the root node directly, because the query is for methods inside classes/structs as well 
    # as top-level methods
    method_query = Query(CSHARP_LANGUAGE, METHOD_QUERY_STR)
    
    # Process classes
    for _, class_nodes_dict in class_query:
        class_node = class_nodes_dict['class_def'][0]
        class_info = _process_class(class_node, method_query, result)
        result.classes.append(class_info)
    
    # Process structs
    for _, struct_node_dict in struct_query:
        struct_node = struct_node_dict['struct_def'][0]
        struct_info = _process_struct(struct_node, method_query, result)
        result.structs.append(struct_info)
    
    # Process interfaces
    for _, interface_node_dict in interface_query:
        interface_node = interface_node_dict['interface_def'][0]
        interface_info = _process_interface(interface_node)
        result.interfaces.append(interface_info)
    
    # Process enums
    for _, enum_node_dict in enum_query:
        enum_node = enum_node_dict['enum_def'][0]
        enum_info = _process_enum(enum_node)
        result.enums.append(enum_info)
    
    return result

