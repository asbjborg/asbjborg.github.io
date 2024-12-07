import os
from pathlib import Path
from datetime import datetime
from utils.frontmatter import FrontmatterHandler
from utils.path_converter import PathConverter

def test_obsidian_to_jekyll():
    """Test converting Obsidian frontmatter to Jekyll format"""
    print("\nTesting obsidian_to_jekyll:")
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create test path converter using actual paths
    path_converter = PathConverter(vault_root, jekyll_root, debug=False)
    handler = FrontmatterHandler(path_converter, debug=False)
    
    test_cases = [
        # Basic frontmatter
        {
            "input": {
                "frontmatter": {
                    "title": "Test Post",
                    "status": "published"
                },
                "path": Path(vault_root) / "atomics/2024/12/04/test-post.md"
            },
            "expected": {
                "title": "Test Post"
            }
        },
        # Time conversion
        {
            "input": {
                "frontmatter": {
                    "title": "Time Test",
                    "time": "14:30:45"
                },
                "path": Path(vault_root) / "atomics/2024/12/04/time-test.md"
            },
            "expected": {
                "title": "Time Test",
                "time": 14 * 3600 + 30 * 60 + 45
            }
        },
        # Image path conversion
        {
            "input": {
                "frontmatter": {
                    "title": "Image Test",
                    "image": "[[atomics/2024/12/04/test-image.png]]"
                },
                "path": Path(vault_root) / "atomics/2024/12/04/image-test.md"
            },
            "expected": {
                "title": "Image Test",
                "image": "/assets/img/posts/test-image.png"
            }
        },
        # Tags filtering
        {
            "input": {
                "frontmatter": {
                    "title": "Tags Test",
                    "tags": ["blog", "atomic", "test"]
                },
                "path": Path(vault_root) / "atomics/2024/12/04/tags-test.md"
            },
            "expected": {
                "title": "Tags Test",
                "tags": ["blog", "test"]
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        result = handler.obsidian_to_jekyll(test["input"]["frontmatter"], test["input"]["path"])
        success = result == test["expected"]
        print(f"\nTest {i}: {'✓' if success else '✗'}")
        if not success:
            print(f"  Input:    {test['input']['frontmatter']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Got:      {result}")

def test_jekyll_to_obsidian():
    """Test converting Jekyll frontmatter to Obsidian format"""
    print("\nTesting jekyll_to_obsidian:")
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create test path converter using actual paths
    path_converter = PathConverter(vault_root, jekyll_root, debug=False)
    handler = FrontmatterHandler(path_converter, debug=False)
    
    test_cases = [
        # Basic frontmatter
        {
            "input": {
                "frontmatter": {
                    "title": "Test Post"
                },
                "path": Path(jekyll_root) / "_posts/2024-12-04-test-post.md"
            },
            "expected": {
                "title": "Test Post",
                "date": '"[[daily_notes/2024-12-04-Wednesday|2024-12-04-Wednesday]]"',
                "tags": ["blog"],
                "moc": "",
                "upsert": "",
                "upserted": "",
                "status": "published"
                # synced is dynamic, tested separately
            }
        },
        # Time conversion
        {
            "input": {
                "frontmatter": {
                    "title": "Time Test",
                    "time": 52245  # 14:30:45
                },
                "path": Path(jekyll_root) / "_posts/2024-12-04-time-test.md"
            },
            "expected": {
                "title": "Time Test",
                "time": "14:30:45",
                "date": '"[[daily_notes/2024-12-04-Wednesday|2024-12-04-Wednesday]]"',
                "tags": ["blog"],
                "moc": "",
                "upsert": "",
                "upserted": "",
                "status": "published"
            }
        },
        # Image path conversion
        {
            "input": {
                "frontmatter": {
                    "title": "Image Test",
                    "image": "/assets/img/posts/test-image.png"
                },
                "path": Path(jekyll_root) / "_posts/2024-12-04-image-test.md"
            },
            "expected": {
                "title": "Image Test",
                "image": '"[[atomics/2024/12/04/test-image.png]]"',
                "date": '"[[daily_notes/2024-12-04-Wednesday|2024-12-04-Wednesday]]"',
                "tags": ["blog"],
                "moc": "",
                "upsert": "",
                "upserted": "",
                "status": "published"
            }
        },
        # Custom tags
        {
            "input": {
                "frontmatter": {
                    "title": "Tags Test",
                    "tags": ["blog", "test"]
                },
                "path": Path(jekyll_root) / "_posts/2024-12-04-tags-test.md"
            },
            "expected": {
                "title": "Tags Test",
                "tags": ["blog", "test"],
                "date": '"[[daily_notes/2024-12-04-Wednesday|2024-12-04-Wednesday]]"',
                "moc": "",
                "upsert": "",
                "upserted": "",
                "status": "published"
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        result = handler.jekyll_to_obsidian(test["input"]["frontmatter"], test["input"]["path"])
        # Remove synced field for comparison since it's dynamic
        if "synced" in result:
            del result["synced"]
        success = result == test["expected"]
        print(f"\nTest {i}: {'✓' if success else '✗'}")
        if not success:
            print(f"  Input:    {test['input']['frontmatter']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Got:      {result}")

def test_synced_field():
    """Test that synced field is properly formatted"""
    print("\nTesting synced field format:")
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    path_converter = PathConverter(vault_root, jekyll_root, debug=False)
    handler = FrontmatterHandler(path_converter, debug=False)
    
    # Get a basic conversion with synced field
    result = handler.jekyll_to_obsidian(
        {"title": "Test"},
        Path(jekyll_root) / "_posts/2024-12-04-test.md"
    )
    
    # Check synced field format
    synced = result.get("synced", "")
    try:
        # Try to parse the date to validate format
        datetime.strptime(synced, "%Y-%m-%d %H:%M:%S")
        print(f"  Synced field format valid: {synced} ✓")
    except ValueError as e:
        print(f"  Invalid synced field format: {synced} ✗")
        print(f"  Error: {str(e)}")

if __name__ == "__main__":
    # Run all tests
    test_obsidian_to_jekyll()
    test_jekyll_to_obsidian()
    test_synced_field()
