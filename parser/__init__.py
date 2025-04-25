import os
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_c_sharp
import tree_sitter_typescript
import tree_sitter_javascript

# Initialize Tree-sitter languages
PYTHON_LANGUAGE = None
CSHARP_LANGUAGE = None
TYPESCRIPT_LANGUAGE = None
TSX_LANGUAGE = None
JAVASCRIPT_LANGUAGE = None

def initialize_grammars():
    """Initialize Tree-sitter language grammars"""
    global PYTHON_LANGUAGE, CSHARP_LANGUAGE, TYPESCRIPT_LANGUAGE, TSX_LANGUAGE, JAVASCRIPT_LANGUAGE
    
    try:
        PYTHON_LANGUAGE = Language(tree_sitter_python.language())
    except Exception as e:
        raise RuntimeError(f"Failed to load Python grammar: {e}")

    try:
        CSHARP_LANGUAGE = Language(tree_sitter_c_sharp.language())
    except Exception as e:
        raise RuntimeError(f"Failed to load C# grammar: {e}")

    try:
        TYPESCRIPT_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
    except Exception as e:
        raise RuntimeError(f"Failed to load TypeScript grammar: {e}")

    try:
        TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
    except Exception as e:
        raise RuntimeError(f"Failed to load TSX grammar: {e}")
    
    try:
        JAVASCRIPT_LANGUAGE = Language(tree_sitter_javascript.language())
    except Exception as e:
        raise RuntimeError(f"Failed to load JavaScript grammar: {e}")

def grammars_loaded():
    """Check if grammars are loaded"""
    return (PYTHON_LANGUAGE is not None and
            CSHARP_LANGUAGE is not None and
            TYPESCRIPT_LANGUAGE is not None and
            TSX_LANGUAGE is not None and 
            JAVASCRIPT_LANGUAGE is not None)

# Initialize grammars when module is imported
initialize_grammars()

# Import parser functions
from .parser import *
from .python_parser import *
from .csharp_parser import *
from .typescript_parser import * # Added for future TypeScript parser
from .javascript_parser import * # Added for future TypeScript parser