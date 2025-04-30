"""Module for stacking markdown reports into consolidated files."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
import config.config as config
from report_tools.file_utils import setup_logger, ensure_directory_exists, find_markdown_files

def parse_config_file(config_file):
    """Parse the configuration file for report stacks."""
    stacks = {}
    current_stack = None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('<!--'):
                    continue
                
                # New stack header
                if line.startswith('###'):
                    current_stack = line.lstrip('# ').strip()
                    stacks[current_stack] = []
                # File entry for current stack
                elif current_stack and line.startswith('-'):
                    filename = line.lstrip('- ').strip()
                    if filename:
                        stacks[current_stack].append(filename)
    except Exception as e:
        logging.error(f"Error parsing config file: {str(e)}")
        return {}
    
    return stacks

def find_files_by_name(directory, filenames):
    """Find file paths by their names."""
    directory_path = Path(directory)
    found_files = []
    
    for root, _, files in os.walk(directory_path):
        for filename in files:
            if filename in filenames:
                found_files.append(os.path.join(root, filename))
                
    return found_files

def create_stack(stack_name, files, output_dir):
    """Create a stacked report file from the provided files."""
    if not files:
        logging.warning(f"No files found for stack: {stack_name}")
        return
    
    # Create normalized stack name for the filename
    safe_name = re.sub(r'[^\w\s-]', '', stack_name).strip().replace(' ', '_')
    current_date = datetime.now().strftime('%y%m%d')
    output_file = os.path.join(output_dir, f"{current_date}_{safe_name}.md")
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(f"# {stack_name} Reports\n\n")
        out_file.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        
        for i, file_path in enumerate(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as in_file:
                    content = in_file.read()
                    
                filename = os.path.basename(file_path)
                out_file.write(f"## {i+1}. {filename}\n\n")
                out_file.write(content)
                
                # Add separator between reports unless it's the last one
                if i < len(files) - 1:
                    out_file.write("\n\n---\n\n")
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {str(e)}")
    
    logging.info(f"Created stack: {output_file} with {len(files)} reports")
    return output_file

def run_stacking(args):
    """Run the report stacking process."""
    logger = setup_logger()
    
    print("\nStarting report stacking process...")
    
    # Ensure output directory exists
    output_dir = ensure_directory_exists(args.output)
    
    # Parse config file
    stacks = parse_config_file(args.config)
    
    if not stacks:
        logging.error("No stacks defined in config file")
        print(f"No stacks found in config file: {args.config}")
        return
    
    print(f"Found {len(stacks)} stacks in config file")
    
    # Find all markdown files in the source directory
    all_files = find_markdown_files(args.input, recursive=True)
    all_files_dict = {f.name: str(f) for f in all_files}
    
    # Process each stack
    created_stacks = []
    
    for stack_name, filenames in stacks.items():
        print(f"\nProcessing stack: {stack_name}")
        
        # Find the files in the directory
        file_paths = []
        for filename in filenames:
            if filename in all_files_dict:
                file_paths.append(all_files_dict[filename])
            else:
                logging.warning(f"File not found: {filename}")
        
        # Create the stack file
        if file_paths:
            stack_file = create_stack(stack_name, file_paths, output_dir)
            if stack_file:
                created_stacks.append(stack_file)
                print(f"  Created stack with {len(file_paths)} reports")
        else:
            print(f"  No matching files found for stack: {stack_name}")
    
    # Print summary
    print(f"\nStacking complete! Created {len(created_stacks)} stacks in {output_dir}")
    print("")  # Final newline for clean separation from prompt