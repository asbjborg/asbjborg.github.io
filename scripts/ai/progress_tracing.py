"""Feature tracking tool for sync engine development.

This script reads YAML files to track:
- Implementation status
- Feature completion
- Pending tasks
- Known issues
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional

def load_yaml(file_path: Path) -> Dict:
    """Load YAML file"""
    with open(file_path) as f:
        return yaml.safe_load(f)

def check_implementation_status(checklist: Dict) -> None:
    """Show implementation status from checklist"""
    print("\n=== Implementation Status ===\n")
    
    for component, details in checklist.items():
        if component in ['coverage_goals', 'implementation_notes']:
            continue
            
        print(f"{component}:\n")
        for module, module_details in details.items():
            print(f"  {module} ({module_details['status']}):")
            for feature in module_details.get('features', []):
                print(f"  ✓ {feature['name']}")
                print(f"    Implemented in: {feature['implemented_in']}")
                print(f"    Verified by: {feature['verified_by']}")
            print()

def check_pending_features(checklist: Dict) -> None:
    """Show pending features and tasks"""
    print("\n=== Pending Features ===\n")
    
    for component, details in checklist.items():
        if component in ['coverage_goals', 'implementation_notes']:
            continue
            
        for module, module_details in details.items():
            if module_details['status'] != 'Complete':
                print(f"{component}.{module}:")
                for feature in module_details.get('features', []):
                    incomplete = [req for req in feature['requirements'] if not req.startswith('✓')]
                    if incomplete:
                        print(f"  - {feature['name']}:")
                        for req in incomplete:
                            print(f"    • {req}")
                print()

def main():
    """Main entry point"""
    # Load tracking files
    root = Path(__file__).parent.parent.parent
    checklist = load_yaml(root / 'docs/strategy/implementation/checklist.yaml')
    
    # Show status
    check_implementation_status(checklist)
    check_pending_features(checklist)

if __name__ == '__main__':
    main()