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
    
    # Create normalized stack name for the filename - NO date prefix
    safe_name = re.sub(r'[^\w\s-]', '', stack_name).strip().replace(' ', '_')
    output_file = os.path.join(output_dir, f"{safe_name}.md")
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(f"# {stack_name} Reports\n\n")
        out_file.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        out_file.write(f"*Contains {len(files)} reports*\n\n")
        
        for i, file_path in enumerate(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as in_file:
                    content = in_file.read()
                    
                filename = os.path.basename(file_path)
                out_file.write(f"## {i+1}. {filename}\n\n")
                out_file.write(content)
                
                # Add enhanced separator between reports unless it's the last one
                if i < len(files) - 1:
                    out_file.write(config.STACK_SEPARATOR)
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {str(e)}")
    
    logging.info(f"Created stack: {output_file} with {len(files)} reports")
    return output_file

def auto_stack_by_directory(base_dir, output_dir):
    """Generate stacks automatically based on directory structure."""
    logging.info(f"Auto-stacking reports from {base_dir}")
    
    # Track stacks by name: {stack_name: [file_paths]}
    stacks = {}
    
    # Get total input reports before filtering
    total_input_reports = 0
    for root, _, files in os.walk(base_dir):
        md_files = [f for f in files if f.endswith('.md')]
        total_input_reports += len(md_files)
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Skip ignored directories
        if any(ignored in root.split(os.sep) for ignored in config.STACKING_IGNORED_DIRECTORIES):
            continue
            
        # Filter for markdown files
        md_files = [f for f in files if f.endswith('.md')]
        if not md_files:
            continue
            
        # Determine stack name based on directory structure
        rel_path = os.path.relpath(root, base_dir)
        if rel_path == '.':
            # Files in the base directory - skip
            continue
            
        parts = rel_path.split(os.sep)
        
        if len(parts) == 1:
            # Top-level folder with reports
            stack_name = parts[0]
        else:
            # Subfolder with reports (use only top and second level)
            stack_name = f"{parts[0]} {parts[1]}"
        
        # Add files to stack
        if stack_name not in stacks:
            stacks[stack_name] = []
            
        stacks[stack_name].extend([os.path.join(root, f) for f in md_files])
    
    # Create stacks for each group
    created_stacks = []
    stack_contents = {}  # Track contents for stack log
    
    for stack_name, files in stacks.items():
        if files:
            # Sort files by company, room, then date
            sorted_files = sort_files_by_company_room_date(files)
            
            # Store contents for stack log
            stack_contents[stack_name] = [os.path.basename(f) for f in sorted_files]
            
            # Create the stack file
            stack_file = create_stack(stack_name, sorted_files, output_dir)
            if stack_file:
                created_stacks.append(stack_file)
                print(f"  Created stack '{stack_name}' with {len(files)} reports")
    
    # Create the stack log with total input count
    create_stack_log(stack_contents, output_dir, total_input_reports)
    
    return created_stacks

def sort_files_by_company_room_date(files):
    """Sort files by company, room, then date using Mac OS natural sort order."""
    def mac_os_sort_key(s):
        """Simulate Mac OS natural sort order where special chars sort first."""
        # Convert to lowercase for case-insensitive sorting
        s = s.lower()
        # Make symbols sort before alphanumeric by adding a prefix
        if s and not s[0].isalnum():
            return "0" + s
        return "1" + s
    
    def sort_key(filepath):
        filename = os.path.basename(filepath)
        
        # Extract date - handle date ranges like "250316-8"
        date_match = re.match(r'(\d{6})(?:-\d+)?', filename)
        date = date_match.group(1) if date_match else "000000"
        
        # Extract company and room
        parts = filename[7:].split(' - ', 1)  # Skip date prefix + space
        
        if len(parts) < 2:
            company = parts[0] if parts else ""
            room = ""
        else:
            company = parts[0]
            room = parts[1].replace('.md', '')
            
        # Return sort key tuple - using Mac OS natural sort order
        return (mac_os_sort_key(company), mac_os_sort_key(room), date)
    
    return sorted(files, key=sort_key)

def create_stack_log(stack_contents, output_dir, total_input_reports):
    """Create a log file showing all stacks and their contents."""
    # Add timestamp to hierarchy filename
    timestamp = datetime.now().strftime('%y%m%d-%H%M')
    log_file = os.path.join(output_dir, f"{timestamp}_stack_hierarchy.md")
    
    # Count total reports across all stacks
    total_output_reports = sum(len(reports) for reports in stack_contents.values())
    
    def mac_os_stack_sort_key(item):
        stack_name = item[0].lower()
        if stack_name and not stack_name[0].isalnum():
            return "0" + stack_name
        return "1" + stack_name
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# Report Stack Hierarchy\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        
        # Enhanced intro line with input/output report counts
        f.write(f"This document lists all {len(stack_contents)} stacks containing a total " +
                f"of {total_output_reports} reports. Started with {total_input_reports} " +
                f"input reports ({total_input_reports - total_output_reports} excluded).\n\n")
        
        for stack_name, reports in sorted(stack_contents.items(), key=mac_os_stack_sort_key):
            f.write(f"## {stack_name}\n\n")
            f.write(f"Contains {len(reports)} reports:\n\n")
            
            for i, report in enumerate(reports):
                f.write(f"* {i+1}. {report}\n")
            
            f.write("\n")
    
    logging.info(f"Created stack hierarchy log: {log_file}")
    print(f"  Created stack hierarchy log with {len(stack_contents)} stacks and {total_output_reports} reports")
    
    return log_file

def run_stacking(args):
    """Run the report stacking process."""
    logger = setup_logger()
    
    print("\nStarting report stacking process...")
    
    # Ensure output directory exists
    output_dir = ensure_directory_exists(args.output)
    
    # Process based on mode
    created_stacks = []
    stack_contents = {}
    
    # Get total count of input reports
    total_input_reports = 0
    for root, _, files in os.walk(args.input):
        md_files = [f for f in files if f.endswith('.md')]
        total_input_reports += len(md_files)
    
    if hasattr(args, 'auto') and args.auto:
        print(f"Using automatic directory-based stacking from {args.input}")
        created_stacks = auto_stack_by_directory(args.input, output_dir)
    else:
        # Traditional config-based stacking (existing functionality)
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
                # Store contents for stack log
                stack_contents[stack_name] = [os.path.basename(f) for f in file_paths]
                
                stack_file = create_stack(stack_name, file_paths, output_dir)
                if stack_file:
                    created_stacks.append(stack_file)
                    print(f"  Created stack with {len(file_paths)} reports")
            else:
                print(f"  No matching files found for stack: {stack_name}")
        
        # Create the stack log for config-based stacks too
        if stack_contents:
            create_stack_log(stack_contents, output_dir, total_input_reports)
    
    # Print summary
    print(f"\nStacking complete! Created {len(created_stacks)} stacks in {output_dir}")
    print("")  # Final newline for clean separation from prompt