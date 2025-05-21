# LMbridge Doc Stacker

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A specialized tool for stacking Markdown documents into optimized files for Large Language Model processing.

## Overview

Doc Stacker intelligently combines related markdown documents into consolidated files optimized for LLMs like NotebookLM, Claude, and ChatGPT. By grouping related documents, it enables more comprehensive context for AI analysis while respecting context window limitations.

## Quick Start

```bash
# Stack reports based on directory structure (default behavior)
python stack.py --input /path/to/markdown/docs

# Use a specific configuration file
python stack.py --config-based --config /path/to/config.md
```

## Features

### Document Stacking

- **Automatic Organization**: Groups documents by directory structure
- **Smart Sorting**: Orders chronologically based on document naming patterns
- **Human-Readable Titles**: Converts filenames to descriptive titles (optional)
- **Context Optimization**: Creates section breaks for better LLM parsing

## Detailed Usage

```bash
python stack.py [options]
```

Options:

- `--input PATH`: Input directory containing markdown documents (default: config.SOURCE_DIR)
- `--output PATH`: Output directory for stacked documents (default: config.OUTPUT_DIR/stacks)
- `--config PATH`: Configuration file for manual stacking (default: config/org_config.md)
- `--config-based`: Use config-based stacking instead of automatic directory-based stacking

## How Stacking Works

The stacking process follows your directory structure:

1. **Top-level folders** become stack names
2. If documents are in **subfolders**, stacks are named `TopFolder_SubFolder`
3. Documents are sorted chronologically when possible
4. A hierarchy log shows the exact content of each stack

### Human-Readable Titles

For improved LLM processing, Doc Stacker can use human-readable titles instead of raw filenames:

1. Create a `__config` folder in your source directory
2. Add a `readable_titles.csv` file with the format:
   ```
   filename,readable_title
   220714-server-restart.md,Data Center Primary Server Restart (July 2022)
   ```
3. The stacker will automatically use these titles when creating section headers

If the CSV file isn't found, filenames will be used as titles.

## Output Files

- **Stack files**: `{StackName}.md` - The consolidated documents
- **Hierarchy log**: `{YYMMDD-HHMM}_stack_hierarchy.md` - Detailed index of all stacks

## Best Practices

1. **Organize documents** in folders by topic/client/project before stacking
2. **Use descriptive filenames** that follow a consistent pattern
3. **Create a readable_titles.csv** for optimal LLM understanding
4. **Review the hierarchy log** to understand your stack organization

## Configuration

Settings can be customized in config.py:

- Source/destination paths
- Recursion settings
- Stacking format options

## License

MIT
