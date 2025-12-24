"""
Project Structure Verification Script

Checks that the refactored project structure is correct.
"""

import os
from pathlib import Path


def check_structure():
    """Verify project structure is correct."""
    
    print("=" * 60)
    print(" PROJECT STRUCTURE VERIFICATION")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    # Define expected structure
    expected_structure = {
        "anpr": {
            "type": "dir",
            "children": ["core", "models", "integrations", "utils", "tracking", "__init__.py"]
        },
        "anpr/core": {
            "type": "dir",
            "children": ["__init__.py", "detector.py", "ocr.py"]
        },
        "anpr/models": {
            "type": "dir",
            "children": ["__init__.py", "manager.py", "weights"]
        },
        "anpr/models/weights": {
            "type": "dir",
            "note": "Should contain .pt model files"
        },
        "anpr/integrations": {
            "type": "dir",
            "children": ["__init__.py", "firebase.py"]
        },
        "anpr/utils": {
            "type": "dir",
            "children": ["__init__.py", "config.py", "logger.py"]
        },
        "anpr/tracking": {
            "type": "dir",
            "children": ["__init__.py", "sort.py"]
        },
        "apps": {
            "type": "dir",
            "children": ["__init__.py", "cli.py", "web_gradio.py", "web_streamlit.py", "demo.py"]
        },
        "config": {
            "type": "dir",
            "children": [".env.example"]
        },
        "outputs": {
            "type": "dir",
            "children": ["detected_cars", "detected_plates", "demo_results", "flagged"]
        },
        "logs": {
            "type": "dir"
        },
        "tests": {
            "type": "dir"
        }
    }
    
    # Files that should exist
    required_files = [
        "README.md",
        "requirements.txt",
        "setup.py",
        ".gitignore"
    ]
    
    errors = []
    warnings = []
    passed = 0
    
    # Check directories and files
    print("\n📁 Checking directory structure...")
    for path, spec in expected_structure.items():
        full_path = base_dir / path
        if spec["type"] == "dir":
            if full_path.exists() and full_path.is_dir():
                print(f"  ✓ {path}/")
                passed += 1
                
                # Check children if specified
                if "children" in spec:
                    for child in spec["children"]:
                        child_path = full_path / child
                        if child_path.exists():
                            print(f"    ✓ {child}")
                            passed += 1
                        else:
                            errors.append(f"Missing: {path}/{child}")
                            print(f"    ✗ {child} (MISSING)")
            else:
                errors.append(f"Missing directory: {path}")
                print(f"  ✗ {path}/ (MISSING)")
        else:
            if full_path.exists():
                print(f"  ✓ {path}")
                passed += 1
            else:
                errors.append(f"Missing: {path}")
                print(f"  ✗ {path} (MISSING)")
    
    # Check required root files
    print("\n📄 Checking required files...")
    for filename in required_files:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
            passed += 1
        else:
            errors.append(f"Missing file: {filename}")
            print(f"  ✗ {filename} (MISSING)")
    
    # Check for old files that should be removed
    print("\n🧹 Checking for old files (should be removed)...")
    old_files = [
        "config.py",
        "model_manager.py",
        "logger_config.py",
        "detection_utils.py",
        "firebase_utils.py",
        "util.py",
        "main.py",
        "deploy.py",
        "app_streamlit.py",
        "demo.py"
    ]
    
    for filename in old_files:
        filepath = base_dir / filename
        if filepath.exists():
            warnings.append(f"Old file still exists: {filename}")
            print(f"  ⚠ {filename} (should be removed)")
        else:
            print(f"  ✓ {filename} (correctly removed)")
            passed += 1
    
    # Check model weights
    print("\n🤖 Checking model weights...")
    weights_dir = base_dir / "anpr" / "models" / "weights"
    if weights_dir.exists():
        model_files = list(weights_dir.glob("*.pt"))
        if model_files:
            print(f"  ✓ Found {len(model_files)} model files:")
            for model in model_files:
                print(f"    • {model.name}")
        else:
            warnings.append("No .pt model files found in anpr/models/weights/")
            print("  ⚠ No .pt files found (models need to be downloaded)")
    
    # Print summary
    print("\n" + "=" * 60)
    print(" VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✓ Passed checks: {passed}")
    print(f"⚠ Warnings: {len(warnings)}")
    print(f"✗ Errors: {len(errors)}")
    
    if warnings:
        print("\n⚠ WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if errors:
        print("\n✗ ERRORS:")
        for error in errors:
            print(f"  • {error}")
        print("\n❌ Project structure has issues that need to be fixed!")
        return False
    else:
        if warnings:
            print("\n✅ Project structure is correct (with minor warnings)")
        else:
            print("\n✅ Project structure is perfect!")
        return True


if __name__ == "__main__":
    success = check_structure()
    exit(0 if success else 1)
