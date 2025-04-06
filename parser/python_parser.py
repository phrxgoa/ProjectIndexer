import ast

class Python_Result:
    def __init__(self):
        self.py_classes = []
        self.py_functions = []
        self.py_imports = []

    # Convert the result to a dictionary for easy serialization
    def __to_dict__(self):
        # Convert each list of objects to a dictionary but on
        result = {}
        if self.py_classes:
            result['py_classes'] = self.py_classes
        if self.py_functions:
            result['py_functions'] = self.py_functions
        if self.py_imports:
            result['py_imports'] = self.py_imports
        return result

def extract_arg(arg):
    type_annotation = "" if not arg.annotation else f": {ast.unparse(arg.annotation)}"
    return f"{arg.arg}{type_annotation}"

def extract_func_info(node, parent_class=None):
    # create string like "func_name(self, arg1: type, arg2: type) -> return_type"
    function_signature = f"{node.name}({','.join([extract_arg(arg) for arg in node.args.args])}) -> {ast.unparse(node.returns) if node.returns else 'None'}"
    return function_signature

def extract_class_info(class_node):
    result = {}
    if class_node.name:
        result['name'] = class_node.name
    if class_node.bases:
        result['bases'] = [ast.unparse(base) for base in class_node.bases]
    # Extract methods from the class body
    methods = [
            extract_func_info(item, parent_class=class_node.name)
            for item in class_node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    # Add methods to the result
    if methods:
        result['methods'] = methods
    return result

def extract_types_and_members_from_file_for_python(file_path: str, extract_imports: bool = False) -> Python_Result:
    result = Python_Result()
    
    # Ignore non-Python files
    if not file_path.endswith('.py'):
        return result
    # Ignore venv and __pycache__ directories
    if 'venv' in file_path or '__pycache__' in file_path:
        return result
    # Ignore files starting with test_ or ending with _test.py
    if file_path.__contains__('_test.py') or file_path.__contains__('test_'):
        return result
    # Read the file and parse the AST
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code, filename=file_path)

        for node in ast.iter_child_nodes(tree):
            # Imports
            if extract_imports and isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        result.py_imports.append(f"{alias.name} as {alias.asname}")
                    else:
                        result.py_imports.append(alias.name)

            elif extract_imports and isinstance(node, ast.ImportFrom):
                # aggregate all imports from the same module
                imported_names = ",".join([alias.name for alias in node.names])
                result.py_imports.append(f"from {node.module} import {imported_names}")

            # Classes and Methods
            elif isinstance(node, ast.ClassDef):
                class_info = extract_class_info(node)
                result.py_classes.append(class_info)

            # Top-level functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = extract_func_info(node)
                result.py_functions.append(func_info)

        return result
    except SyntaxError as e:
        print(f"Syntax error in file {file_path}: {e}")
        return result
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return result
    finally:
        # Close the file if it was opened
        if 'f' in locals():
            f.close()
        pass