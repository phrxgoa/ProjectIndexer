import timeit
import time
from parser.csharp_parser import extract_types_and_members_from_file_for_csharp as tree_sitter_parse
from parser.csharp_parser import C_Sharp_Result as TreeSitterResult

# Backup old implementation for comparison
def regex_parse(file_path: str) -> TreeSitterResult:
    import re
    patterns_csharp = {
        'classes': re.compile(r'\bclass\s+(\w+)(?=\s*[:{])'),
        'structs': re.compile(r'\bstruct\s+(\w+)(?=\s*[:{])'),
        'interfaces': re.compile(r'\binterface\s+(\w+)(?=\s*[:{])'),
        'enums': re.compile(r'\benum\s+(\w+)(?=\s*[{])'),
        'methods': re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:[\w\<\>\[\]]+\s+)+(\w+)\s*\([^)]*\)\s*(?=\{|=>)')
    }
    
    results = TreeSitterResult()
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        for key, pattern in patterns_csharp.items():
            matches = pattern.findall(content)
            if not matches:
                continue
            for match in matches:
                getattr(results, key).append(match)
    return results

def benchmark_parser(parser_func, file_path: str, iterations: int = 100):
    start_time = time.time()
    
    # Warm up
    for _ in range(5):
        parser_func(file_path)
    
    # Time individual runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        parser_func(file_path)
        end = time.perf_counter()
        times.append(end - start)
    
    total_time = time.time() - start_time
    avg_time = sum(times) / iterations
    min_time = min(times)
    max_time = max(times)
    
    return {
        'total_time': total_time,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'iterations': iterations
    }

if __name__ == '__main__':
    test_file = 'test.cs'
    iterations = 100
    
    print("Benchmarking Tree-sitter parser...")
    ts_results = benchmark_parser(tree_sitter_parse, test_file, iterations)
    print(f"Tree-sitter results: {ts_results}")
    
    print("\nBenchmarking Regex parser...")
    regex_results = benchmark_parser(regex_parse, test_file, iterations)
    print(f"Regex results: {regex_results}")
    
    print("\nComparison:")
    print(f"Tree-sitter is {regex_results['avg_time'] / ts_results['avg_time']:.2f}x faster than Regex")
    print(f"Tree-sitter parsed {iterations} files in {ts_results['total_time']:.4f}s")
    print(f"Regex parsed {iterations} files in {regex_results['total_time']:.4f}s")
    
    # Print actual parsing results for verification
    print("\nTree-sitter parse results:")
    print(tree_sitter_parse(test_file).__to_dict__())
    
    print("\nRegex parse results:")
    print(regex_parse(test_file).__to_dict__())