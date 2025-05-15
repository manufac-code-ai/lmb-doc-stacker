#!/usr/bin/env python3
"""Stack markdown reports into consolidated files for analysis."""

import argparse
import config.config as config
from report_tools.stacking import run_stacking

def main():
    """Main entry point for the stacking script."""
    parser = argparse.ArgumentParser(description='Stack markdown reports into consolidated files.')
    parser.add_argument('--config', default='config/org_config.md',
                        help='Configuration file for report stacking')
    parser.add_argument('--input', default=config.SOURCE_DIR,
                        help='Input directory containing markdown reports')
    parser.add_argument('--output', default=f'{config.OUTPUT_DIR}/stacks',
                        help='Output directory for stacked reports')
    # Change --auto to --config-based to invert the default behavior
    parser.add_argument('--config-based', action='store_true',
                        help='Use config-based stacking instead of automatic directory-based stacking')
                      
    args = parser.parse_args()
    
    # Run the stacking with the parsed arguments
    run_stacking(args)

if __name__ == "__main__":
    main()