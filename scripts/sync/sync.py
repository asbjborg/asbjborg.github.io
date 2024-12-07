import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, NamedTuple
import frontmatter
from .file_handler import FileHandler
from utils.path_converter import PathConverter
from utils.frontmatter import FrontmatterHandler
from dotenv import load_dotenv

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class SyncAction(NamedTuple):
    """Represents a sync action to be taken"""
    source: Path
    target: Path
    direction: str  # 'obsidian_to_jekyll' or 'jekyll_to_obsidian'

class SyncError(Exception):
    """Base class for sync-related errors"""
    pass

class FilePermissionError(SyncError):
    """Raised when there are permission issues with files"""
    pass

class FileOperationError(SyncError):
    """Raised when file operations fail"""
    pass

class SyncEngine:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False, dry_run: bool = False):
        # Load environment variables
        load_dotenv()
        
        self.vault_root = Path(vault_root)
        self.jekyll_root = Path(jekyll_root)
        self.debug = debug
        self.dry_run = dry_run
        
        # Get paths from environment variables with defaults
        self.atomics_path = os.getenv('SYNC_VAULT_ATOMICS', 'atomics')
        self.posts_path = os.getenv('SYNC_JEKYLL_POSTS', '_posts')
        self.assets_path = os.getenv('SYNC_JEKYLL_ASSETS', 'assets/img/posts')
        
        self.file_handler = FileHandler(vault_root, jekyll_root, debug)
        self.path_converter = PathConverter(vault_root, jekyll_root, debug)
        self.frontmatter_handler = FrontmatterHandler(self.path_converter, debug, dry_run)
        self.errors = []  # Track errors during sync
    
    def print_header(self, text: str) -> None:
        """Print a formatted header"""
        if self.debug:
            print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    
    def print_subheader(self, text: str) -> None:
        """Print a formatted subheader"""
        if self.debug:
            print(f"\n{Colors.BLUE}{text}{Colors.ENDC}")
    
    def print_action(self, text: str, dry_run: bool = False) -> None:
        """Print a formatted action message"""
        if self.debug:
            prefix = f"{Colors.YELLOW}WOULD" if dry_run else f"{Colors.GREEN}WILL"
            print(f"  {prefix}: {text}{Colors.ENDC}")
    
    def print_info(self, text: str) -> None:
        """Print formatted info"""
        if self.debug:
            print(f"  {text}")
    
    def print_error(self, text: str) -> None:
        """Print formatted error"""
        if self.debug:
            print(f"{Colors.RED}ERROR: {text}{Colors.ENDC}")
    
    def check_file_permissions(self, path: Path, write: bool = False) -> None:
        """Check if we have the required permissions for a file or directory"""
        try:
            if not path.exists():
                # Check if we can create in parent directory
                if write and not os.access(path.parent, os.W_OK):
                    raise FilePermissionError(f"No write permission for directory: {path.parent}")
                return
            
            # Check read permission
            if not os.access(path, os.R_OK):
                raise FilePermissionError(f"No read permission for: {path}")
            
            # Check write permission if needed
            if write and not os.access(path, os.W_OK):
                raise FilePermissionError(f"No write permission for: {path}")
                
        except Exception as e:
            if isinstance(e, FilePermissionError):
                raise
            raise FileOperationError(f"Failed to check permissions for {path}: {str(e)}")
    
    def determine_sync_actions(self) -> List[SyncAction]:
        """Determine what files need to be synced in which direction"""
        if self.debug:
            print("\nDetermining sync actions...")
        
        actions: List[SyncAction] = []
        
        # Get files from both sides
        obsidian_published, obsidian_drafts = self.file_handler.get_obsidian_files()
        jekyll_posts, jekyll_assets = self.file_handler.get_jekyll_files()
        
        # Create lookup dictionaries with normalized names
        obsidian_lookup = {
            self.file_handler.normalize_filename(self.path_converter.obsidian_to_jekyll_post(p).name): p 
            for p in obsidian_published
        }
        jekyll_lookup = {
            self.file_handler.normalize_filename(p.name): p 
            for p in jekyll_posts
        }
        
        # Check files that exist in both places
        for jekyll_name, obsidian_path in obsidian_lookup.items():
            if jekyll_name in jekyll_lookup:
                jekyll_path = jekyll_lookup[jekyll_name]
                
                # Compare modification times
                obsidian_mtime = obsidian_path.stat().st_mtime
                jekyll_mtime = jekyll_path.stat().st_mtime
                
                if self.debug:
                    print(f"\nComparing: {obsidian_path.name} <-> {jekyll_path.name}")
                    print(f"  Normalized name: {jekyll_name}")
                    print(f"  Obsidian mtime: {datetime.fromtimestamp(obsidian_mtime)}")
                    print(f"  Jekyll mtime: {datetime.fromtimestamp(jekyll_mtime)}")
                
                if obsidian_mtime > jekyll_mtime:
                    if self.debug:
                        print("  -> Obsidian is newer")
                    actions.append(SyncAction(
                        source=obsidian_path,
                        target=jekyll_path,
                        direction='obsidian_to_jekyll'
                    ))
                elif jekyll_mtime > obsidian_mtime:
                    if self.debug:
                        print("  -> Jekyll is newer")
                    actions.append(SyncAction(
                        source=jekyll_path,
                        target=obsidian_path,
                        direction='jekyll_to_obsidian'
                    ))
        
        # Check for files only in Jekyll (need to be created in Obsidian)
        for jekyll_name, jekyll_path in jekyll_lookup.items():
            if jekyll_name not in obsidian_lookup:
                if self.debug:
                    print(f"\nFound Jekyll-only post: {jekyll_path.name}")
                    print(f"  Normalized name: {jekyll_name}")
                
                # Convert Jekyll path to where it should be in Obsidian
                obsidian_path = self.path_converter.jekyll_to_obsidian_post(jekyll_path)
                
                actions.append(SyncAction(
                    source=jekyll_path,
                    target=obsidian_path,
                    direction='jekyll_to_obsidian'
                ))
        
        # We don't need to check for Obsidian-only files
        # They will be synced to Jekyll when their status changes to 'published'
        
        if self.debug:
            print(f"\nFound {len(actions)} sync actions needed:")
            for action in actions:
                print(f"  {action.direction}: {action.source.name} -> {action.target.name}")
                print(f"    Normalized: {self.file_handler.normalize_filename(action.source.name)}")
        
        return actions
    
    def sync_file(self, action: SyncAction) -> None:
        """Sync a single file according to the action"""
        try:
            self.print_subheader(f"Processing: {action.source.name} -> {action.target.name}")
            self.print_info(f"Normalized name: {self.file_handler.normalize_filename(action.source.name)}")
            
            # Check source file permissions
            self.check_file_permissions(action.source)
            
            # Check target permissions if not dry run
            if not self.dry_run:
                self.check_file_permissions(action.target.parent, write=True)
            
            # Create target directory if needed
            if not self.dry_run:
                try:
                    action.target.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise FileOperationError(f"Failed to create directory {action.target.parent}: {str(e)}")
            
            # Read source file
            try:
                post = frontmatter.load(action.source)
            except Exception as e:
                raise FileOperationError(f"Failed to read {action.source}: {str(e)}")
            
            # Convert frontmatter
            if action.direction == 'obsidian_to_jekyll':
                new_fm = self.frontmatter_handler.obsidian_to_jekyll(post.metadata, action.source)
                
                # Convert image references in content
                content = post.content
                for match in re.finditer(r'(!\[\[.*?\]\])', content):
                    obsidian_ref = match.group(1)
                    jekyll_ref = f"![{Path(obsidian_ref).stem}]({self.path_converter.obsidian_to_jekyll_image(obsidian_ref)})"
                    content = content.replace(obsidian_ref, jekyll_ref)
                
                # Copy referenced images
                for match in re.finditer(r'!\[\[(.*?)\]\]', post.content):
                    image_path = self.vault_root / match.group(1)
                    if image_path.exists():
                        target_path = self.jekyll_root / self.assets_path / image_path.name
                        self.print_action(f"Copy image: {image_path.name}", self.dry_run)
                        if not self.dry_run:
                            try:
                                # Check image permissions
                                self.check_file_permissions(image_path)
                                self.check_file_permissions(target_path.parent, write=True)
                                shutil.copy2(image_path, target_path)
                            except Exception as e:
                                raise FileOperationError(f"Failed to copy image {image_path.name}: {str(e)}")
            
            else:  # jekyll_to_obsidian
                new_fm = self.frontmatter_handler.jekyll_to_obsidian(post.metadata, action.source)
                
                # Convert image references in content
                content = post.content
                for match in re.finditer(r'!\[(.*?)\]\((.*?)\)', content):
                    alt_text, jekyll_ref = match.groups()
                    obsidian_ref = self.path_converter.jekyll_to_obsidian_image(jekyll_ref, action.source.name)
                    content = content.replace(f"![{alt_text}]({jekyll_ref})", obsidian_ref)
                
                # Copy referenced images
                for match in re.finditer(r'!\[.*?\]\((.*?)\)', post.content):
                    image_path = self.jekyll_root / match.group(1).lstrip('/')
                    if image_path.exists():
                        target_path = action.target.parent / image_path.name
                        self.print_action(f"Copy image: {image_path.name}", self.dry_run)
                        if not self.dry_run:
                            try:
                                # Check image permissions
                                self.check_file_permissions(image_path)
                                self.check_file_permissions(target_path.parent, write=True)
                                shutil.copy2(image_path, target_path)
                            except Exception as e:
                                raise FileOperationError(f"Failed to copy image {image_path.name}: {str(e)}")
            
            # Create new post with converted frontmatter and content
            if not self.dry_run:
                try:
                    # Write to target with custom YAML formatting
                    with open(action.target, 'w', encoding='utf-8') as f:
                        yaml_lines = []
                        yaml_lines.append('---')
                        for key, value in new_fm.items():
                            if key == 'synced':
                                yaml_lines.append(f'synced: "{value}"')
                            else:
                                yaml_lines.append(f'{key}: {value}')
                        yaml_lines.append('---')
                        yaml_lines.append('')
                        yaml_lines.append(content)
                        f.write('\n'.join(yaml_lines))
                except Exception as e:
                    raise FileOperationError(f"Failed to write {action.target}: {str(e)}")
            else:
                self.print_action(f"Sync file: {action.target.name}", True)
                
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, FilePermissionError):
                error_msg = f"Permission denied: {error_msg}"
            elif isinstance(e, FileOperationError):
                error_msg = f"File operation failed: {error_msg}"
            else:
                error_msg = f"Unexpected error: {error_msg}"
            
            self.print_error(error_msg)
            self.errors.append((action, error_msg))
    
    def sync(self) -> None:
        """Run the sync process"""
        if self.dry_run:
            self.print_header("DRY RUN MODE - No files will be modified")
        else:
            self.print_header("SYNC MODE - Files will be modified")
        
        self.print_subheader("Phase 1: Planning")
        
        try:
            # First, determine what needs to be synced
            actions = self.determine_sync_actions()
            
            if not actions:
                self.print_info("Nothing to sync.")
                return
            
            self.print_subheader("Phase 2: Execution")
            
            # Process each sync action
            for action in actions:
                try:
                    self.sync_file(action)
                except Exception as e:
                    # Error already logged in sync_file
                    continue
            
            # Print summary
            self.print_header("Summary")
            if self.errors:
                self.print_error(f"Completed with {len(self.errors)} errors:")
                for action, error in self.errors:
                    self.print_error(f"  {action.source.name} -> {action.target.name}")
                    self.print_error(f"    {error}")
            else:
                if self.dry_run:
                    self.print_info("Dry run completed - no files were modified")
                else:
                    self.print_info("Sync completed successfully")
                    
        except Exception as e:
            self.print_error(f"Sync failed: {str(e)}")
            raise
