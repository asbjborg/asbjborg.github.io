import re
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class FrontmatterHandler:
    def __init__(self, path_converter, debug: bool = False, dry_run: bool = False):
        self.path_converter = path_converter
        self.debug = debug
        self.dry_run = dry_run
    
    def obsidian_to_jekyll(self, frontmatter: Dict[str, Any], obsidian_path: Path) -> Dict[str, Any]:
        """Convert Obsidian frontmatter to Jekyll format"""
        jekyll_fm = {}
        
        # Copy title as is
        if 'title' in frontmatter:
            jekyll_fm['title'] = frontmatter['title']
        
        # Convert time from "HH:mm:ss" to seconds since midnight
        if 'time' in frontmatter:
            try:
                time_str = frontmatter['time']
                if isinstance(time_str, str):
                    h, m, s = map(int, time_str.split(':'))
                    jekyll_fm['time'] = h * 3600 + m * 60 + s
            except Exception as e:
                if self.debug:
                    print(f"Error converting time: {str(e)}")
        
        # Convert image path
        if 'image' in frontmatter:
            try:
                image_ref = frontmatter['image']
                jekyll_fm['image'] = self.path_converter.obsidian_to_jekyll_image(image_ref, in_frontmatter=True)
            except Exception as e:
                if self.debug:
                    print(f"Error converting image path: {str(e)}")
        
        # Copy tags, filtering out system tags
        if 'tags' in frontmatter:
            tags = frontmatter.get('tags', [])
            if isinstance(tags, list):
                jekyll_fm['tags'] = [
                    tag for tag in tags 
                    if tag not in ['atomic']  # Add other system tags here
                ]
        
        return jekyll_fm
    
    def jekyll_to_obsidian(self, frontmatter: Dict[str, Any], jekyll_path: Path) -> Dict[str, Any]:
        """Convert Jekyll frontmatter to Obsidian format"""
        obsidian_fm = {}
        
        # Copy title as is
        if 'title' in frontmatter:
            obsidian_fm['title'] = frontmatter['title']
        
        # Convert time from seconds to "HH:mm:ss"
        if 'time' in frontmatter:
            try:
                seconds = int(frontmatter['time'])
                h, remainder = divmod(seconds, 3600)
                m, s = divmod(remainder, 60)
                obsidian_fm['time'] = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception as e:
                if self.debug:
                    print(f"Error converting time: {str(e)}")
        
        # Convert image path
        if 'image' in frontmatter:
            try:
                image_path = frontmatter['image']
                obsidian_fm['image'] = self.path_converter.jekyll_to_obsidian_image(
                    image_path, 
                    jekyll_path.name,
                    in_frontmatter=True
                )
            except Exception as e:
                if self.debug:
                    print(f"Error converting image path: {str(e)}")
        
        # Extract date from Jekyll filename for the date field
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})', jekyll_path.stem)
        if match:
            year, month, day = match.groups()
            # Convert to Obsidian date format with wikilink
            weekday = datetime(int(year), int(month), int(day)).strftime('%A')
            obsidian_fm['date'] = f'"[[daily_notes/{year}-{month}-{day}-{weekday}|{year}-{month}-{day}-{weekday}]]"'
        
        # Copy tags
        if 'tags' in frontmatter:
            obsidian_fm['tags'] = frontmatter['tags']
        else:
            obsidian_fm['tags'] = ['blog']  # Default tag
        
        # Add required Obsidian fields
        obsidian_fm.update({
            'moc': '',
            'upsert': '',
            'upserted': '',
            'status': 'published',
        })
        
        # Only update synced timestamp if not in dry run mode
        if not self.dry_run:
            obsidian_fm['synced'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return obsidian_fm
