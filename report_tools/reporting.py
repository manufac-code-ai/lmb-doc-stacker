"""Report generation and statistics for validation results."""

import csv
import statistics
from collections import Counter
from pathlib import Path
import config.config as config

def calculate_word_statistics(word_counts):
    """
    Calculate statistics for word counts.
    
    Args:
        word_counts: Dictionary with 'valid' and 'invalid' lists of word counts
        
    Returns:
        Dictionary with statistics for each category
    """
    word_stats = {}
    for category, counts in word_counts.items():
        if counts:
            word_stats[category] = {
                "average": sum(counts) / len(counts),
                "median": statistics.median(counts) if counts else 0,
                "min": min(counts) if counts else 0,
                "max": max(counts) if counts else 0,
                "total": sum(counts),
                "count": len(counts)
            }
        else:
            word_stats[category] = {
                "average": 0, 
                "median": 0, 
                "min": 0, 
                "max": 0, 
                "total": 0,
                "count": 0
            }
    
    return word_stats

def write_summary_files(file_errors, file_word_counts, word_stats, error_counter):
    """
    Write all summary and analysis files.
    
    Args:
        file_errors: Dictionary mapping filenames to their error codes
        file_word_counts: Dictionary mapping filenames to word counts
        word_stats: Dictionary with word count statistics
        error_counter: Counter with error frequencies
    """
    write_word_count_csv(file_word_counts, file_errors)
    write_error_summary(error_counter)
    write_rare_errors(file_errors, error_counter)
    append_stats_to_summary(word_stats)

def write_word_count_csv(file_word_counts, file_errors):
    """Write CSV with word counts for all files."""
    with open(config.WORD_COUNT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["FILENAME", "WORD_COUNT", "CATEGORY"])
        
        # Add all files sorted by word count (descending)
        for filename, count in sorted(file_word_counts.items(), key=lambda x: x[1], reverse=True):
            category = "Valid" if filename not in file_errors or not file_errors[filename] else "Invalid"
            csv_writer.writerow([filename, count, category])

def write_error_summary(error_counter):
    """Write CSV summarizing error frequencies."""
    with open(config.ERROR_SUMMARY, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["ERROR_CODE", "COUNT"])
        
        # Add all errors sorted by frequency
        for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True):
            csv_writer.writerow([error, count])

def write_rare_errors(file_errors, error_counter):
    """Write a report of rare errors (occurring in 2 or fewer files)."""
    # Find infrequent errors (≤ 2 occurrences)
    rare_errors = {error: count for error, count in error_counter.items() if count <= 2}
    
    # If there are rare errors, create a more detailed report
    if rare_errors:
        with open(config.RARE_ERRORS, 'w', encoding='utf-8') as rare_file:
            rare_file.write("Rare Errors (occurring in 2 or fewer files)\n")
            rare_file.write("=========================================\n\n")
            
            # Group files by the rare errors they contain
            error_files = {}
            for error in rare_errors:
                error_files[error] = []
                
            for filename, errors in file_errors.items():
                for error in errors:
                    if error in rare_errors:
                        error_files[error].append(filename)
            
            # Write out each rare error and the files it appears in
            for error, filenames in error_files.items():
                if filenames:  # Only write errors that have associated files
                    rare_file.write(f"{error}: {len(filenames)} occurrences\n")
                    for filename in filenames:
                        rare_file.write(f"  - {filename}\n")
                    rare_file.write("\n")

def append_stats_to_summary(word_stats):
    """Append statistical information to the summary log."""
    with open(config.SUMMARY_LOG, 'a', encoding='utf-8') as log:
        log.write("\n\nWord Count Statistics\n")
        log.write("===================\n")
        
        # Valid report statistics
        if word_stats.get('valid', {}).get('count', 0) > 0:
            log.write(f"Valid Reports ({word_stats['valid']['count']} files):\n")
            log.write(f"  Average: {word_stats['valid']['average']:.1f} words\n")
            log.write(f"  Median: {word_stats['valid']['median']} words\n")
            log.write(f"  Range: {word_stats['valid']['min']} to {word_stats['valid']['max']} words\n")
            log.write(f"  Total: {word_stats['valid']['total']} words\n\n")
        
        # Invalid report statistics
        if word_stats.get('invalid', {}).get('count', 0) > 0:
            log.write(f"Invalid Reports ({word_stats['invalid']['count']} files):\n")
            log.write(f"  Average: {word_stats['invalid']['average']:.1f} words\n")
            log.write(f"  Median: {word_stats['invalid']['median']} words\n")
            log.write(f"  Range: {word_stats['invalid']['min']} to {word_stats['invalid']['max']} words\n")
            log.write(f"  Total: {word_stats['invalid']['total']} words\n")