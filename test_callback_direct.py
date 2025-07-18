#!/usr/bin/env python
# Test script for directly testing the step callback functionality

import sys
import os
import time
from PIL import Image

# Add modules directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
try:
    from modules.ai_vision_controller import EnhancedAIVisionController
    from modules.ai_integration import AIIntegration
except ImportError as e:
    print(f"Error importing modules: {str(e)}", flush=True)
    sys.exit(1)

def on_step_callback(step_num, description, image_path):
    """Callback function for step screenshots"""
    print(f"CALLBACK TRIGGERED: Step {step_num} - {description} - {image_path}", flush=True)
    
def main():
    """Main entry point"""
    print("Testing step callback functionality...", flush=True)
    
    # Create controller
    controller = EnhancedAIVisionController()
    print("Controller created", flush=True)
    
    ai_manager = AIIntegration(controller)
    controller.ai_manager = ai_manager
    print("AI manager connected", flush=True)
    
    # Set step callback
    print("Setting step callback...", flush=True)
    controller.set_step_callback(on_step_callback)
    
    # Verify that the callback is set correctly
    if hasattr(controller, 'step_callback') and controller.step_callback == on_step_callback:
        print("✓ step_callback attribute set correctly", flush=True)
    else:
        print("✗ step_callback attribute not set correctly", flush=True)
        
    if hasattr(controller, 'on_step_screenshot') and controller.on_step_screenshot == on_step_callback:
        print("✓ on_step_screenshot attribute set correctly", flush=True)
    else:
        print("✗ on_step_screenshot attribute not set correctly", flush=True)
    
    # Take a screenshot
    print("Taking a screenshot...", flush=True)
    screenshot = controller.take_screenshot()
    
    if screenshot:
        # Save screenshot
        timestamp = int(time.time())
        filename = f"test_direct_screenshot_{timestamp}.png"
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}", flush=True)
        
        # Simulate a step
        print("Simulating a step...", flush=True)
        controller.step_counter = 1
        step_path = os.path.join(controller.session_dir, "step_001_test.png")
        print(f"Step path: {step_path}", flush=True)
        
        # Copy the test screenshot to the step path
        screenshot.save(step_path)
        
        # Call capture_step_screenshot which should trigger the callback
        print("Calling capture_step_screenshot...", flush=True)
        result_path = controller.capture_step_screenshot("Test step direct")
        print(f"Capture result path: {result_path}", flush=True)
        
        # Directly call the callback to verify it works
        print("Directly calling the callback...", flush=True)
        if controller.on_step_screenshot:
            controller.on_step_screenshot(1, "Direct callback test", step_path)
        else:
            print("Error: on_step_screenshot is not set", flush=True)
        
        # Wait a bit to see the output
        time.sleep(1)
        
        print("Test completed", flush=True)
    else:
        print("Failed to take screenshot", flush=True)
    
if __name__ == "__main__":
    main() 