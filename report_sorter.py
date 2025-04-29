import os
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Required fields that must be present in markdown files
REQUIRED_FIELDS = [
    "**Date of service:**",
    "**Technician name:**",
    "**Customer point of contact:**",
    "**Description of problem:**",
    "**Description of work performed:**",
    "**Issue resolved?**",
    "**Next steps?**"
]

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
        tuple: (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Check for presence of each required field
            for field in REQUIRED_FIELDS:
                if field not in content:
                    # Field is missing or not formatted correctly
                    plain_field = field.replace('**', '')
                    if plain_field in content:
                        issues.append(f"Field not properly bolded: {plain_field}")
                    else:
                        issues.append(f"Missing field: {field}")
            
            # Check for duplicated fields
            for field in REQUIRED_FIELDS:
                occurrences = content.count(field)
                if occurrences > 1:
                    issues.append(f"Duplicated field: {field} (appears {occurrences} times)")
                    
        is_valid = len(issues) == 0
        return is_valid, issues
    
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]

def process_folder(input_folder, output_base="_md_output", move_files=False):
    """
    Process markdown files and sort them into valid/invalid categories.
    
    Args:
        input_folder: Path to folder containing markdown files
        output_base: Base folder name for output
        move_files: Whether to move files (True) or copy them (False)
    
    Returns:
        tuple: (valid_count, invalid_count)
    """
    input_path = Path(input_folder)
    
    # Create output directories
    valid_dir = Path(output_base) / "valid"
    invalid_dir = Path(output_base) / "invalid"
    
    valid_dir.mkdir(exist_ok=True, parents=True)
    invalid_dir.mkdir(exist_ok=True, parents=True)
    
    # Summary log
    summary_log = Path(output_base) / "summary.txt"
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    
    with open(summary_log, 'w', encoding='utf-8') as log:
        log.write("Report Validation Summary\n")
        log.write("=======================\n\n")
        
        for file_path in input_path.glob('*.md'):
            total_files += 1
            is_valid, issues = validate_report(file_path)
            
            if is_valid:
                valid_files += 1
                destination = valid_dir / file_path.name
                if move_files:
                    shutil.move(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                log.write(f"✓ VALID: {file_path.name}\n")
                logging.info(f"Valid report: {file_path.name}")
            else:
                invalid_files += 1
                destination = invalid_dir / file_path.name
                if move_files:
                    shutil.move(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                log.write(f"✗ INVALID: {file_path.name}\n")
                log.write(f"  Problems: {', '.join(issues)}\n")
                logging.warning(f"Invalid report: {file_path.name} - Issues: {issues}")
        
        # Write summary statistics
        log.write("\n\nSummary Statistics\n")
        log.write("==================\n")
        log.write(f"Total files processed: {total_files}\n")
        if total_files > 0:
            log.write(f"Valid reports: {valid_files} ({valid_files/total_files*100:.1f}%)\n")
            log.write(f"Invalid reports: {invalid_files} ({invalid_files/total_files*100:.1f}%)\n")
        else:
            log.write("No files processed.\n")
    
    logging.info(f"Processing complete. {valid_files} valid and {invalid_files} invalid reports identified.")
    
    if total_files == 0:
        print(f"No markdown files found in {input_folder}")
    
    return valid_files, invalid_files

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Sort markdown reports based on structure validation.')
    parser.add_argument('--input', default='_md_input', help='Input folder containing markdown reports')
    parser.add_argument('--output', default='_md_output', help='Base output folder')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying them')
    parser.add_argument('--log', default='report_validation.log', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(args.log)
    
    # Make sure input folder exists
    if not os.path.exists(args.input):
        os.makedirs(args.input)
        print(f"Created input folder: {args.input}")
        print(f"Please place your markdown reports in this folder and run the script again.")
        return
    
    # Make sure output base folder exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    print(f"Starting report validation from {args.input}...")
    valid, invalid = process_folder(
        args.input, 
        args.output, 
        move_files=args.move
    )
    
    print(f"Processing complete! Valid: {valid}, Invalid: {invalid}")
    if valid + invalid > 0:
        print(f"See {args.output}/summary.txt for details")

if __name__ == "__main__":
    main()
    