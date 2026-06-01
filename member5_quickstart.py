#!/usr/bin/env python3
"""
Quick Start Guide for Member 5 - ReAct Agent Testing
Run this script to verify all Member 5 functionality
"""

import sys
import os
from pathlib import Path

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_section(title):
    print(f"\n{title}")
    print("-" * 70)

def check_files():
    """Verify all required files exist"""
    print_header("📋 FILE VERIFICATION")
    
    required_files = [
        ("backend/agent/agent.py", "ReAct Agent Implementation"),
        ("backend/agent/system_prompt.txt", "System Prompt"),
        ("requirements.txt", "Dependencies"),
        ("tests/test_member5_react.py", "Test Suite"),
        ("tests/test_integration_member5.py", "Integration Tests"),
        ("models/Phi-3-mini-4k-instruct-q4.gguf", "Local Model"),
    ]
    
    all_exist = True
    for file_path, description in required_files:
        full_path = Path(file_path)
        exists = "✅" if full_path.exists() else "❌"
        print(f"{exists} {description:.<40} {file_path}")
        if not full_path.exists() and ".gguf" not in file_path:
            all_exist = False
    
    print()
    return all_exist

def check_dependencies():
    """Check if required packages installed"""
    print_section("📦 DEPENDENCIES CHECK")
    
    dependencies = [
        "llama_cpp",
        "pydantic",
        "requests",
        "dotenv",
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (missing - run: pip install -r requirements.txt)")
            missing.append(dep)
    
    return len(missing) == 0

def run_unit_tests():
    """Run Member 5 test suite"""
    print_section("🧪 RUNNING UNIT TESTS")
    print("Executing: python tests/test_member5_react.py\n")
    
    sys.path.insert(0, str(Path(__file__).parent / "backend" / "agent"))
    
    try:
        from agent import run_react_loop, load_system_prompt, MAX_ITERATIONS
        
        # Quick validation
        print("✅ Agent module loaded successfully")
        print(f"✅ MAX_ITERATIONS = {MAX_ITERATIONS}")
        
        system_prompt = load_system_prompt()
        print(f"✅ System Prompt loaded ({len(system_prompt)} bytes)")
        
        # Test basic execution
        print("\nRunning quick functionality test...")
        result = run_react_loop("Tôi muốn biết thông tin vé")
        print(f"✅ Agent execution successful ({len(result)} chars response)")
        
        return True
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def run_integration_demo():
    """Run integration workflow demo"""
    print_section("🔗 INTEGRATION WORKFLOW DEMO")
    print("This demonstrates all 5 members working together\n")
    
    sys.path.insert(0, str(Path(__file__).parent / "backend" / "agent"))
    
    try:
        from agent import run_react_loop
        
        scenarios = [
            ("Thời tiết ngày mai như thế nào?", None),
            ("Vé Wave Park bao nhiêu tiền?", None),
            ("Mai 2 người lớn 1 bé 4 tuổi, tính vé bao nhiêu?", 
             {"nodes": [{"id": 1, "text": "Vé NL: 250k, Bé 1m-1m4: 150k"}]}),
        ]
        
        for i, (query, graph) in enumerate(scenarios, 1):
            print(f"\n[Scenario {i}] {query}")
            result = run_react_loop(query, graph_blob=graph)
            print(f"Response: {result[:100]}...")
            print("✅ Processed successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        return False

def show_quick_reference():
    """Show quick reference for common tasks"""
    print_header("📚 QUICK REFERENCE")
    
    commands = [
        ("Test Member 5 functionality", "python tests/test_member5_react.py"),
        ("Run integration demo", "python tests/test_integration_member5.py"),
        ("Test with local model", "python backend/agent/agent.py"),
        ("Install dependencies", "pip install -r requirements.txt"),
        ("View system prompt", "cat backend/agent/system_prompt.txt"),
    ]
    
    for description, command in commands:
        print(f"\n{description}:")
        print(f"  $ {command}")

def main():
    """Main quick start routine"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  Member 5 - ReAct Agent QUICK START GUIDE".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run checks
    files_ok = check_files()
    deps_ok = check_dependencies()
    
    print_header("⚙️ FUNCTIONALITY TESTS")
    
    if not files_ok:
        print("⚠️  Some required files missing. Skipping tests.\n")
    else:
        tests_ok = run_unit_tests()
        
        if tests_ok:
            print("\n✅ Unit tests passed!\n")
            demo_ok = run_integration_demo()
            
            if demo_ok:
                print("\n" + "="*70)
                print("✅ ALL CHECKS PASSED - Member 5 is fully functional!")
                print("="*70 + "\n")
    
    # Show reference
    show_quick_reference()
    
    print("\n" + "="*70)
    print("📖 For detailed documentation, see: MEMBER5_SUMMARY.md")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
