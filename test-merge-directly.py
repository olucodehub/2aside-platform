"""Direct test of the merge matching function"""
import sys
import os

# Add paths
sys.path.insert(0, r'C:\Dev\Rendezvous\2-Aside\funding-service')
sys.path.insert(0, r'C:\Dev\Rendezvous\2-Aside')

print("Starting direct merge test...")

try:
    from auto_matcher import run_matching
    print("Successfully imported run_matching")

    print("\nCalling run_matching()...")
    run_matching()
    print("\n✓ Merge completed successfully!")

except Exception as e:
    print(f"\n✗ Error occurred: {e}")
    import traceback
    traceback.print_exc()
