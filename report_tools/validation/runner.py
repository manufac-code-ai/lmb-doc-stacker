"""High-level validation runner handling CLI and orchestration."""

import os
import logging
import config.config as config
from report_tools.file_utils import setup_logger, find_markdown_files
from report_tools.validation.processor import process_folder

def run_validation(args):
    """Run the validation process with the provided arguments."""
    # Print a blank line at the start for separation from command
    print("")
    
    # Setup logger
    setup_logger()
    
    # Override recursive search if specified
    recursive = not args.no_recursive if hasattr(args, 'no_recursive') else config.RECURSIVE_SEARCH
    
    # Override show valid setting if specified
    show_valid = args.show_valid if hasattr(args, 'show_valid') else config.SHOW_VALID_REPORTS
    
    # Set config.RECURSIVE_SEARCH for this run
    config.RECURSIVE_SEARCH = recursive
    
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
    
    # Get total files including ignored directories
    ignored_count = 0
    if recursive:
        # This is already filtering ignored directories in find_markdown_files
        pass
        
    # Run the validation
    valid, invalid, ignored_files, error_counter, word_stats = process_folder(
        args.input, 
        args.output, 
        move_files=args.move,
        report_only=args.report_only,
        strict=args.strict,
        show_valid=show_valid
    )
    
    # Add double newline for better readability
    print("\n\nProcessing complete! Valid: {}, Invalid: {}".format(valid, invalid))
    
    # Add summary of ignored files
    if ignored_files > 0:
        print(f"Note: {ignored_files} reports were explicitly excluded from validation")
    
    # Add summary of ignored directories
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
        print(f"See {config.SUMMARY_LOG} for details")
        print(f"Word count analysis in {config.WORD_COUNT_CSV}")
        print(f"Error frequency analysis in {config.ERROR_SUMMARY}")
        
        # Print rare errors reference with better spacing
        if error_counter:
            # Add double newline for visual separation
            print(f"\n\nSee {config.RARE_ERRORS} for complete details")
            
            # Print top 5 most common errors
            print("\nTop issues found:")
            for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error}: {count} occurrences")
    
    # Add final newline to separate from next terminal prompt
    print("")