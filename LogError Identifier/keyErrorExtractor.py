import re

def parse_failed_tests(log_content):
    # Patterns for test names and errors
    test_pattern = r"_{5,}\s+(test_[\w_]+)\s+_{5,}"
    path_pattern = r"([\/\w-]+\.py):(\d+)"
    type_error_pattern = r"TypeError: An asyncio\.Future, a coroutine or an awaitable is required"
    
    failed_tests = []
    current_test = None
    current_path = None
    error_context_lines = []
    in_error_section = False
    
    # Split log into lines
    lines = log_content.split('\n')
    
    for i, line in enumerate(lines):
        # Look for test name
        test_match = re.search(test_pattern, line)
        if test_match:
            current_test = test_match.group(1)
            in_error_section = False
            error_context_lines = []
            
        # Look for file path
        path_match = re.search(path_pattern, line)
        if path_match:
            current_path = path_match.group(1)
        
        # Store context lines
        if current_test:
            error_context_lines.append(line.strip())
            
        # Check for errors
        if current_test and ("KeyError:" in line or re.search(type_error_pattern, line)):
            in_error_section = True
            error_type = "KeyError" if "KeyError:" in line else "TypeError"
            
            # Clean up the path
            if current_path:
                clean_path = re.search(r'(?:^|/)(?:test/.+|plenum/test/.+)$', current_path)
                test_path = clean_path.group(0) if clean_path else current_path
                test_path = test_path.lstrip('/')
            else:
                test_path = "path not found"
            
            # Get the error context (lines leading up to error)
            context_window = 10  # Increase context window for better visibility
            error_context = []
            start_idx = max(0, len(error_context_lines) - context_window)
            for j in range(start_idx, len(error_context_lines)):
                if error_context_lines[j]:  # Only add non-empty lines
                    error_context.append(error_context_lines[j])
            
            failed_tests.append({
                'test_name': current_test,
                'test_path': test_path,
                'error_type': error_type,
                'error_line': line.strip(),
                'error_context': '\n'.join(error_context)
            })
            
        # Reset for next test
        if in_error_section and line.strip() == "" and current_test:
            in_error_section = False
            error_context_lines = []
            
    return failed_tests

def main():
    try:
        # Read log file
        with open('test-result-plenum-2.txt', 'r') as f:
            log_content = f.read()
        
        # Get failed tests
        failed_tests = parse_failed_tests(log_content)
        
        # Print results
        if failed_tests:
            print(f"Found {len(failed_tests)} test failures:\n")
            
            # Group failures by error type
            key_errors = [t for t in failed_tests if t['error_type'] == 'KeyError']
            type_errors = [t for t in failed_tests if t['error_type'] == 'TypeError']
            
            if key_errors:
                print(f"KeyError Failures ({len(key_errors)}):")
                print("=" * 80)
                for i, test in enumerate(key_errors, 1):
                    print(f"Failure #{i}:")
                    print(f"Test Name: {test['test_name']}")
                    print(f"Test Path: {test['test_path']}")
                    print("Error Context:")
                    print(test['error_context'])
                    print("-" * 80 + "\n")
            
            if type_errors:
                print(f"\nTypeError Failures ({len(type_errors)}):")
                print("=" * 80)
                for i, test in enumerate(type_errors, 1):
                    print(f"Failure #{i}:")
                    print(f"Test Name: {test['test_name']}")
                    print(f"Test Path: {test['test_path']}")
                    print("Error Context:")
                    print(test['error_context'])
                    print("-" * 80 + "\n")
                    
        else:
            print("No test failures found")
            
    except FileNotFoundError:
        print("Error: test_log.txt file not found")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
