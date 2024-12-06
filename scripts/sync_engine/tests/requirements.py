"""Test requirements and metadata system"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import yaml
import inspect
import pytest

@dataclass
class TestRequirements:
    """Test requirements metadata"""
    features: List[str]
    edge_cases: List[str]
    dependencies: List[str]
    expected_coverage: float
    description: str

def load_requirements(test_module: str) -> Dict[str, TestRequirements]:
    """Load test requirements from YAML file"""
    # Get the module file path
    module_path = Path(test_module)
    # Look for corresponding YAML file
    yaml_path = module_path.parent / (module_path.stem + '_requirements.yaml')
    
    if not yaml_path.exists():
        return {}
        
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
        
    requirements = {}
    for test_name, test_data in data.items():
        requirements[test_name] = TestRequirements(**test_data)
    
    return requirements

def test_requirements(**kwargs):
    """Decorator to add requirements metadata to test functions"""
    def decorator(test_func):
        # Store requirements in function metadata
        test_func.requirements = TestRequirements(**kwargs)
        return test_func
    return decorator

def get_test_requirements(test_func) -> Optional[TestRequirements]:
    """Get requirements for a test function"""
    # Check decorator metadata
    if hasattr(test_func, 'requirements'):
        return test_func.requirements
        
    # Check YAML file
    module_file = inspect.getfile(test_func)
    requirements = load_requirements(module_file)
    return requirements.get(test_func.__name__)

def pytest_collection_modifyitems(items):
    """Pytest hook to process test requirements"""
    for item in items:
        # Get requirements for test
        reqs = get_test_requirements(item.function)
        if reqs:
            # Add requirements to test metadata
            item.requirements = reqs
            # Add markers based on features
            for feature in reqs.features:
                marker = pytest.mark.requirement(feature)
                item.add_marker(marker) 