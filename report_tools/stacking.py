"""Module for stacking markdown reports into consolidated files."""

import logging
import os
import re
import csv
from datetime import datetime
from pathlib import Path
import config.config as config
from report_tools.file_utils import setup_logger, ensure_directory_exists, find_markdown_files
from report_tools.token_utils import count_tokens, format_stack_summary

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

def create_stack(stack_name, files, output_dir, title_mapping=None):
    """Create a stack from the given files."""
    if not files:
        logging.warning(f"No matching files found for stack: {stack_name}")
        return None, None
        
    # Load titles if not provided
    if title_mapping is None:
        title_mapping = load_readable_titles()
        
    # Create stack content
    content = [f"# {stack_name} Reports\n"]
    content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    content.append(f"*Contains {len(files)} reports*\n")
    
    # Add each report to the stack
    for i, file_path in enumerate(files, 1):
        try:
            # Get filename for title lookup
            filename = Path(file_path).name
            
            # Get readable title or use filename as fallback
            if filename in title_mapping:
                report_title = title_mapping[filename]
                # Include both title and filename
                content.append(f"\n## {i}. {report_title}")
                content.append(f"*File: {filename}*\n")
            else:
                # Use filename as title when no readable title exists
                content.append(f"\n## {i}. {filename}")
                logging.info(f"No readable title found for: {filename}")  # Changed to INFO level
            
            # Read report content
            with open(file_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # Add report content (skip any frontmatter if present)
            content.append(report_content)
            
            # Add separator between reports (except after the last one)
            if i < len(files):
                content.append(config.STACK_SEPARATOR)
                
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
    
    # Join the content into a single string
    complete_content = "\n".join(content)
    
    # Calculate token and word counts
    tokens, words, is_accurate = count_tokens(complete_content)
    logging.info(f"Stack {stack_name}: {len(files)} files, {words:,} words, {tokens:,} tokens")
    
    # Save the stack to a file
    safe_name = "".join(c if c.isalnum() else "_" for c in stack_name)
    output_file = os.path.join(output_dir, f"{safe_name}{config.OUTPUT_FORMAT}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(complete_content)
    
    logging.info(f"Created stack: {output_file} with {len(files)} reports")
    return output_file, complete_content

def auto_stack_by_directory(base_dir, output_dir):
    """Generate stacks automatically based on directory structure."""
    logging.info(f"Auto-stacking reports from {base_dir}")
    
    # Track stacks by name: {stack_name: [file_paths]}
    stacks = {}
    
    # Get total input reports before filtering
    total_input_reports = 0
    for root, _, files in os.walk(base_dir):
        doc_files = []
        for file in files:
            for ext, enabled in config.FILE_TYPE_SUPPORT.items():
                if enabled and file.endswith(ext):
                    doc_files.append(file)
        total_input_reports += len(doc_files)
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Skip ignored directories
        if any(ignored in root.split(os.sep) for ignored in config.STACKING_IGNORED_DIRECTORIES):
            continue
            
        # Filter for supported files
        doc_files = []
        for file in files:
            for ext, enabled in config.FILE_TYPE_SUPPORT.items():
                if enabled and file.endswith(ext):
                    doc_files.append(file)
        if not doc_files:
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
            
        stacks[stack_name].extend([os.path.join(root, f) for f in doc_files])
    
    # Create stacks for each group
    created_stacks = []
    stack_contents = {}  # Track contents for stack log
    stack_stats = {}     # Track statistics for each stack
    
    # First, sort the stack names alphabetically
    sorted_stack_names = sorted(stacks.keys())
    
    for stack_name in sorted_stack_names:
        files = stacks[stack_name]
        if files:
            # Sort files by company, room, then date
            sorted_files = sort_files_by_company_room_date(files)
            
            # Store contents for stack log
            stack_contents[stack_name] = [os.path.basename(f) for f in sorted_files]
            
            # Create the stack file and get content
            stack_file, content = create_stack(stack_name, sorted_files, output_dir)
            if stack_file:
                created_stacks.append(stack_file)
                # Get token stats for console output
                tokens, words, _ = count_tokens(content)
                stack_stats[stack_name] = (len(files), words, tokens)
    
    # Output simplified console summary - one line per stack
    print(f"\nCreated {len(created_stacks)} stacks:")
    for stack_name in sorted_stack_names:
        if stack_name in stack_stats:
            files, words, tokens = stack_stats[stack_name]
            print(f"  • {stack_name}: {files} files, {words:,} words, {tokens:,} tokens")
    
    # Create the stack log with total input count
    create_stack_log(stack_contents, output_dir, total_input_reports, stack_stats)
    
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

def create_stack_log(stack_contents, output_dir, total_input_reports, stack_stats=None):
    """Create a log file showing all stacks and their contents."""
    # Add timestamp to hierarchy filename
    timestamp = datetime.now().strftime('%y%m%d-%H%M')
    log_file = os.path.join(output_dir, f"{timestamp}_stack_hierarchy{config.OUTPUT_FORMAT}")
    
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
        
        # Add summary table with token counts if we have stats
        if stack_stats and len(stack_stats) > 0:
            f.write("## Stack Sizes\n\n")
            f.write("| Stack | Files | Words | Tokens |\n")
            f.write("|-------|-------|-------|--------|\n")
            
            for stack_name in sorted(stack_stats.keys(), key=lambda x: x.lower()):
                files, words, tokens = stack_stats[stack_name]
                f.write(f"| {stack_name} | {files} | {words:,} | {tokens:,} |\n")
            
            f.write("\n")
        
        f.write("## Stack Contents\n\n")
        for stack_name, reports in sorted(stack_contents.items(), key=mac_os_stack_sort_key):
            f.write(f"### {stack_name}\n\n")
            f.write(f"Contains {len(reports)} reports:\n\n")
            
            for i, report in enumerate(reports):
                f.write(f"* {i+1}. {report}\n")
            
            f.write("\n")
    
    logging.info(f"Created stack hierarchy log: {log_file}")
    print(f"\nCreated stack hierarchy log with {len(stack_contents)} stacks and {total_output_reports} reports")
    
    return log_file

def load_readable_titles(source_dir=None):
    """
    Load readable titles from CSV file.
    
    Args:
        source_dir: Base directory to look for titles file
        
    Returns:
        Dict mapping filenames to readable titles
    """
    import csv
    import os
    import logging
    from pathlib import Path
    import config.config as config
    
    title_mapping = {}
    
    # Determine the path to the titles file
    if source_dir is None:
        source_dir = config.SOURCE_DIR
    
    titles_path = os.path.join(source_dir, config.TITLES_FOLDER, config.TITLES_FILENAME)
    
    # Check if file exists
    if not os.path.exists(titles_path):
        logging.warning(f"Readable titles file not found at {titles_path}. Using filenames as titles.")
        return title_mapping
    
    try:
        with open(titles_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    filename = row[0].strip()
                    readable_title = row[1].strip()
                    title_mapping[filename] = readable_title
        
        logging.info(f"Loaded {len(title_mapping)} readable titles from {titles_path}")
    except Exception as e:
        logging.error(f"Error loading readable titles: {e}")
    
    return title_mapping

def run_stacking(args):
    """Run the stacking process with the given arguments."""
    # Setup logging
    setup_logger()
    print("\nStarting report stacking process...")
    
    # Load readable titles once
    title_mapping = load_readable_titles()
    print(f"Loaded {len(title_mapping)} readable titles")
    
    # Ensure output directory exists
    output_dir = ensure_directory_exists(args.output)
    
    # Process based on mode
    created_stacks = []
    stack_contents = {}
    stack_stats = {}  # Track statistics for each stack
    
    # Get total count of input reports
    total_input_reports = 0
    document_files = []
    for root, _, files in os.walk(args.input):
        root_document_files = []
        for file in files:
            for ext, enabled in config.FILE_TYPE_SUPPORT.items():
                if enabled and file.endswith(ext):
                    root_document_files.append(os.path.join(root, file))
        document_files.extend(root_document_files)
    
    total_input_reports = len(document_files)
    
    # Check if no matching files were found
    if total_input_reports == 0:
        enabled_extensions = [ext for ext, enabled in config.FILE_TYPE_SUPPORT.items() if enabled]
        logging.warning(f"No files with enabled extensions ({', '.join(enabled_extensions)}) were found in the input directory.")
        print(f"\nNo matching files found! Check that FILE_TYPE_SUPPORT in config.py matches your input files.")
        print(f"Currently enabled file types: {', '.join(enabled_extensions)}")
        print(f"\nStacking complete! Created 0 stacks in {output_dir}")
        return
    
    # Invert the logic to make auto-stacking the default
    if hasattr(args, 'config_based') and args.config_based:
        # Config-based stacking
        stacks = parse_config_file(args.config)
        
        if not stacks:
            logging.error("No stacks defined in config file")
            print(f"No stacks found in config file: {args.config}")
            return
        
        print(f"Found {len(stacks)} stacks in config file")
        
        # Find all document files in the source directory
        all_files = find_markdown_files(args.input, recursive=True, context="stacking")
        all_files_dict = {f.name: str(f) for f in all_files}
        
        # Sort stack names for consistent ordering
        sorted_stack_names = sorted(stacks.keys())
        
        # Process each stack
        for stack_name in sorted_stack_names:
            filenames = stacks[stack_name]
            
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
                
                stack_file, content = create_stack(stack_name, file_paths, output_dir, title_mapping)
                if stack_file:
                    created_stacks.append(stack_file)
                    # Get token stats for console output
                    tokens, words, _ = count_tokens(content)
                    stack_stats[stack_name] = (len(file_paths), words, tokens)
            else:
                logging.warning(f"No matching files found for stack: {stack_name}")
        
        # Output simplified console summary - one line per stack
        print(f"\nCreated {len(created_stacks)} stacks:")
        for stack_name in sorted_stack_names:
            if stack_name in stack_stats:
                files, words, tokens = stack_stats[stack_name]
                print(f"  • {stack_name}: {files} files, {words:,} words, {tokens:,} tokens")
        
        # Create the stack log for config-based stacks too
        if stack_contents:
            create_stack_log(stack_contents, output_dir, total_input_reports, stack_stats)
    else:
        # Auto-stacking (now the default)
        print(f"Using automatic directory-based stacking from {args.input}")
        created_stacks = auto_stack_by_directory(args.input, output_dir)
    
    # Print summary
    print(f"\nStacking complete! Created {len(created_stacks)} stacks in {output_dir}")
    print("")  # Final newline for clean separation from prompt