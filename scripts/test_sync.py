import os
import shutil
from pathlib import Path
import frontmatter
from datetime import datetime, timedelta
from sync.sync import SyncEngine, SyncAction
from dotenv import load_dotenv

def setup_test_files(test_dir: Path) -> None:
    """Create test files with various sync scenarios"""
    # Create Obsidian structure
    obsidian_dir = test_dir / "PKM"
    obsidian_files = {
        # Published post that's newer in Obsidian
        "atomics/2024/12/04/newer-in-obsidian.md": {
            "title": "Newer in Obsidian",
            "status": "published",
            "content": "Updated in Obsidian\n![[atomics/2024/12/04/test-image.png]]",
            "mtime": datetime.now()
        },
        # Published post that's older in Obsidian
        "atomics/2024/12/04/newer-in-jekyll.md": {
            "title": "Newer in Jekyll",
            "status": "published",
            "content": "Original in Obsidian\n![[atomics/2024/12/04/test-image.png]]",
            "mtime": datetime.now() - timedelta(hours=1)
        }
    }
    
    # Create Jekyll structure
    jekyll_dir = test_dir / "jekyll"
    jekyll_files = {
        # Post that's older in Jekyll
        "_posts/2024-12-04-newer-in-obsidian.md": {
            "title": "Newer in Obsidian",
            "content": "Original in Jekyll\n![test-image](/assets/img/posts/test-image.png)",
            "mtime": datetime.now() - timedelta(hours=1)
        },
        # Post that's newer in Jekyll
        "_posts/2024-12-04-newer-in-jekyll.md": {
            "title": "Newer in Jekyll",
            "content": "Updated in Jekyll\n![test-image](/assets/img/posts/test-image.png)",
            "mtime": datetime.now()
        }
    }
    
    # Create files in Obsidian
    for file_path, info in obsidian_files.items():
        full_path = obsidian_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = info.pop("content")
        mtime = info.pop("mtime", None)
        
        post = frontmatter.Post(content, **info)
        with open(full_path, 'w') as f:
            f.write(frontmatter.dumps(post))
        
        if mtime:
            os.utime(full_path, (mtime.timestamp(), mtime.timestamp()))
    
    # Create test image in Obsidian
    image_path = obsidian_dir / "atomics/2024/12/04/test-image.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    with open(image_path, 'w') as f:
        f.write("Test image content")
    
    # Create files in Jekyll
    for file_path, info in jekyll_files.items():
        full_path = jekyll_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = info.pop("content")
        mtime = info.pop("mtime", None)
        
        post = frontmatter.Post(content, **info)
        with open(full_path, 'w') as f:
            f.write(frontmatter.dumps(post))
        
        if mtime:
            os.utime(full_path, (mtime.timestamp(), mtime.timestamp()))
    
    # Create test image in Jekyll
    image_path = jekyll_dir / "assets/img/posts/test-image.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    with open(image_path, 'w') as f:
        f.write("Test image content")

def test_sync_dry_run():
    """Test that dry run mode shows changes without making them"""
    print("\nTesting sync dry run:")
    
    # Create test directory
    test_dir = Path("test_sync")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Get initial file states
        obsidian_content = {}
        jekyll_content = {}
        
        # Record Obsidian content
        obsidian_dir = test_dir / "PKM/atomics/2024/12/04"
        for md_file in obsidian_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                obsidian_content[md_file.name] = f.read()
        
        # Record Jekyll content
        jekyll_dir = test_dir / "jekyll/_posts"
        for md_file in jekyll_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                jekyll_content[md_file.name] = f.read()
        
        # Run sync in dry run mode
        engine = SyncEngine(
            str(test_dir / "PKM"),
            str(test_dir / "jekyll"),
            debug=True,
            dry_run=True
        )
        
        engine.sync()
        
        # Verify no files were changed
        success = True
        
        print("\nChecking Obsidian files:")
        for md_file in obsidian_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                current = f.read()
                original = obsidian_content[md_file.name]
                unchanged = current == original
                success = success and unchanged
                print(f"  {md_file.name}: {'✓' if unchanged else '✗'}")
        
        print("\nChecking Jekyll files:")
        for md_file in jekyll_dir.glob("*.md"):
            with open(md_file, 'r') as f:
                current = f.read()
                original = jekyll_content[md_file.name]
                unchanged = current == original
                success = success and unchanged
                print(f"  {md_file.name}: {'✓' if unchanged else '✗'}")
        
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_sync_execution():
    """Test that sync actually makes changes in normal mode"""
    print("\nTesting sync execution:")
    
    # Create test directory
    test_dir = Path("test_sync")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Run sync
        engine = SyncEngine(
            str(test_dir / "PKM"),
            str(test_dir / "jekyll"),
            debug=True
        )
        
        engine.sync()
        
        # Verify files were updated
        success = True
        
        print("\nChecking file updates:")
        
        # Check Obsidian → Jekyll sync
        jekyll_file = test_dir / "jekyll/_posts/2024-12-04-newer-in-obsidian.md"
        with open(jekyll_file, 'r') as f:
            content = f.read()
            updated = "Updated in Obsidian" in content
            success = success and updated
            print(f"  Obsidian → Jekyll: {'✓' if updated else '✗'}")
        
        # Check Jekyll → Obsidian sync
        obsidian_file = test_dir / "PKM/atomics/2024/12/04/newer-in-jekyll.md"
        with open(obsidian_file, 'r') as f:
            content = f.read()
            updated = "Updated in Jekyll" in content
            success = success and updated
            print(f"  Jekyll → Obsidian: {'✓' if updated else '✗'}")
        
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_sync():
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')

if __name__ == "__main__":
    # Run all tests
    test_sync_dry_run()
    test_sync_execution() 