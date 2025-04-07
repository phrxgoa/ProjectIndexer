import os
from tree_sitter import Language, Parser, Query
import tree_sitter_c_sharp

class C_Sharp_Result:
    def __init__(self):
        self.classes = []
        self.structs = []
        self.interfaces = []
        self.enums = []
        self.methods = []
        self.properties = []
        self.fields = []
        
    def __to_dict__(self):
        return {
            'classes': self.classes,
            'structs': self.structs,
            'interfaces': self.interfaces,
            'enums': self.enums,
            'methods': self.methods,
            'properties': self.properties,
            'fields': self.fields
        }

def get_csharp_language():
    language_capsule = tree_sitter_c_sharp.language()
    return Language(language_capsule)

def extract_types_and_members_from_file_for_csharp(file_path: str) -> C_Sharp_Result:
    result = C_Sharp_Result()
    
    if not file_path.endswith('.cs'):
        return result

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    CSHARP_LANGUAGE = get_csharp_language()
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
    """).matches(tree.root_node)

    # Process classes
    for index, class_nodes_dict in CLASS_QUERY:
        # has attributes class_name, bases, class_body, class_def
        class_node = class_nodes_dict['class_def']
        class_info = {
            'name': class_node[0].child_by_field_name('name').text.decode('utf8')
        }
        
        # Get base classes/interfaces
        bases_node = class_nodes_dict.get('bases', None)
        if bases_node:
            class_info['bases'] = [b.text.decode('utf8') for b in bases_node[0].children if b.type != ':']
        
        result.classes.append(class_info)

    # Process structs
    for index, struct_node_dict in STRUCT_QUERY:
        # has attributes struct_name, bases, struct_body
        struct_node = struct_node_dict['struct_def']
        # Get struct name
        struct_info = {
            'name': struct_node[0].child_by_field_name('name').text.decode('utf8')
        }
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

    # Process methods
    for index, method_node_dict in METHOD_QUERY:
        # has attributes method_name, params, return_type, method_body
        method_node = method_node_dict['method_def'][0]
        if not method_node:
            continue
        # Get method name and parameters
        type = method_node.child_by_field_name('type')
        parameters = method_node.child_by_field_name('parameter_list')
            
        method_info = {
            'name': method_node.child_by_field_name('name').text.decode('utf8'),
            'return_type': type.text.decode('utf8') if type else None,
            'parameters': parameters.text.decode('utf8') if parameters else None
        }
        
        # Get modifiers
        modifiers_node = method_node.child_by_field_name('modifiers')
        if modifiers_node:
            method_info['modifiers'] = [m.text.decode('utf8') for m in modifiers_node.children]
        
        result.methods.append(method_info)

    return result

