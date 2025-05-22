# LMbridge Doc Stacker

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A Python tool for combining text documents (.md, .txt) into consolidated files for Large Language Model processing.

## Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Detailed Usage](#detailed-usage)
- [Stack Organization Methods](#stack-organization-methods)
- [Human-Readable Titles](#human-readable-titles)
- [Configuration](#configuration)
- [Roadmap](#roadmap)

## Overview

Doc Stacker concatenates multiple text documents into single files while preserving their organization. It uses your folder structure to determine which documents belong together, adds clear separators between them, and formats them to work well with LLMs like NotebookLM, Claude, and ChatGPT. This helps LLMs process related information as a group while staying within context limits.

## Quick Start

```
# Combine documents based on directory structure (default behavior)
python stack.py --input /path/to/text/docs

# Use a specific configuration file
python stack.py --config-based --config /path/to/config.md
```

## Features

### Document Combining

- **Folder-Based Grouping**: Creates stacks based on your existing folder organization
- **Configurable Sorting**: Orders files based on patterns in filenames (defaults to chronological when possible)
- **Title Formatting**: Can use readable names instead of filenames (via CSV mapping)
- **Document Separation**: Adds consistent separator markers between documents

## Detailed Usage

`python stack.py [options]`

Options:

- `--input PATH`: Directory containing documents to combine (default: config.SOURCE_DIR)
- `--output PATH`: Output directory for combined files (default: config.OUTPUT_DIR/stacks)
- `--config PATH`: Configuration file for manual organization (default: config/org_config.md)
- `--config-based`: Use config-based organizing instead of directory-based

---

## Stack Organization Methods

Doc Stacker offers two ways to organize your documents into stacks:

### 1. Directory-Based Organization (Default)

By default, Doc Stacker uses your folder structure to determine which files belong together:

- Each top-level folder in your input directory becomes a stack
- All files within that folder (and its subfolders) are included in the stack
- If using subfolders, stacks are named using the pattern `ParentFolder_Subfolder`

This approach is convenient when your documents are already organized in logical folders.

### 2. Config-Based Organization

For more control, you can manually specify document groupings using a configuration file:

`python stack.py --config-based --config path/to/config.md`

Example configuration file (`org_config.md`):

```
# Document Stacking Configuration

## Stack: Financial_Reports_2023
Description: Q1-Q3 financial reports and analysis
Files:
- financial/q1_2023_report.md
- financial/q2_2023_report.md
- financial/q3_2023_report.md
- analysis/financial_summary_2023.md

## Stack: Project_Alpha_Technical
Description: Technical documentation for Project Alpha
Files:
- projects/alpha/requirements.md
- projects/alpha/architecture.md
- projects/alpha/api_spec.md
- technical/database_schema.md
```

Each stack is defined with:

- A level-2 heading (`##`) with the stack name
- An optional description
- A list of files (paths relative to your input directory)

This approach is useful when you want to combine files from different folders or create custom groupings.

---

## Human-Readable Titles

Doc Stacker can use descriptive titles for your documents instead of raw filenames, making the stacked output more readable for LLMs:

### Setting Up Title Mapping

1. Create a `__config` folder inside your source directory
2. Create a file named `readable_titles.csv` inside this folder
3. Format the CSV with two columns: filename and readable title

```
filename,readable_title
q1_2023_report.md,Q1 2023 Financial Report
q2_2023_report.md,Q2 2023 Financial Report
q3_2023_report.md,Q3 2023 Financial Report
financial_summary_2023.md,2023 Financial Summary
requirements.md,Project Alpha Requirements
architecture.md,Project Alpha Architecture
api_spec.md,Project Alpha API Specification
database_schema.md,Database Schema
```

When Doc Stacker processes your files, it will:

- Look for this CSV in the `__config` folder of your source directory
- Replace filenames with readable titles in section headers
- Fall back to using filenames if the CSV is missing or a file isn't listed

This is particularly useful when your filenames are abbreviated or use naming conventions that aren't descriptive enough for an LLM to understand.

---

## Configuration

Doc Stacker can be customized through settings in config.py:

### File Handling

- `OUTPUT_FORMAT`: File extension for output files (.md or .txt)
- `FILE_TYPE_SUPPORT`: Dictionary of file types to process
- `STACK_SEPARATOR`: Marker text between documents in stacks

### File Sorting

Doc Stacker sorts files within each stack using configurable patterns:

```python
FILENAME_PATTERNS = {
    # Regex for date extraction (currently YYMMDD)
    "date_pattern": r'(\d{6})(?:-\d+)?',

    # Fields to sort by, in priority order
    "sort_fields": ["date", "company", "room"],

    # Whether to enable date-based sorting
    "use_date_sorting": True
}
```

These settings can be adjusted to match your filename conventions. By default, the system looks for dates in YYMMDD format at the beginning of filenames.

---

## Roadmap

Future planned enhancements:

- **Stack Size Statistics**

  - Token count estimation for different LLM models
  - Configurable maximum size limits with warnings
  - Size distribution analysis across stacks
  - Dashboard view of stack sizes relative to LLM context windows

- Support for additional file formats (PDF, DOCX)
- Customizable output templates
- Enhanced chronological sorting algorithms
- Simplified console logging with summary statistics only
- GUI interface for visual stack management
