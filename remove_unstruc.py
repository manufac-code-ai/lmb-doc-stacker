import os
import shutil
from pathlib import Path
import sys

# Configuration - use absolute paths
input_folder = Path(os.path.abspath("_md_input"))
offload_folder = Path(os.path.abspath("_offload/unstructured"))
unstructured_folder = Path(os.path.abspath("_md_output/unstructured"))

print(f"Input folder: {input_folder}")
print(f"Offload folder: {offload_folder}")
print(f"Unstructured folder: {unstructured_folder}")

# Check if source directory exists
if not os.path.exists(unstructured_folder):
    print(f"ERROR: Unstructured directory doesn't exist: {unstructured_folder}")
    sys.exit(1)

# Check if input directory exists
if not os.path.exists(input_folder):
    print(f"ERROR: Input directory doesn't exist: {input_folder}")
    sys.exit(1)

# Create offload directory if it doesn't exist
offload_folder.mkdir(parents=True, exist_ok=True)

files_moved = 0
failed_moves = 0

for file_path in Path(unstructured_folder).glob("*.md"):
    source_file = input_folder / file_path.name
    dest_file = offload_folder / file_path.name
    
    if source_file.exists():
        try:
            print(f"Moving: {source_file}")
            print(f"To: {dest_file}")
            
            # Handle case where destination already exists
            if dest_file.exists():
                print(f"  Warning: Destination already exists, adding suffix")
                base, ext = os.path.splitext(dest_file)
                dest_file = Path(f"{base}_duplicate{ext}")
            
            # Perform the actual move with verbose error handling
            shutil.move(str(source_file), str(dest_file))
            
            # Verify the move worked
            if not source_file.exists() and dest_file.exists():
                print(f"  SUCCESS: File moved successfully")
                files_moved += 1
            else:
                print(f"  ERROR: Move operation didn't work as expected")
                failed_moves += 1
                
        except Exception as e:
            print(f"  ERROR moving {source_file.name}: {str(e)}")
            failed_moves += 1
    else:
        print(f"Source file not found: {source_file}")

print(f"\nSummary: Moved {files_moved} files, {failed_moves} failures")
print(f"Input files remaining: {len(list(input_folder.glob('*.md')))}")

# Verify the results
if failed_moves > 0:
    print("\nWARNING: Some files could not be moved. See errors above.")
    print("You may need to move them manually.")
else:
    print("\nAll files processed successfully.")