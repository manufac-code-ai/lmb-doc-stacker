# Markdown Report Tools

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A toolkit for validating and stacking Markdown service reports for optimal use with Large Language Models.

## Overview

This toolkit provides two powerful utilities for working with service report collections:

1. **Validation**: Check reports for proper structure and required fields
2. **Stacking**: Combine related reports into consolidated files organized by client/location

The stacked reports are optimized for use with LLMs like NotebookLM, Perplexity, and ChatGPT, allowing you to analyze service history across related systems.

## Quick Start

```bash
# Validate reports (identifies formatting issues)
python validate.py --input /path/to/reports

# Stack reports automatically based on directory structure
python stack.py --auto --input /path/to/reports
```

## Features

### Report Validation

- **Structure Checking**: Verifies required fields are present
- **Case-Insensitive Matching**: Handles variations in field names
- **Error Reporting**: Detailed logs of validation issues
- **Statistics**: Word counts and error frequency analysis

### Report Stacking

- **Automatic Organization**: Groups reports by directory structure
- **Smart Sorting**: Orders by company → room → date
- **Directory-Based**: Creates logical stacks based on your folder hierarchy
- **Hierarchy Logs**: Comprehensive index of all stacked reports

## Detailed Usage

### Validation

```bash
python validate.py [options]
```

Options:

- `--input PATH`: Directory containing reports (default: config.SOURCE_DIR)
- `--output PATH`: Output directory (default: config.OUTPUT_DIR)
- `--strict`: Use strict field matching without normalization
- `--report-only`: Analyze without moving files (default: True)
- `--move`: Move files instead of copying them
- `--show-valid`: Show valid reports in console output

### Stacking

```bash
python stack.py [options]
```

Options:

- `--auto`: Stack based on directory structure (recommended)
- `--input PATH`: Input directory containing reports
- `--output PATH`: Output directory for stacked reports
- `--config PATH`: Config file for manual stacking (when not using --auto)

## How Stacking Works

The automatic stacking process follows your directory structure:

1. **Top-level folders** become stack names
2. If reports are in **subfolders**, stacks are named `TopFolder SubFolder`
3. Reports are sorted by company, room, then date
4. A hierarchy log shows the exact content of each stack

## Output Files

- **Stack files**: `{StackName}.md` - The consolidated reports
- **Hierarchy log**: `{YYMMDD-HHMM}_stack_hierarchy.md` - Detailed index of all stacks
- **Validation logs**: Various files in `_logs/` directory

## Best Practices

1. **Organize reports** in folders by client/location before stacking
2. **Validate reports** to identify formatting issues before stacking
3. **Use the `--auto` flag** for intelligent directory-based stacking
4. **Review the hierarchy log** to understand your stack organization

## Configuration

Settings can be customized in `config/config.py`:

- Source/destination paths
- Validation requirements
- Stacking formatting options

## License

MIT
