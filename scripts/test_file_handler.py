import os
import shutil
from pathlib import Path
import frontmatter
from sync.file_handler import FileHandler

def setup_test_files(test_dir: Path) -> None:
    """Create test files with various statuses"""
    # Create test structure
    files = {
        "atomics/2024/12/04/published-post.md": {
            "title": "Published Post",
            "status": "published"
        },
        "atomics/2024/12/04/draft-post.md": {
            "title": "Draft Post",
            "status": "draft"
        },
        "atomics/2024/12/04/private-post.md": {
            "title": "Private Post",
            "status": "private"
        },
        "atomics/2024/12/04/no-status-post.md": {
            "title": "No Status Post"
        }
    }
    
    # Create the files with frontmatter
    for file_path, fm in files.items():
        full_path = test_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        post = frontmatter.Post("Test content", **fm)
        with open(full_path, 'w') as f:
            f.write(frontmatter.dumps(post))

def setup_jekyll_files(jekyll_dir: Path) -> None:
    """Create test Jekyll files"""
    # Create posts directory with some files
    posts_dir = jekyll_dir / "_posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    post_files = [
        "2024-12-04-test-post-1.md",
        "2024-12-04-test-post-2.md"
    ]
    
    for post in post_files:
        with open(posts_dir / post, 'w') as f:
            f.write("Test content")
    
    # Create assets directory with some files
    assets_dir = jekyll_dir / "assets" / "img" / "posts"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    asset_files = [
        "test-image-1.png",
        "test-image-2.jpg"
    ]
    
    for asset in asset_files:
        with open(assets_dir / asset, 'w') as f:
            f.write("Test content")

def test_get_obsidian_files():
    """Test getting Obsidian files with different statuses"""
    print("\nTesting get_obsidian_files:")
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create test directory
    test_dir = Path("test_vault")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_test_files(test_dir)
        
        # Create file handler with test directory
        handler = FileHandler(str(test_dir), jekyll_root, debug=False)
        
        # Get files
        published, drafts = handler.get_obsidian_files()
        
        # Verify results
        print("\nPublished files:")
        published_count = 0
        for f in published:
            print(f"  - {f.relative_to(test_dir)}")
            published_count += 1
        print(f"Found {published_count} published files (expected 1)")
        
        print("\nDraft files:")
        draft_count = 0
        for f in drafts:
            print(f"  - {f.relative_to(test_dir)}")
            draft_count += 1
        print(f"Found {draft_count} draft files (expected 1)")
        
        # Verify counts
        success = published_count == 1 and draft_count == 1
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_get_jekyll_files():
    """Test getting Jekyll posts and assets"""
    print("\nTesting get_jekyll_files:")
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create test directory
    test_dir = Path("test_jekyll")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    try:
        # Setup test files
        setup_jekyll_files(test_dir)
        
        # Create file handler with test directory
        handler = FileHandler(vault_root, str(test_dir), debug=False)
        
        # Get files
        posts, assets = handler.get_jekyll_files()
        
        # Verify results
        print("\nJekyll posts:")
        post_count = 0
        for f in posts:
            print(f"  - {f.relative_to(test_dir)}")
            post_count += 1
        print(f"Found {post_count} posts (expected 2)")
        
        print("\nJekyll assets:")
        asset_count = 0
        for f in assets:
            print(f"  - {f.relative_to(test_dir)}")
            asset_count += 1
        print(f"Found {asset_count} assets (expected 2)")
        
        # Verify counts
        success = post_count == 2 and asset_count == 2
        print(f"\nTest result: {'✓' if success else '✗'}")
        
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    # Run all tests
    test_get_obsidian_files()
    test_get_jekyll_files() 