#!/usr/bin/env python3
"""
Quick verification that the bar chart fix is applied correctly

This script checks the code without running it (no dependencies needed)
"""
import re


def verify_fix():
    """Verify the fix has been applied to a2ui_agent_with_loop.py"""
    print("=" * 70)
    print("Bar Chart Fix Verification")
    print("=" * 70)
    
    file_path = "agents/a2ui_agent_with_loop.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    
    checks = []
    
    # Check 1: Should have all_data_models instead of all_data_contents
    check1 = "all_data_models = []" in content
    checks.append(("✓" if check1 else "✗", "Uses all_data_models list", check1))
    
    # Check 2: Should NOT have the old flattening code
    check2 = "all_data_contents.extend(data_model[" not in content
    checks.append(("✓" if check2 else "✗", "Removed data flattening code", check2))
    
    # Check 3: Should append to all_data_models
    check3 = "all_data_models.append(comp_data[" in content or \
             "all_data_models.append(data_model)" in content
    checks.append(("✓" if check3 else "✗", "Appends to all_data_models", check3))
    
    # Check 4: Should loop through all_data_models
    check4 = "for data_model in all_data_models:" in content
    checks.append(("✓" if check4 else "✗", "Loops through all_data_models", check4))
    
    # Check 5: Should use data_model["path"]
    check5 = 'path=data_model["path"]' in content
    checks.append(("✓" if check5 else "✗", "Uses individual data model paths", check5))
    
    # Check 6: Should use data_model["contents"]
    check6 = 'contents=data_model["contents"]' in content
    checks.append(("✓" if check6 else "✗", "Uses individual data model contents", check6))
    
    # Check 7: Should NOT have path="/ui" for combined data
    check7 = 'path="/ui"' not in content or 'path="/ui"' not in content.split("Initialize Data Model")[1].split("Begin Rendering")[0] if "Initialize Data Model" in content else True
    checks.append(("✓" if check7 else "✗", "Removed hardcoded /ui path", check7))
    
    # Print results
    print("\nCode Verification:")
    print("-" * 70)
    for symbol, description, passed in checks:
        print(f"{symbol} {description}")
    
    all_passed = all(check[2] for check in checks)
    
    print("-" * 70)
    if all_passed:
        print("✅ All checks passed! Bar chart fix is correctly applied.")
    else:
        print("⚠️  Some checks failed. Please review the changes.")
    
    # Additional info
    print("\n" + "=" * 70)
    print("What was fixed:")
    print("=" * 70)
    print("BEFORE: Data models from all components were flattened into one path")
    print("        data_update = DataModelUpdate(path='/ui', contents=all_contents)")
    print("")
    print("AFTER:  Each component's data model is sent separately")
    print("        for data_model in all_data_models:")
    print("            data_update = DataModelUpdate(")
    print("                path=data_model['path'],")
    print("                contents=data_model['contents']")
    print("            )")
    print("")
    print("BENEFIT: Bar charts (and all components) maintain correct data paths")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = verify_fix()
    sys.exit(0 if success else 1)
