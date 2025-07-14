#!/usr/bin/env python3
"""CLI usage examples for the refactored email manager."""

import sys

def show_usage_examples():
    """Display CLI usage examples."""
    print("📧 Email Manager CLI - Usage Examples")
    print("=" * 50)
    
    print("\n1. Basic Commands:")
    print("   python main.py --help")
    print("   python main.py status")
    print("   python main.py fetch-emails")
    print("   python main.py list-emails --limit 20")
    
    print("\n2. Search Commands:")
    print("   python main.py search 'meeting tomorrow'")
    print("   python main.py search 'invoice' --date-after 2025-01-01")
    print("   python main.py search 'payment' --regex '\\d{1,6}' --limit 5")
    
    print("\n3. NEW - Interactive Search Loop:")
    print("   python main.py search-loop")
    print("   python main.py search-loop --after-date 2025-01-01")
    print("   # Then type queries interactively:")
    print("   # > Enter search query (or q to quit): meeting")
    print("   # > Enter search query (or q to quit): invoice")
    print("   # > Enter search query (or q to quit): q")
    
    
    print("\n4. Email Details:")
    print("   python main.py get-email <UID>")
    
    print("\n📊 Performance Features:")
    print("   - GPU acceleration (CUDA if available)")
    print("   - FAISS IndexHNSWFlat for scalable search")
    print("   - Batch processing with torch.no_grad()")
    print("   - Shared core components for search-loop")
    print("   - Results sorted by date DESC")
    
    print("\n🔍 Search Loop Benefits:")
    print("   - Sub-second search response")
    print("   - Model loaded once, reused for all queries")
    print("   - Interactive experience")
    print("   - Date filtering support")
    print("   - Ctrl+C safe exit")

def run_sample_searches():
    """Run sample searches to demonstrate functionality."""
    import subprocess
    import sys
    
    print("\n🚀 Running Sample Searches...")
    print("=" * 40)
    
    # Example searches
    searches = [
        "python main.py status",
        "python main.py list-emails --limit 3",
        "python main.py search 'meeting'",
    ]
    
    for cmd in searches:
        print(f"\n> {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print("Output:", result.stdout[:500])
            if result.stderr:
                print("Error:", result.stderr[:200])
        except subprocess.TimeoutExpired:
            print("Command timed out")
        except Exception as e:
            print(f"Error running command: {e}")
        print("-" * 40)

if __name__ == "__main__":
    show_usage_examples()
    
    # Optionally run sample searches
    if len(sys.argv) > 1 and sys.argv[1] == "--run-samples":
        run_sample_searches()
