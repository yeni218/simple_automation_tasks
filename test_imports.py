#!/usr/bin/env python
# Test script for verifying imports in EnhancedAIVisionController

import sys
import os
import traceback
import datetime
import pyautogui

# Add modules directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
try:
    from modules.ai_vision_controller import EnhancedAIVisionController
    print("Successfully imported EnhancedAIVisionController", flush=True)
except ImportError as e:
    print(f"Error importing modules: {str(e)}", flush=True)
    sys.exit(1)

def main():
    """Main entry point"""
    print("Testing EnhancedAIVisionController imports...", flush=True)
    
    # Create controller
    try:
        controller = EnhancedAIVisionController()
        print("Controller created successfully", flush=True)
    except Exception as e:
        print(f"Error creating controller: {str(e)}", flush=True)
        traceback.print_exc()
        return
    
    # Test datetime import
    try:
        # Create a session directory
        print(f"Session directory: {controller.session_dir}", flush=True)
        
        # Test writing to log file
        log_path = os.path.join(controller.session_dir, "test_log.txt")
        with open(log_path, "w") as log_file:
            current_time = datetime.datetime.now()
            log_file.write(f"Test log entry at {current_time}\n")
        print(f"✓ Successfully wrote to log file using datetime: {log_path}", flush=True)
    except Exception as e:
        print(f"✗ Error testing datetime: {str(e)}", flush=True)
        traceback.print_exc()
    
    # Test pyautogui import
    try:
        # Get screen size
        screen_width, screen_height = pyautogui.size()
        print(f"✓ Successfully got screen size using pyautogui: {screen_width}x{screen_height}", flush=True)
    except Exception as e:
        print(f"✗ Error testing pyautogui: {str(e)}", flush=True)
        traceback.print_exc()
    
    print("Test completed", flush=True)

if __name__ == "__main__":
    main() 