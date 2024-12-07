import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from utils.backup import BackupHandler

def setup_test_files(test_dir: Path) -> None:
    """Create test files for backup testing"""
    # Create PKM structure
    pkm_dir = test_dir / "PKM"
    pkm_files = {
        "atomics/2024/12/04/test-post-1.md": "Test post 1 content",
        "atomics/2024/12/04/test-post-2.md": "Test post 2 content",
        "atomics/2024/12/04/test-image.png": "Test image content"
    }
    
    # Create Jekyll structure
    jekyll_dir = test_dir / "jekyll"
    jekyll_files = {
        "_posts/2024-12-04-test-post-1.md": "Test post 1 content",
        "_posts/2024-12-04-test-post-2.md": "Test post 2 content",
        "assets/img/posts/test-image.png": "Test image content"
    }
    
    # Create PKM files
    for file_path, content in pkm_files.items():
        full_path = pkm_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    # Create Jekyll files
    for file_path, content in jekyll_files.items():
        full_path = jekyll_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

def test_backup_dry_run():
    """Test that dry run mode shows changes without making them"""
    print("\nTesting backup dry run:")
    
    # Create test directory
    test_dir = Path("test_backup")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Run backup in dry run mode
        handler = BackupHandler(
            str(test_dir / "PKM"),
            str(test_dir / "jekyll"),
            debug=True,
            dry_run=True
        )
        
        handler.backup_all()
        
        # Verify no backup directories were created
        success = True
        
        pkm_backup = test_dir / "PKM_backup"
        jekyll_backup = test_dir / "jekyll_backup"
        
        print("\nChecking backup directories:")
        for backup_dir in [pkm_backup, jekyll_backup]:
            exists = backup_dir.exists()
            success = success and not exists
            print(f"  {backup_dir.name}: {'✓' if not exists else '✗'}")
        
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_backup_execution():
    """Test that backup actually creates files in normal mode"""
    print("\nTesting backup execution:")
    
    # Create test directory
    test_dir = Path("test_backup")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Run backup
        handler = BackupHandler(
            str(test_dir / "PKM"),
            str(test_dir / "jekyll"),
            debug=True
        )
        
        handler.backup_all()
        
        # Verify backup directories were created with files
        success = True
        
        print("\nChecking PKM backup:")
        pkm_backup = test_dir / "PKM_backup"
        if pkm_backup.exists():
            # Should have one backup directory
            backup_dirs = list(pkm_backup.iterdir())
            has_one_backup = len(backup_dirs) == 1
            success = success and has_one_backup
            print(f"  Has one backup directory: {'✓' if has_one_backup else '✗'}")
            
            if has_one_backup:
                # Check files were copied
                backup_dir = backup_dirs[0]
                files = list((backup_dir / "atomics/2024/12/04").glob("*"))
                has_files = len(files) == 3  # 2 posts + 1 image
                success = success and has_files
                print(f"  Has correct files: {'✓' if has_files else '✗'}")
        else:
            success = False
            print("  ✗ PKM backup directory not created")
        
        print("\nChecking Jekyll backup:")
        jekyll_backup = test_dir / "jekyll_backup"
        if jekyll_backup.exists():
            # Should have one backup directory
            backup_dirs = list(jekyll_backup.iterdir())
            has_one_backup = len(backup_dirs) == 1
            success = success and has_one_backup
            print(f"  Has one backup directory: {'✓' if has_one_backup else '✗'}")
            
            if has_one_backup:
                # Check files were copied
                backup_dir = backup_dirs[0]
                posts = list((backup_dir / "_posts").glob("*"))
                images = list((backup_dir / "assets/img/posts").glob("*"))
                has_files = len(posts) == 2 and len(images) == 1
                success = success and has_files
                print(f"  Has correct files: {'✓' if has_files else '✗'}")
        else:
            success = False
            print("  ✗ Jekyll backup directory not created")
        
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_backup_rotation():
    """Test that backup rotation works correctly"""
    print("\nTesting backup rotation:")
    
    # Create test directory
    test_dir = Path("test_backup")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Create handler with max 3 backups
        handler = BackupHandler(
            str(test_dir / "PKM"),
            str(test_dir / "jekyll"),
            debug=True
        )
        handler.max_backups = 3
        
        # Create 5 backups
        for i in range(5):
            handler.backup_all()
        
        # Verify only 3 most recent backups exist
        success = True
        
        print("\nChecking backup rotation:")
        for backup_dir in [test_dir / "PKM_backup", test_dir / "jekyll_backup"]:
            if backup_dir.exists():
                backup_count = len(list(backup_dir.iterdir()))
                correct_count = backup_count == 3
                success = success and correct_count
                print(f"  {backup_dir.name}: {'✓' if correct_count else '✗'} ({backup_count} backups)")
            else:
                success = False
                print(f"  ✗ {backup_dir.name} not created")
        
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    # Run all tests
    test_backup_dry_run()
    test_backup_execution()
    test_backup_rotation() 