import ast

class Python_Result:
    def __init__(self):
        self.py_classes = []
        self.py_functions = []
        self.py_library_imports = []
        self.py_library_imports_as = []
        self.py_method_imports = []

    def __to_dict__(self):
        return {
            'py_classes': self.py_classes,
            'py_functions': self.py_functions,
            'py_library_imports': self.py_library_imports,
            'py_library_imports_as': self.py_library_imports_as,
            'py_method_imports': self.py_method_imports
        }

def extract_types_and_members_from_file_for_python(file_path: str) -> Python_Result:
    result = Python_Result()

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=file_path)

    def extract_func_info(node, parent_class=None):
        def extract_arg(arg):
            type_annotation = "" if not arg.annotation else f": {ast.unparse(arg.annotation)}"
            return {
                "name": f"{arg.arg}{type_annotation}"
            }

        return {
            "name": node.name,
            "args": [extract_arg(arg) for arg in node.args.args],
            "returns": ast.unparse(node.returns) if node.returns else None,
        }

    def extract_class_info(class_node):
        return {
            "name": class_node.name,
            "methods": [
                extract_func_info(item, parent_class=class_node.name)
                for item in class_node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
            "bases": [ast.unparse(base) for base in class_node.bases],
        }

    for node in ast.iter_child_nodes(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    result.py_library_imports_as.append(f"{alias.name} as {alias.asname}")
                else:
                    result.py_library_imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                result.py_method_imports.append(f"from {node.module} import {alias.name}")

        # Classes and Methods
        elif isinstance(node, ast.ClassDef):
            class_info = extract_class_info(node)
            result.py_classes.append(class_info)

        # Top-level functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_info = extract_func_info(node)
            result.py_functions.append(func_info)

    return result