#!/usr/bin/env python3

import yaml
import os
from pathlib import Path
from typing import Dict, List, Set

def load_checklist() -> dict:
    """Load the checklist YAML file."""
    checklist_path = Path("docs/strategy/implementation/checklist.yaml")
    with open(checklist_path) as f:
        return yaml.safe_load(f)

def verify_files(files: List[str]) -> Set[str]:
    """Verify which files from the list exist and return missing ones."""
    missing = set()
    for file_path in files:
        if not os.path.exists(file_path):
            missing.add(file_path)
    return missing

def analyze_progress(data: dict, prefix: str = "") -> Dict[str, dict]:
    """Recursively analyze the checklist structure."""
    results = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            if "status" in value:  # This is a feature group
                status = value["status"]
                files = value.get("files", [])
                features = value.get("features", [])
                missing_files = verify_files(files)
                
                results[f"{prefix}{key}"] = {
                    "status": status,
                    "feature_count": len(features),
                    "file_count": len(files),
                    "missing_files": list(missing_files),
                    "complete": status == "Complete" and not missing_files
                }
            else:  # This is a category
                results.update(analyze_progress(value, f"{prefix}{key}/"))
    
    return results

def main():
    """Main function to analyze and display progress."""
    checklist = load_checklist()
    results = analyze_progress(checklist)
    
    # Print summary
    print("\nFeature Implementation Progress:")
    print("=" * 50)
    
    complete = 0
    total = 0
    missing_files_total = []
    
    for path, data in sorted(results.items()):
        status_symbol = "✓" if data["complete"] else "⨯"
        print(f"\n{status_symbol} {path}")
        print(f"  Status: {data['status']}")
        print(f"  Features: {data['feature_count']}")
        print(f"  Files: {data['file_count']}")
        
        if data["missing_files"]:
            print("  Missing files:")
            for file in data["missing_files"]:
                print(f"    - {file}")
            missing_files_total.extend(data["missing_files"])
        
        if data["complete"]:
            complete += 1
        total += 1
    
    # Print overall statistics
    print("\nOverall Progress:")
    print("=" * 50)
    print(f"Complete features: {complete}/{total} ({(complete/total)*100:.1f}%)")
    
    if missing_files_total:
        print("\nMissing Files Summary:")
        print("=" * 50)
        for file in sorted(set(missing_files_total)):
            print(f"- {file}")

if __name__ == "__main__":
    main() 