#!/usr/bin/env python3
"""
Markdown Report Stack Generator

This script creates concatenated report stacks from individual markdown files
according to a configuration file. Each stack contains multiple reports with
headers and separators.
"""

import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime
import config.config as config

def setup_logger():
    """Configure the logging system."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def parse_config(config_path, logger):
    """
    Parse the org_config.md file to extract stack definitions.
    
    Returns a dictionary mapping stack names to lists of filenames.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read config file: {e}")
        sys.exit(1)
    
    # Updated pattern to capture full heading text including spaces
    stack_pattern = r'### ([^\n]+)\s+([\s\S]+?)(?=### |\Z)'
    stack_matches = re.findall(stack_pattern, content)
    
    if not stack_matches:
        logger.error("No report stack definitions found in config file")
        sys.exit(1)
    
    stacks = {}
    for stack_name, file_list in stack_matches:
        # Extract filenames from list items, stripping the "- " prefix
        files = [line.strip()[2:] for line in file_list.strip().split('\n') if line.strip().startswith('- ')]
        stacks[stack_name] = files
        logger.info(f"Found stack '{stack_name}' with {len(files)} files")
    
    return stacks

def sanitize_filename(heading):
    """Convert a heading into a valid filename."""
    # Replace spaces with underscores and remove any invalid characters
    filename = re.sub(r'[^\w\-]', '_', heading)
    # Ensure we don't have multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def verify_all_files_exist(stacks, input_dir, logger):
    """
    Verify that all files referenced in the stacks exist in the input directory.
    Exits with error if any file is missing.
    """
    missing_files = []
    
    for stack_name, files in stacks.items():
        for filename in files:
            file_path = Path(input_dir) / filename
            if not file_path.exists():
                missing_files.append((stack_name, filename))
    
    if missing_files:
        logger.error("The following files are missing:")
        for stack_name, filename in missing_files:
            logger.error(f"  Stack '{stack_name}': {filename}")
        sys.exit(1)
    
    logger.info("All files verified - proceeding with stack generation")

def generate_report_stacks(stacks, input_dir, output_dir, logger):
    """
    Generate report stacks by concatenating files according to the stack definitions.
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Open log file
    log_path = Path(output_dir) / "concat_log.txt"
    with open(log_path, 'w', encoding='utf-8') as log_file:
        # Write log header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"Report Stack Generation Log\n")
        log_file.write(f"==========================\n")
        log_file.write(f"Generated: {timestamp}\n\n")
        
        total_files_processed = 0
        
        # Process each stack
        for stack_name, files in stacks.items():
            # Create sanitized filename from stack name
            safe_filename = sanitize_filename(stack_name)
            output_path = Path(output_dir) / f"{safe_filename}.md"
            
            log_file.write(f"Stack: {stack_name}\n")
            log_file.write(f"Files included:\n")
            
            # Create the stack file
            with open(output_path, 'w', encoding='utf-8') as stack_file:
                stack_file.write(f"# Report Stack: {stack_name}\n\n")
                stack_file.write(f"Generated: {timestamp}\n\n")
                stack_file.write(f"Contains {len(files)} reports\n\n")
                stack_file.write("------\n\n")
                
                # Add each file to the stack
                for filename in files:
                    input_path = Path(input_dir) / filename
                    
                    # Add file to the stack
                    stack_file.write(f"### Report Start: {filename}\n\n")
                    
                    with open(input_path, 'r', encoding='utf-8') as input_file:
                        stack_file.write(input_file.read())
                        stack_file.write("\n\n")
                    
                    stack_file.write("------\n\n")
                    
                    # Log the added file
                    log_file.write(f"  - {filename}\n")
                    total_files_processed += 1
            
            logger.info(f"Created stack '{stack_name}' with {len(files)} files as '{safe_filename}.md'")
            log_file.write("\n")
        
        # Write summary
        log_file.write(f"\nSummary\n")
        log_file.write(f"=======\n")
        log_file.write(f"Total stacks created: {len(stacks)}\n")
        log_file.write(f"Total files processed: {total_files_processed}\n")
    
    logger.info(f"All stacks created. See {log_path} for details.")
    return total_files_processed

def main():
    """Main entry point for the script."""
    logger = setup_logger()
    
    # Configuration (using values from config module)
    config_path = "config/org_config.md"
    input_dir = config.SOURCE_DIR
    output_dir = f"{config.OUTPUT_DIR}/stacks"
    
    # Parse config file
    logger.info(f"Reading stack configurations from {config_path}")
    stacks = parse_config(config_path, logger)
    
    # Verify all files exist
    logger.info(f"Verifying all files exist in {input_dir}")
    verify_all_files_exist(stacks, input_dir, logger)
    
    # Generate report stacks
    logger.info(f"Generating report stacks in {output_dir}")
    total_files = generate_report_stacks(stacks, input_dir, output_dir, logger)
    
    logger.info(f"Successfully created {len(stacks)} stacks containing {total_files} files")
    print(f"Report stacks created successfully in {output_dir}")

if __name__ == "__main__":
    main()