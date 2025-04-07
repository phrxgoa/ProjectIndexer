import os
from tree_sitter import Parser, Query
from . import CSHARP_LANGUAGE

class C_Sharp_Result:
    def __init__(self):
        self.classes = []
        self.structs = []
        self.interfaces = []
        self.enums = []
        self.methods = []  # Flat list for backward compatibility
        
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
        if self.methods:
            result['methods'] = self.methods  # Maintain flat list
        return result
    
    
def process_method_node(method_node):
    if not method_node:
        return None
        
    method_info = {}
    # Get method name
    method_info['name'] = method_node.child_by_field_name('name').text.decode('utf8')
    # Get parameters
    raw_parameters = method_node.child_by_field_name('parameters')
    parameters = ','.join([p.text.decode('utf8') for p in raw_parameters.children if p.type == 'parameter'])
    if len(parameters) > 0:
        method_info['parameters'] = parameters
    # Get return type
    type = method_node.child_by_field_name('type')
    if type:
        method_info['return_type'] = type.text.decode('utf8')
    # Get modifiers
    modifiers_node = method_node.child_by_field_name('modifiers')
    if modifiers_node:
        method_info['modifiers'] = [m.text.decode('utf8') for m in modifiers_node.children]
    return method_info

def extract_types_and_members_from_file_for_csharp(file_path: str) -> C_Sharp_Result:
    result = C_Sharp_Result()
    
    # File reading operations
    try:
        if not file_path.endswith('.cs'):
            return result

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        if not source_code:
            return result
            
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return result
    
    # Initialize Tree-sitter parser
    parser = Parser(language=CSHARP_LANGUAGE)
    tree = parser.parse(bytes(source_code, 'utf8'))

    # Tree-sitter queries for C#
    CLASS_QUERY = CSHARP_LANGUAGE.query("""
        (class_declaration
            name: (identifier) @class_name
            (base_list)? @bases
            body: (declaration_list) @class_body) @class_def
    """).matches(tree.root_node)

    STRUCT_QUERY = Query(CSHARP_LANGUAGE, """
        (struct_declaration
            name: (identifier) @struct_name
            (base_list)? @bases
            body: (declaration_list) @struct_body) @struct_def
    """).matches(tree.root_node)

    INTERFACE_QUERY = Query(CSHARP_LANGUAGE, """
        (interface_declaration
            name: (identifier) @interface_name
            (base_list)? @bases
            body: (declaration_list) @interface_body) @interface_def
    """).matches(tree.root_node)

    ENUM_QUERY = Query(CSHARP_LANGUAGE, """
        (enum_declaration
            name: (identifier) @enum_name
            body: (enum_member_declaration_list) @enum_body) @enum_def
    """).matches(tree.root_node)

    METHOD_QUERY = Query(CSHARP_LANGUAGE, """
        (method_declaration
            (type)? @return_type
            name: (identifier) @method_name
            (parameter_list) @params
            body: (block)? @method_body) @method_def
    """)

    # Process classes
    for index, class_nodes_dict in CLASS_QUERY:
        # has attributes class_name, bases, class_body, class_def
        class_node = class_nodes_dict['class_def'][0]
        class_info = {
            'name': class_node.child_by_field_name('name').text.decode('utf8')
        }
        
        # Get base classes/interfaces
        bases_node = class_nodes_dict.get('bases', None)
        if bases_node:
            # add concatenated bases
            bases = [b.text.decode('utf8') for b in bases_node[0].children if b.type != ':']
            class_info['bases'] = "".join(bases)
        
        # Process methods within class
        methods = []
        body_node = class_node.child_by_field_name('body')
        method_matches = list(METHOD_QUERY.matches(body_node))
        for method_index, method_nodes_dict in method_matches:
            method_node = method_nodes_dict['method_def'][0]
            method_info = process_method_node(method_node)
            methods.append(method_info)
            result.methods.append(method_info)  # Maintain flat list
            
        if methods:
            class_info['methods'] = methods
            
        result.classes.append(class_info)
    # Process structs
    for index, struct_node_dict in STRUCT_QUERY:
        # has attributes struct_name, bases, struct_body
        struct_node = struct_node_dict['struct_def'][0]
        struct_info = {
            'name': struct_node.child_by_field_name('name').text.decode('utf8')
        }
        
        # Process methods within struct
        methods = []
        body_node = struct_node.child_by_field_name('body')
        method_matches = METHOD_QUERY.matches(body_node)
        for method_index, method_nodes_dict in method_matches:
            method_node = method_nodes_dict['method_def'][0]
            method_info = process_method_node(method_node)
            methods.append(method_info)
            result.methods.append(method_info)  # Maintain flat list
            
        if methods:
            struct_info['methods'] = methods
            
        result.structs.append(struct_info)

    # Process interfaces
    for index, interface_node_dict in INTERFACE_QUERY:
        # has attributes interface_name, bases, interface_body
        interface_node = interface_node_dict['interface_def']
        # Get interface name
        interface_info = {
            'name': interface_node[0].child_by_field_name('name').text.decode('utf8')
        }
        result.interfaces.append(interface_info)

    # Process enums
    for index, enum_node_dict in ENUM_QUERY:
        # has attributes enum_name, enum_body
        enum_node = enum_node_dict['enum_def']
        # Get enum name
        enum_info = {
            'name': enum_node[0].child_by_field_name('name').text.decode('utf8')
        }
        result.enums.append(enum_info)

    # Process top-level methods
    for index, method_node_dict in METHOD_QUERY.matches(tree.root_node):
        method_node = method_node_dict['method_def'][0]
        # Skip if method is inside a class or struct
        if method_node.parent and method_node.parent.type in ('class_declaration', 'struct_declaration'):
            continue
            
        method_info = process_method_node(method_node)
        if method_info:
            result.methods.append(method_info)

    return result

