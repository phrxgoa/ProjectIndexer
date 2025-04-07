import os
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_c_sharp

# Initialize Tree-sitter languages
PYTHON_LANGUAGE = None
CSHARP_LANGUAGE = None

def initialize_grammars():
    """Initialize Tree-sitter language grammars"""
    global PYTHON_LANGUAGE, CSHARP_LANGUAGE
    
    try:
        PYTHON_LANGUAGE = Language(tree_sitter_python.language())
    except Exception as e:
        raise RuntimeError(f"Failed to load Python grammar: {e}")

    try:
        CSHARP_LANGUAGE = Language(tree_sitter_c_sharp.language())
    except Exception as e:
        raise RuntimeError(f"Failed to load C# grammar: {e}")

def grammars_loaded():
    """Check if grammars are loaded"""
    return PYTHON_LANGUAGE is not None and CSHARP_LANGUAGE is not None

# Initialize grammars when module is imported
initialize_grammars()

# Import parser functions
from .parser import *
from .python_parser import *
from .csharp_parser import *