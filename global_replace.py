#!/usr/bin/env python3
"""
Global Text Replacement Script
Replace all instances of BRICKIT with BRICKIT across the project
"""

import os
import re
from pathlib import Path

def replace_in_file(file_path: Path, old_text: str, new_text: str):
    """Replace text in a single file"""
    try:
        # Skip binary files and certain directories
        if file_path.suffix in ['.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.ico']:
            return False
            
        # Skip directories we don't want to modify
        skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            return False
            
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Check if file contains the old text
        if old_text not in content:
            return False
            
        # Replace all occurrences (case-insensitive)
        new_content = re.sub(re.escape(old_text), new_text, content, flags=re.IGNORECASE)
        
        # Write back
        file_path.write_text(new_content, encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main replacement function"""
    project_root = Path(".")
    old_text = "BRICKIT"
    new_text = "BRICKIT"
    
    print(f"🔄 Starting global replacement: {old_text} → {new_text}")
    print("=" * 60)
    
    files_modified = 0
    total_replacements = 0
    
    # Walk through all files
    for file_path in project_root.rglob("*"):
        if file_path.is_file():
            if replace_in_file(file_path, old_text, new_text):
                files_modified += 1
                # Count replacements
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    replacements = content.count(old_text)
                    total_replacements += replacements
                    print(f"✅ {file_path} ({replacements} replacements)")
                except:
                    print(f"✅ {file_path}")
    
    print("=" * 60)
    print(f"🎉 Replacement complete!")
    print(f"📁 Files modified: {files_modified}")
    print(f"🔄 Total replacements: {total_replacements}")
    
    # Summary of files that might need manual review
    print("\n📋 Files that may need manual review:")
    manual_review_files = [
        ".env",
        "README.md", 
        "package.json",
        "requirements.txt"
    ]
    
    for file_name in manual_review_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"   🔍 {file_name}")

if __name__ == "__main__":
    main()
