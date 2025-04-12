# Project Indexer

## Overview

`Project Indexer` is a simple script designed to index the locations of classes, files, and other components within a project. This indexing allows **Large Language Models (LLMs)** to quickly understand the project's structure, enabling **D.R.Y. (Don't Repeat Yourself) coding** by preventing redundant object creation and avoiding full project scans.

By providing an organized index, `Project Indexer` enhances the LLM's understanding from the outset. When combined with a **well-structured design document** containing patterns and examples, it facilitates **efficient onboarding** for new tasks or ongoing development in an active codebase.

The tool currently supports both C# and Python files, with specialized regex patterns for each language's syntax. The index includes:

- For C#: classes, structs, interfaces, enums, and methods
- For Python:
  - Classes (including decorated classes)
  - Functions (including decorated functions)
  - Methods (instance, class and static methods)
  - Imports (absolute and relative)
  - Docstrings (as metadata)


## Why Use ProjectIndexer?

- **Reduces unnecessary LLM scanning**: Saves token usage compared to constant back-and-forth querying.
- **Prevents hallucinations**: Helps LLMs recognize what exists in the codebase.
- **Speeds up development**: Ideal for large projects with many files and classes.
- **Compatible with multiple LLMs**, including:
  - RooCode - the Awesome VSCode AI Developement Extension.
  - Gemini (All)
  - Sonnet (All)
  - o3-mini and o3-mini-high
  - Deepseek V3.1 & Deepseek R1
  - GPT models
  - Grok

## Features

- **Creates** a **.json file** listing class names, methods and locations
- **Multi-language support**: Works with both C# and Python codebases
- **Tree-sitter parsing**: More accurate than regex for complex syntax cases
- **Lightweight**: Only indexes names and locations, not full class properties or implementations
- **Supports integration with RooCode**: In some cases, you can configure `Code/Architect` mode to frequently refer to `ProjectIndex.json`. You may also set it to **run periodically** upon reaching milestones or creating new tasks

> **Note:** This tool was built for personal use due to managing a **VS Solution with 5 projects and over 600 classes/methods**.

## Parser Architecture

The project uses a modular parser system with Tree-sitter for accurate syntax parsing:

- `parser/__init__.py`: Main parser interface and Tree-sitter grammar initialization
- `parser/csharp_parser.py`: Handles C# specific parsing using Tree-sitter
- `parser/python_parser.py`: Handles Python specific parsing using Tree-sitter

Each parser implements:

- File extension detection
- Tree-sitter based parsing with language grammars
- Common output format (JSON)

### Tree-sitter Integration

The project now uses [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) for more accurate parsing:

- **Pre-loaded grammars** for Python and C# at startup
- **Faster parsing** by avoiding regex pattern matching
- **More reliable** extraction of code structures
- **Better handling** of complex syntax cases

Required dependencies (automatically installed via requirements.txt):

- tree-sitter==0.24.0
- tree-sitter-python==0.23.6
- tree-sitter-c-sharp==0.23.1

## Installation & Usage

1. Drop `Project_Indexer.py` into the root of your project

2. Configure the root directory:

   - Open `Project_Indexer.py`
   - On line 54, set `root_directory` to your project's root path
   - Example for Windows: `"C:\\MyProject"`
   - Example for Mac/Linux: `"/Users/name/MyProject"`

3. Run the script via command line:

```sh
# Using --path argument to specify project directory
python Project_Indexer.py --path /path/to/your/project
# Using --imports to specify extracting imported libraries/methods in each file (only supported for python right now)
python Project_Indexer.py --path /path/to/your/project --imports
# Without arguments (uses hardcoded path in script)
python Project_Indexer.py
```

3.  The script will generate `ProjectIndex.json`.

4.  Direct your LLM to read `ProjectIndex.json` for efficient project awareness.

## C# Project Indexer

1. This is a highly specialized indexer for **C# files only**. It also reads and indexes `.razor` files for Blazor projects.
2. It uses the **PythonNET** library to interface with **Roslyn analyzers** to "walk the tree," resulting in a highly compressed `ProjectIndex.json` file.
3. Place the script in the **root directory** of your project.
4. Run the following command to generate the index:
   ```python cSharpIndexer.py ```
5. If Roslyn dependencies are missing, the script will attempt to install them automatically. Manual installation may be required in some cases.
6. Pull requests and contributions are welcome — this tool is highly experimental.



I hope this is useful.

Happy coding!

## Contributing

Feel free to fork the repository and submit pull requests for improvements!

## License

This project is licensed under the [MIT License](LICENSE).

---
