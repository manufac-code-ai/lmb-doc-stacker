import os
import shutil
import logging
import argparse
import csv
import re
import statistics  # Add this import for median calculation
from pathlib import Path
from datetime import datetime
from collections import Counter
import config  # Add this import with the other imports

# Import field definitions from the validation_fields module
from validation_fields import REQUIRED_FIELDS, FIELD_ALTERNATIVES, get_plain_field_name

def normalize_markdown_content(content):
    normalized = content
    
    # 1. First fix bold fields with colons/question marks outside the bold markers
    normalized = re.sub(r'\*\*(.*?)\*\*:', r'**\1:**', normalized)
    normalized = re.sub(r'\*\*(.*?)\*\*\?', r'**\1?**', normalized)
    
    # 2. Case-insensitive field normalization with exact patterns for problematic fields
    replacements = [
        # Next steps variations (both ? and : variants)
        (r'\*\*Next Steps\?\*\*', r'**Next steps?**'),
        (r'\*\*Next Steps:\*\*', r'**Next steps?**'),
        (r'\*\*Next steps:\*\*', r'**Next steps?**'),
        
        # Issue resolved variations 
        (r'\*\*Issue Resolved\?\*\*', r'**Issue resolved?**'),
        (r'\*\*Issue resolved:\*\*', r'**Issue resolved?**'),
        (r'\*\*Issues resolved:\*\*', r'**Issue resolved?**'),
        (r'\*\*Issues Resolved\?\*\*', r'**Issue resolved?**'),
        
        # Description problem/problems variations (with precise colon handling)
        (r'\*\*Description of problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Description of Problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Descriptions of problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Descriptions of Problems:\*\*', r'**Description of problem:**'),
        
        # Description of work performed variations
        (r'\*\*Description of Work Performed:\*\*', r'**Description of work performed:**'),
        (r'\*\*Description of work Performed:\*\*', r'**Description of work performed:**'),
    ]
    
    # Apply each replacement
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 3. Replace alternative field names with canonical ones
    for canonical_field, alternatives in FIELD_ALTERNATIVES.items():
        for alt_field in alternatives:
            normalized = normalized.replace(alt_field, canonical_field)
    
    return normalized

def setup_logger(log_file='report_validation.log'):
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def validate_report(file_path):
    """
    Validate a markdown report file against the required structure.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        tuple: (is_valid, list_of_error_codes)
    """
    error_codes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            
            # Apply normalization preprocessing
            normalized_content = normalize_markdown_content(original_content)
            
            # First check if there are any fields at all (for UNSTRUCTURED_DOCUMENT)
            has_any_fields = False
            for field in REQUIRED_FIELDS:
                plain_field = field.replace('**', '')
                if plain_field in normalized_content:
                    has_any_fields = True
                    break
                
            if not has_any_fields:
                error_codes.append("UNSTRUCTURED_DOCUMENT")
                return False, error_codes
            
            # Check for presence of each required field
            for field in REQUIRED_FIELDS:
                plain_field = field.replace('**', '')
                
                if field not in normalized_content:
                    # Field is missing or not formatted correctly
                    if plain_field in normalized_content:
                        # Field exists but not bolded
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"UNBOLDED_FIELD:{field_name}")
                    else:
                        # Field is completely missing (even after normalization)
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"MISSING_FIELD:{field_name}")
            
            # Check for duplicated fields
            for field in REQUIRED_FIELDS:
                occurrences = normalized_content.count(field)
                if occurrences > 1:
                    field_name = get_plain_field_name(field)
                    error_codes.append(f"DUPLICATE_FIELD:{field_name}")
            
            # Check for empty fields (optional feature)
            for field in REQUIRED_FIELDS:
                if field in normalized_content:
                    field_pos = normalized_content.find(field) + len(field)
                    # Look for the next field or end of content
                    next_field_pos = float('inf')
                    for other_field in REQUIRED_FIELDS:
                        if other_field != field and other_field in normalized_content:
                            pos = normalized_content.find(other_field, field_pos)
                            if pos > field_pos and pos < next_field_pos:
                                next_field_pos = pos
                    
                    if next_field_pos == float('inf'):
                        next_field_pos = len(normalized_content)
                    
                    field_content = normalized_content[field_pos:next_field_pos].strip()
                    if not field_content:
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"EMPTY_FIELD:{field_name}")
                    
        is_valid = len(error_codes) == 0
        return is_valid, error_codes
    
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return False, [f"ERROR:{str(e)}"]

def analyze_error_patterns(file_errors):
    """
    Create a reverse mapping of which files have each error type.
    
    Args:
        file_errors: Dictionary mapping filenames to their errors
        
    Returns:
        dict: Mapping from error codes to lists of filenames
    """
    error_to_files = {}
    
    for filename, errors in file_errors.items():
        for error in errors:
            if error not in error_to_files:
                error_to_files[error] = []
            error_to_files[error].append(filename)
    
    return error_to_files

def find_markdown_files(base_dir, recursive=config.RECURSIVE_SEARCH):
    """Find all markdown files in the directory (and subdirectories if recursive)."""
    base_path = Path(base_dir).resolve()  # Convert to absolute path
    all_files = []
    
    if recursive:
        # Recursive search with directory filtering
        for file_path in base_path.glob('**/*.md'):
            # Check if any ignored directory is in the path parts
            path_parts = file_path.parts
            should_ignore = False
            
            for ignored_dir in config.IGNORED_DIRECTORIES:
                if ignored_dir in path_parts:
                    # Silent ignore - don't log each file
                    should_ignore = True
                    break
            
            if not should_ignore:
                all_files.append(file_path)
    else:
        # Just find files in the top directory (no subdirectory filtering needed)
        all_files = list(base_path.glob('*.md'))
    
    logging.info(f"Found {len(all_files)} markdown files to process")
    return all_files

def process_folder(input_folder, output_base=config.OUTPUT_DIR, move_files=False, report_only=config.DEFAULT_REPORT_ONLY):
    """
    Process markdown files and sort them into categories.
    
    Args:
        input_folder: Path to folder containing markdown files
        output_base: Base folder name for output
        move_files: Whether to move files (True) or copy them (False)
        report_only: If True, don't move/copy files, just analyze
        
    Returns:
        tuple: (valid_count, invalid_count, pm_count, error_counter, word_stats)
    """
    # Find all markdown files, potentially in subdirectories
    markdown_files = find_markdown_files(input_folder)
    
    if not markdown_files:
        print(f"No markdown files found in {input_folder}{' or its subdirectories' if config.RECURSIVE_SEARCH else ''}")
        return 0, 0, 0, {}, {}
    
    # Create output directories with validated subdirectory
    validated_dir = Path(output_base) / config.VALIDATED_DIR
    valid_dir = validated_dir / "valid"
    invalid_dir = validated_dir / "invalid"
    
    valid_dir.mkdir(exist_ok=True, parents=True)
    invalid_dir.mkdir(exist_ok=True, parents=True)
    
    # Summary logs now also go in the validated directory
    summary_log = validated_dir / "summary.txt"
    error_summary_csv = validated_dir / "error_summary.csv"
    rare_errors_log = validated_dir / "rare_errors.txt"
    word_count_csv = validated_dir / "word_counts.csv"
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    error_counter = Counter()
    file_errors = {}
    
    # New structures for tracking word counts
    word_counts = {
        "valid": [],
        "invalid": []
    }
    file_word_counts = {}
    
    with open(summary_log, 'w', encoding='utf-8') as log:
        log.write("Report Validation Summary\n")
        log.write("=======================\n\n")
        
        for file_path in markdown_files:
            total_files += 1
            
            # Count words in the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())
                file_word_counts[file_path.name] = word_count
            
            # Validate the report
            is_valid, error_codes = validate_report(file_path)
            
            # Store the file's error codes for summary
            file_errors[file_path.name] = error_codes
            
            # Update error counter for CSV summary
            for error in error_codes:
                error_counter[error] += 1
            
            if is_valid:
                valid_files += 1
                word_counts["valid"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = valid_dir / file_path.name
                    if move_files:
                        shutil.move(str(file_path), str(destination))
                    else:
                        shutil.copy2(str(file_path), str(destination))
                
                # Still write to the log file but conditionally print to console
                log.write(f"✅ VALID: {file_path.name} ({word_count} words)\n")
                if config.SHOW_VALID_REPORTS:
                    logging.info(f"Valid report: {file_path.name}")
            else:
                invalid_files += 1
                word_counts["invalid"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = invalid_dir / file_path.name
                    if move_files:
                        shutil.move(str(file_path), str(destination))
                    else:
                        shutil.copy2(str(file_path), str(destination))
                
                log.write(f"❌ INVALID: {file_path.name} ({word_count} words)\n")
                log.write(f"  Errors: {', '.join(error_codes)}\n")
                # Use ERROR level for better visibility
                logging.error(f"INVALID: {file_path.name} - Errors: {error_codes}")
        
        # Calculate word count statistics
        word_stats = {}
        for category, counts in word_counts.items():
            if counts:
                word_stats[category] = {
                    "average": sum(counts) / len(counts),
                    "median": statistics.median(counts) if counts else 0,
                    "min": min(counts) if counts else 0,
                    "max": max(counts) if counts else 0,
                    "total": sum(counts)
                }
            else:
                word_stats[category] = {"average": 0, "median": 0, "min": 0, "max": 0, "total": 0}
        
        # Write summary statistics with word counts
        log.write("\n\nSummary Statistics\n")
        log.write("==================\n")
        log.write(f"Total files processed: {total_files}\n")
        
        if total_files > 0:
            # Valid reports statistics
            log.write(f"Valid reports: {valid_files} ({valid_files/total_files*100:.1f}%)\n")
            if valid_files > 0:
                log.write(f"  Average length: {word_stats['valid']['average']:.1f} words\n")
                log.write(f"  Median length: {word_stats['valid']['median']} words\n")
                log.write(f"  Range: {word_stats['valid']['min']} to {word_stats['valid']['max']} words\n")
            
            # Invalid reports statistics
            log.write(f"Invalid reports: {invalid_files} ({invalid_files/total_files*100:.1f}%)\n")
            if invalid_files > 0:
                log.write(f"  Average length: {word_stats['invalid']['average']:.1f} words\n")
                log.write(f"  Median length: {word_stats['invalid']['median']} words\n")
                log.write(f"  Range: {word_stats['invalid']['min']} to {word_stats['invalid']['max']} words\n")
        else:
            log.write("No files processed.\n")
    
    # Write word count CSV
    with open(word_count_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["FILENAME", "WORD_COUNT", "CATEGORY"])
        
        # Add all files sorted by word count (descending)
        for filename, count in sorted(file_word_counts.items(), key=lambda x: x[1], reverse=True):
            category = "Valid" if filename not in file_errors or not file_errors[filename] else "Invalid"
            csv_writer.writerow([filename, count, category])
    
    # Rest of CSV and error reporting remains the same...

    logging.info(f"Processing complete. {valid_files} valid, {invalid_files} invalid reports identified.")
    
    if total_files == 0:
        print(f"No markdown files found in {input_folder}")
    
    # Return values with 0 for PM since we no longer detect them
    return valid_files, invalid_files, 0, error_counter, word_stats

def main():
    """Main entry point for the script."""
    # Add a blank line at the start for separation from command
    print("")
    
    parser = argparse.ArgumentParser(description='Sort markdown reports based on structure validation.')
    parser.add_argument('--input', default=config.SOURCE_DIR, 
                        help=f'Input folder containing markdown reports (default: {config.SOURCE_DIR})')
    parser.add_argument('--output', default=config.OUTPUT_DIR, 
                        help=f'Base output folder (default: {config.OUTPUT_DIR})')
    parser.add_argument('--move', action='store_true', 
                        help='Move files instead of copying them')
    parser.add_argument('--log', default=config.LOG_FILE, 
                        help=f'Log file path (default: {config.LOG_FILE})')
    parser.add_argument('--strict', action='store_true', default=config.STRICT_VALIDATION,
                        help='Use strict validation without normalization')
    parser.add_argument('--report-only', action='store_true', default=config.DEFAULT_REPORT_ONLY,
                        help='Only analyze files without moving/copying (default: %(default)s)')
    parser.add_argument('--no-recursive', action='store_true',
                        help='Do not search subdirectories for markdown files')
    parser.add_argument('--show-valid', action='store_true', 
                        help='Show valid reports in console output (default: hidden)')
                    
    args = parser.parse_args()
    
    # Override show valid setting if specified
    if hasattr(args, 'show_valid') and args.show_valid:
        config.SHOW_VALID_REPORTS = True
    
    # Setup logging
    setup_logger(args.log)
    
    # Override recursive search if specified
    recursive = not args.no_recursive if hasattr(args, 'no_recursive') else config.RECURSIVE_SEARCH
    
    # Make sure input folder exists
    if not os.path.exists(args.input):
        os.makedirs(args.input)
        print(f"Created input folder: {args.input}")
        print(f"Please place your markdown reports in this folder and run the script again.")
        return
    
    # Make sure output base folder exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Add blank line before starting message
    print("")
    print(f"Starting report validation from {args.input}" + 
          (" (including subdirectories)" if recursive else ""))
    
    # Add a blank line before configuration info
    print("")
    if args.strict:
        print("Using strict validation (no normalization)")
    else:
        print("Using normalized validation (accepting alternate field formats)")
    
    # Add a blank line before processing mode
    print("")
    if args.report_only:
        print("Report-only mode: files will be analyzed but not moved/copied")
    
    # Set config.RECURSIVE_SEARCH for this run
    config.RECURSIVE_SEARCH = recursive
    
    # Get all markdown files, filtering out ignored directories
    all_files = find_markdown_files(args.input, recursive=recursive)
    ignored_count = 0
    
    # Count total files including those in ignored directories
    if recursive:
        total_files_unfiltered = len(list(Path(args.input).glob('**/*.md')))
        ignored_count = total_files_unfiltered - len(all_files)
    
    # Run the validation
    valid, invalid, pm, error_counter, word_stats = process_folder(
        args.input, 
        args.output, 
        move_files=args.move,
        report_only=args.report_only
    )
    
    # Add double newline for better readability
    print("\n\nProcessing complete! Valid: {}, Invalid: {}".format(valid, invalid))
    
    # Add summary of ignored files
    if ignored_count > 0:
        print(f"Note: {ignored_count} files in excluded directories were not processed")
        print(f"Excluded directories: {', '.join(config.IGNORED_DIRECTORIES)}")
    
    # Add a newline before word count statistics
    print("")
    
    # Print word count statistics
    if valid > 0:
        print(f"Valid reports average length: {word_stats['valid']['average']:.1f} words (range: {word_stats['valid']['min']} to {word_stats['valid']['max']} words)")
    if invalid > 0:
        print(f"Invalid reports average length: {word_stats['invalid']['average']:.1f} words (range: {word_stats['invalid']['min']} to {word_stats['invalid']['max']} words)")
    
    # Add a newline before file references
    print("")
    
    if valid + invalid > 0:
        print(f"See {args.output}/validated/summary.txt for details")
        print(f"Word count analysis in {args.output}/validated/word_counts.csv")
        print(f"Error frequency analysis in {args.output}/validated/error_summary.csv")
        
        # Print rare errors reference with better spacing
        if error_counter:
            # Add double newline for visual separation
            print("\n\nSee {}/validated/rare_errors.txt for complete details".format(args.output))
            
            # Print top 5 most common errors
            print("\nTop issues found:")
            for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error}: {count} occurrences")
                
    # Add final newline to separate from next terminal prompt
    print("")

if __name__ == "__main__":
    main()
