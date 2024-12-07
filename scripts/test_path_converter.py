import os
from pathlib import Path
from utils.path_converter import PathConverter
from dotenv import load_dotenv

def test_post_path_conversion():
    """Test converting post paths between Obsidian and Jekyll formats"""
    print("\nTesting post path conversion:")
    
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create path converter
    converter = PathConverter(vault_root, jekyll_root, debug=False)
    
    test_cases = [
        # Basic post
        {
            "obsidian_path": Path(vault_root) / "atomics/2024/12/04/testing-jekyll-sync-engine.md",
            "jekyll_path": Path(jekyll_root) / "_posts/2024-12-04-testing-jekyll-sync-engine.md"
        },
        # Post with underscores
        {
            "obsidian_path": Path(vault_root) / "atomics/2024/12/04/test_file_name.md",
            "jekyll_path": Path(jekyll_root) / "_posts/2024-12-04-test_file_name.md"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        # Test Obsidian → Jekyll
        converted_jekyll = converter.obsidian_to_jekyll_post(test["obsidian_path"])
        jekyll_success = converted_jekyll == test["jekyll_path"]
        print(f"  Obsidian → Jekyll: {'✓' if jekyll_success else '✗'}")
        if not jekyll_success:
            print(f"    Input:    {test['obsidian_path']}")
            print(f"    Expected: {test['jekyll_path']}")
            print(f"    Got:      {converted_jekyll}")
        
        # Test Jekyll → Obsidian
        converted_obsidian = converter.jekyll_to_obsidian_post(test["jekyll_path"])
        obsidian_success = converted_obsidian == test["obsidian_path"]
        print(f"  Jekyll → Obsidian: {'✓' if obsidian_success else '✗'}")
        if not obsidian_success:
            print(f"    Input:    {test['jekyll_path']}")
            print(f"    Expected: {test['obsidian_path']}")
            print(f"    Got:      {converted_obsidian}")

def test_image_path_conversion():
    """Test converting image paths between Obsidian and Jekyll formats"""
    print("\nTesting image path conversion:")
    
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create path converter
    converter = PathConverter(vault_root, jekyll_root, debug=False)
    
    test_cases = [
        # Basic image
        {
            "obsidian_path": "![[atomics/2024/12/04/test-header-image.png]]",
            "jekyll_path": "/assets/img/posts/test-header-image.png",
            "post_name": "2024-12-04-test-post.md"
        },
        # Image with underscores
        {
            "obsidian_path": "![[atomics/2024/12/04/test_image_name.png]]",
            "jekyll_path": "/assets/img/posts/test_image_name.png",
            "post_name": "2024-12-04-test-post.md"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        # Test Obsidian → Jekyll
        converted_jekyll = converter.obsidian_to_jekyll_image(test["obsidian_path"])
        jekyll_success = converted_jekyll == test["jekyll_path"]
        print(f"  Obsidian → Jekyll: {'✓' if jekyll_success else '✗'}")
        if not jekyll_success:
            print(f"    Input:    {test['obsidian_path']}")
            print(f"    Expected: {test['jekyll_path']}")
            print(f"    Got:      {converted_jekyll}")
        
        # Test Jekyll → Obsidian
        converted_obsidian = converter.jekyll_to_obsidian_image(test["jekyll_path"], test["post_name"])
        expected_obsidian = test["obsidian_path"]
        obsidian_success = converted_obsidian == expected_obsidian
        print(f"  Jekyll → Obsidian: {'✓' if obsidian_success else '✗'}")
        if not obsidian_success:
            print(f"    Input:    {test['jekyll_path']}")
            print(f"    Expected: {expected_obsidian}")
            print(f"    Got:      {converted_obsidian}")

def test_frontmatter_image_path():
    """Test converting image paths in frontmatter"""
    print("\nTesting frontmatter image path conversion:")
    
    # Load environment variables
    load_dotenv()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return
    
    # Create path converter
    converter = PathConverter(vault_root, jekyll_root, debug=False)
    
    test_cases = [
        # Basic image
        {
            "obsidian_path": '"[[atomics/2024/12/04/test-header-image.png]]"',
            "jekyll_path": '"/assets/img/posts/test-header-image.png"',
            "post_name": "2024-12-04-test-post.md"
        },
        # Image with underscores
        {
            "obsidian_path": '"[[atomics/2024/12/04/test_image_name.png]]"',
            "jekyll_path": '"/assets/img/posts/test_image_name.png"',
            "post_name": "2024-12-04-test-post.md"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        # Test Obsidian → Jekyll
        converted_jekyll = converter.obsidian_to_jekyll_image(test["obsidian_path"], in_frontmatter=True)
        jekyll_success = converted_jekyll == test["jekyll_path"]
        print(f"  Obsidian → Jekyll: {'✓' if jekyll_success else '✗'}")
        if not jekyll_success:
            print(f"    Input:    {test['obsidian_path']}")
            print(f"    Expected: {test['jekyll_path']}")
            print(f"    Got:      {converted_jekyll}")
        
        # Test Jekyll → Obsidian
        converted_obsidian = converter.jekyll_to_obsidian_image(
            test["jekyll_path"], 
            test["post_name"],
            in_frontmatter=True
        )
        expected_obsidian = test["obsidian_path"]
        obsidian_success = converted_obsidian == expected_obsidian
        print(f"  Jekyll → Obsidian: {'✓' if obsidian_success else '✗'}")
        if not obsidian_success:
            print(f"    Input:    {test['jekyll_path']}")
            print(f"    Expected: {expected_obsidian}")
            print(f"    Got:      {converted_obsidian}")

if __name__ == "__main__":
    # Run all tests
    test_post_path_conversion()
    test_image_path_conversion()
    test_frontmatter_image_path() 