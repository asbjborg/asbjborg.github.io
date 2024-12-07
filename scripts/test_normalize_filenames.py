import os
import shutil
from pathlib import Path
from normalize_filenames import (
    is_jekyll_friendly,
    make_jekyll_friendly,
    extract_date_from_path,
    normalize_filenames
)
from dotenv import load_dotenv

def test_is_jekyll_friendly():
    """Test the is_jekyll_friendly function with standard test cases"""
    print("\nTesting is_jekyll_friendly:")
    test_cases = {
        "good-file-name.md": True,
        "Bad File Name.md": False,
        "file_with_underscore.md": True,
        "file-with-UPPERCASE.md": False,
        "file.with.dots.md": False,
        "file@with#special$chars.md": False,
        "2024-12-04-jekyll-post.md": True,
        "test_file_underscores.md": True,
        "Test File Spaces.md": False
    }
    
    for filename, expected in test_cases.items():
        result = is_jekyll_friendly(filename)
        print(f"  {filename}: {'✓' if result == expected else '✗'} (got {result}, expected {expected})")

def test_make_jekyll_friendly():
    """Test the make_jekyll_friendly function with standard test cases"""
    print("\nTesting make_jekyll_friendly:")
    test_cases = {
        "Bad File Name.md": "bad-file-name.md",
        "file_with_underscore.md": "file_with_underscore.md",
        "file-with-UPPERCASE.md": "file-with-uppercase.md",
        "file.with.dots.md": "file-with-dots.md",
        "file@with#special$chars.md": "file-with-special-chars.md",
        "Test File Spaces.md": "test-file-spaces.md",
        "Already-good-name.md": "already-good-name.md",
        "Mixed.File-Name_Style.md": "mixed-file-name-style.md"
    }
    
    for input_name, expected in test_cases.items():
        result = make_jekyll_friendly(input_name)
        print(f"  {input_name} -> {result}: {'✓' if result == expected else '✗'}")

def test_extract_date():
    """Test the extract_date_from_path function with standard test cases"""
    print("\nTesting extract_date_from_path:")
    test_cases = [
        ("PKM/atomics/2024/12/04/test.md", "2024-12-04"),
        ("PKM/atomics/2024/1/4/test.md", "2024-01-04"),  # Should pad with zeros
        ("PKM/atomics/2024/12/31/test.md", "2024-12-31"),  # End of month
        ("PKM/atomics/2024/02/29/test.md", "2024-02-29"),  # Leap year
        ("PKM/atomics/2023/02/28/test.md", "2023-02-28")   # Non-leap year
    ]
    
    for input_path, expected in test_cases:
        try:
            result = extract_date_from_path(Path(input_path))
            print(f"  {input_path} -> {result}: {'✓' if result == expected else '✗'}")
        except ValueError as e:
            print(f"  {input_path} -> Error: {str(e)}")

def test_normalize_filenames():
    """Test the full normalization process with standard test files"""
    print("\nTesting normalize_filenames:")
    
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    
    # Create test directory
    test_dir = Path("test_vault")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Create test structure
    files = [
        "atomics/2024/12/04/Test File With Spaces.md",
        "atomics/2024/12/04/Test-File-Already-Good.md",
        "atomics/2024/12/04/Test_File_With_Underscores.md",
        "atomics/2024/12/04/Test File with UPPERCASE.md",
        "atomics/2024/12/04/Test.File.With.Dots.md",
        "atomics/2024/12/04/Test@File#With$Special&Chars.md"
    ]
    
    # Create the files with some content
    for file_path in files:
        full_path = test_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write("""---
title: Test Post
status: published
---

Test content
""")
    
    try:
        # Run normalization in dry-run mode first
        print("\n  Running in dry-run mode:")
        normalize_filenames(str(test_dir), debug=True, dry_run=True)
        
        # Run actual normalization
        print("\n  Running actual normalization:")
        normalize_filenames(str(test_dir), debug=True)
        
        # Check results
        print("\n  Final files:")
        for f in (test_dir / "atomics").rglob("*.md"):
            print(f"    {f.relative_to(test_dir)}")
    
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    # Run all tests
    test_is_jekyll_friendly()
    test_make_jekyll_friendly()
    test_extract_date()
    test_normalize_filenames() 