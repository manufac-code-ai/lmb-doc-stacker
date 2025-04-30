# README

## Report Sorter Tool: Functional Summary

### What This Tool Does

The report_sorter.py script helps you process and organize service reports by:

1. **Validating** service reports against a standard format
2. **Categorizing** them into three groups:
   - ✅ **Valid Reports**: Properly formatted with all required fields
   - ❌ **Invalid Reports**: Missing fields or formatting issues
   - 🔧 **PM Reports**: Preventative maintenance reports (detected by "PM" in filename)
3. **Analyzing** word counts and providing statistics
4. **Generating** detailed reports on any problems found

### How to Use It

1. **Put your reports in the input folder**:
   - Place all `.md` files in the _md_input folder

2. **Run the script**:
   ```bash
   python report_sorter.py
   ```

3. **Review the results**:
   - Files are sorted into folders: valid, invalid, and PM
   - Summary reports are created in _md_output

### Common Options

- **Report-only mode** (don't move files):
  ```bash
  python report_sorter.py --report-only
  ```

- **Move files** instead of copying:
  ```bash
  python report_sorter.py --move
  ```

- **Custom input/output folders**:
  ```bash
  python report_sorter.py --input my_reports --output sorted_reports
  ```

### Output Reports

After running, you'll get:
- `summary.txt`: Overview of all processed files
- `word_counts.csv`: Detailed word count data for each file
- `error_summary.csv`: Analysis of common errors
- `rare_errors.txt`: Details on uncommon issues

This tool is perfect for checking if your newly found reports meet your formatting standards before processing them further.