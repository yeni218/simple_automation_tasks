#!/usr/bin/env python
# Test script for verifying step callback functionality with fixed imports

import sys
import os
import time
import datetime
import pyautogui
from PIL import Image

# Add modules directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
try:
    from modules.ai_vision_controller import EnhancedAIVisionController
    from modules.ai_integration import AIIntegration
except ImportError as e:
    print(f"Error importing modules: {str(e)}")
    sys.exit(1)

def on_step_callback(step_num, description, image_path):
    """Callback function for step screenshots"""
    print(f"Step callback received: {step_num} - {description} - {image_path}")
    
def main():
    """Main entry point"""
    print("Testing step callback functionality with fixed imports...")
    
    # Create controller
    controller = EnhancedAIVisionController()
    ai_manager = AIIntegration(controller)
    controller.ai_manager = ai_manager
    
    # Set step callback
    controller.set_step_callback(on_step_callback)
    
    # Verify that the callback is set correctly
    if hasattr(controller, 'step_callback') and controller.step_callback == on_step_callback:
        print("✓ step_callback attribute set correctly")
    else:
        print("✗ step_callback attribute not set correctly")
        
    if hasattr(controller, 'on_step_screenshot') and controller.on_step_screenshot == on_step_callback:
        print("✓ on_step_screenshot attribute set correctly")
    else:
        print("✗ on_step_screenshot attribute not set correctly")
    
    # Take a screenshot
    print("Taking a screenshot...")
    screenshot = controller.take_screenshot()
    
    if screenshot:
        # Save screenshot
        timestamp = int(time.time())
        filename = f"test_fixed_screenshot_{timestamp}.png"
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}")
        
        # Simulate a step
        print("Simulating a step...")
        controller.step_counter = 1
        step_path = os.path.join(controller.session_dir, "step_001_test.png")
        
        # Copy the test screenshot to the step path
        screenshot.save(step_path)
        
        # Call capture_step_screenshot which should trigger the callback
        print("Calling capture_step_screenshot...")
        result_path = controller.capture_step_screenshot("Test step fixed")
        print(f"Capture result path: {result_path}")
        
        # Create a simple command sequence
        commands = [
            "click: [100, 100]",
            "type: Hello, world!",
            "press: enter"
        ]
        
        # Execute the command sequence
        print("Executing command sequence...")
        result = controller.execute_command_sequence(commands)
        print(f"Command sequence result: {result}")
        
        print("Test completed")
    else:
        print("Failed to take screenshot")
    
if __name__ == "__main__":
    main() 