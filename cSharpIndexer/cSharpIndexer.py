import json
from pathlib import Path
import time
import argparse
import os
import sys

# --- Set Environment Variable for Pythonnet Runtime ---
print("Setting PYTHONNET_RUNTIME=coreclr environment variable...")
os.environ['PYTHONNET_RUNTIME'] = 'coreclr'

# --- Pythonnet Setup ---
try:
    import clr
    print("pythonnet library imported.")
    runtime_env = os.environ.get('PYTHONNET_RUNTIME')
    if runtime_env and runtime_env.lower() == 'coreclr':
        print("Confirmed PYTHONNET_RUNTIME=coreclr is set.")
    else:
        print("Warning: PYTHONNET_RUNTIME might not be 'coreclr'. Issues may occur.")

except ImportError:
    print("Error: pythonnet library not found.")
    print("Please install it using: pip install pythonnet")
    sys.exit(1)
except Exception as e:
    print(f"Error during pythonnet import or runtime check: {e}")
    sys.exit(1)


# --- Load Roslyn Assemblies ---
roslyn_loaded = False
try:
    roslyn_version = "4.8.0"
    target_framework = "netstandard2.0"
    nuget_base_path = Path.home() / ".nuget" / "packages"

    # Construct correct paths for the assemblies
    analysis_common_pkg_path = nuget_base_path / "microsoft.codeanalysis.common" / roslyn_version / "lib" / target_framework
    analysis_dll = analysis_common_pkg_path / "Microsoft.CodeAnalysis.dll"

    csharp_pkg_path = nuget_base_path / "microsoft.codeanalysis.csharp" / roslyn_version / "lib" / target_framework
    csharp_dll = csharp_pkg_path / "Microsoft.CodeAnalysis.CSharp.dll"

    # Debug prints for paths
    print(f"Attempting to load Roslyn v{roslyn_version} from NuGet cache:")
    print(f" - Analysis DLL: {analysis_dll}")
    print(f" - CSharp DLL: {csharp_dll}")

    # Verify paths exist
    if not analysis_dll.exists():
        raise FileNotFoundError(f"Microsoft.CodeAnalysis.dll not found at expected NuGet path: {analysis_dll}")
    if not csharp_dll.exists():
        raise FileNotFoundError(f"Microsoft.CodeAnalysis.CSharp.dll not found at expected NuGet path: {csharp_dll}")

    # Load the assemblies
    clr.AddReference(str(analysis_dll))
    clr.AddReference(str(csharp_dll))
    roslyn_loaded = True
    print("Roslyn assemblies loaded successfully from NuGet cache.")

    # Import namespaces after loading assemblies
    import Microsoft.CodeAnalysis as MSAnalysis
    import Microsoft.CodeAnalysis.CSharp as MSCSharp
    import Microsoft.CodeAnalysis.CSharp.Syntax as MSSyntax
    print("Roslyn namespaces imported successfully.")

except Exception as e:
    print(f"Error: Failed to load or import Roslyn assemblies. {e}")
    sys.exit(1)


def get_parent_context(node):
    """Finds the parent context (namespace, class, etc.) for a given node."""
    parent = node.Parent
    while parent is not None:
        if isinstance(parent, MSSyntax.BaseTypeDeclarationSyntax):  # Class, Struct, Interface, Enum, Record
            return parent.Identifier.ValueText
        elif isinstance(parent, MSSyntax.NamespaceDeclarationSyntax):
            return parent.Name.ToString()
        parent = parent.Parent
    return None


def index_csharp_and_razor_files(root_dir, output_file="ProjectIndex.json"):
    """Indexes C# and Razor files in the given directory."""
    start_time = time.time()
    all_definitions = []
    root_path = Path(root_dir).resolve()

    print(f"Starting indexing in: {root_path}")

    # Find all .cs and .razor files
    all_files = list(root_path.rglob("*.cs")) + list(root_path.rglob("*.razor"))
    print(f"Found {len(all_files)} .cs and .razor files.")

    excluded_dir_names = {"obj", "bin"}
    files_to_process = [f for f in all_files if not any(part.lower() in excluded_dir_names for part in f.parts)]

    for file_path in files_to_process:
        relative_path_str = str(file_path.relative_to(root_path)).replace("\\", "/")
        file_extension = file_path.suffix.lower()

        try:
            content = file_path.read_text(encoding="utf-8")

            if file_extension == ".cs":
                parse_options = MSCSharp.CSharpParseOptions(languageVersion=MSCSharp.LanguageVersion.Latest)
                syntax_tree = MSCSharp.CSharpSyntaxTree.ParseText(content, options=parse_options, path=str(file_path))
                root = syntax_tree.GetRoot()
                
                for node in root.DescendantNodes():
                    # Only index high-level definitions
                    if isinstance(node, MSSyntax.ClassDeclarationSyntax):
                        name = node.Identifier.ValueText
                        parent = get_parent_context(node)
                        # Add class definition as [name, path, parent]
                        all_definitions.append([name, relative_path_str, parent])
                    elif isinstance(node, MSSyntax.NamespaceDeclarationSyntax):
                        name = node.Name.ToString()
                        # Add namespace definition as [name, path, None]
                        all_definitions.append([name, relative_path_str, None])

            elif file_extension == ".razor":
                # Add Razor file path only as a string
                all_definitions.append(relative_path_str)

        except Exception as e:
            print(f"Error processing file {relative_path_str}: {e}")

    # Output results
    try:
        output_path = root_path / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_definitions, f, separators=(',', ':'))  # Compact JSON formatting
        print(f"Indexing completed successfully. Output written to {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")

    print(f"Indexing completed in {time.time() - start_time:.2f} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index C# and Razor project definitions.")
    parser.add_argument(
        "root_dir",
        nargs="?",
        default=".",
        help="Root directory of the C# project/solution (default: current directory)."
    )
    parser.add_argument(
        "-o", "--output",
        default="ProjectIndex.json",
        help="Output JSON file name (default: ProjectIndex.json)."
    )
    args = parser.parse_args()

    target_dir = Path(args.root_dir)
    if not target_dir.is_dir():
        print(f"Error: Provided root directory '{args.root_dir}' not found or is not a directory.")
        sys.exit(1)

    index_csharp_and_razor_files(target_dir, args.output)