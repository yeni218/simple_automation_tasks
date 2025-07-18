import pyautogui
import cv2
import numpy as np
from PIL import Image
import base64
import io
import json
import time
import os
import re
from typing import Dict, List, Tuple, Optional
import threading
import requests
import datetime

class AIVisionController:
    """Controller for AI vision-based automation"""
    
    def __init__(self):
        """Initialize the controller"""
        self.ui_elements = {}
        self.move_duration = 0.5  # Default move duration (seconds)
        self.visual_feedback = True  # Enable visual feedback by default
        self.api_endpoint = "http://localhost:5000/v1/chat/completions"  # Default API endpoint
        self.debug_mode = True  # Enable debug mode with screenshots
        self.screenshots_dir = "execution_logs"
        self.ai_manager = None  # AI manager reference for UI element detection
        self.on_step_screenshot = None  # Callback for UI update on screenshot
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Create a new session directory with timestamp
        self.session_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.screenshots_dir, f"session_{self.session_timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Step counter for this session
        self.step_counter = 0
        
    def take_screenshot(self, region=None):
        """Take a screenshot of the entire screen or a specific region"""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None
    
    def capture_step_screenshot(self, description=""):
        """Capture a screenshot for the current step"""
        if not self.debug_mode:
            return None
            
        try:
            # Increment step counter
            self.step_counter += 1
            
            # Take screenshot
            screenshot = self.take_screenshot()
            if not screenshot:
                return None
                
            # Generate filename with step number and timestamp
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            filename = f"step_{self.step_counter:03d}_{timestamp}.png"
            
            # If description provided, add it to the filename
            if description:
                # Clean description for filename (remove special chars)
                clean_desc = "".join(c for c in description if c.isalnum() or c == ' ')
                clean_desc = clean_desc.replace(' ', '_')[:30]  # Limit length
                filename = f"step_{self.step_counter:03d}_{timestamp}_{clean_desc}.png"
                
            # Save screenshot
            filepath = os.path.join(self.session_dir, filename)
            screenshot.save(filepath)
            
            # Create a log entry
            log_entry = f"Step {self.step_counter}: {description}\n"
            with open(os.path.join(self.session_dir, "execution_log.txt"), "a") as log_file:
                log_file.write(log_entry)
                
            # Notify UI to add step card if callback is set
            if hasattr(self, 'on_step_screenshot') and callable(self.on_step_screenshot):
                self.on_step_screenshot(self.step_counter, description, filepath)
                
            return filepath
        except Exception as e:
            print(f"Error capturing step screenshot: {str(e)}")
            return None
    
    def save_ui_element(self, name, image_path, action_type="click"):
        """Save a UI element"""
        self.ui_elements[name] = {
            "image_path": image_path,
            "action_type": action_type,
            "last_found": None
            }
        
        # Save the UI elements to a file for persistence
        self._save_ui_elements()
        
    def _save_ui_elements(self):
        """Save UI elements to a file"""
        # This is a placeholder - in a real implementation, this would
        # save the UI elements to a JSON file or database
        pass
            
    def find_ui_element(self, element_name, confidence=0.8):
        """Find a UI element on screen"""
        if element_name not in self.ui_elements:
            print(f"UI element '{element_name}' not found in saved elements")
            return None
            
        element = self.ui_elements[element_name]
        if not os.path.exists(element["image_path"]):
            print(f"Image file not found: {element['image_path']}")
            return None
            
        try:
            # Take a screenshot to search in
            self.capture_step_screenshot(f"Looking for UI element: {element_name}")
            
            # Find the element using pyautogui - confidence is a valid parameter for this function
            # but type checking may not recognize it correctly
            try:
                location = pyautogui.locateCenterOnScreen(  # type: ignore
                    element["image_path"], 
                    confidence=confidence
                )
            except TypeError:
                # Fallback if confidence parameter is not supported
                location = pyautogui.locateCenterOnScreen(element["image_path"])  # type: ignore
            
            # Update last found timestamp if found
            if location:
                import time
                self.ui_elements[element_name]["last_found"] = time.time()
                
                # Take a screenshot showing we found the element
                self.capture_step_screenshot(f"Found UI element: {element_name}")
                
                return location
        except Exception as e:
            print(f"Error finding UI element '{element_name}': {str(e)}")
            return None
            
    def perform_action(self, action_type, target=None, text=None, **kwargs):
        """Perform an action on screen"""
        try:
            # Capture screenshot before action
            description = f"Before {action_type} on {target}" if target else f"Before {action_type}"
            self.capture_step_screenshot(description)
                
            if action_type == "click":
                self._perform_click(target, **kwargs)
            elif action_type == "double_click":
                self._perform_double_click(target, **kwargs)
            elif action_type == "right_click":
                self._perform_right_click(target, **kwargs)
            elif action_type == "move":
                self._perform_move(target, **kwargs)
            elif action_type == "type":
                self._perform_type(text, **kwargs)
            elif action_type == "key_press":
                self._perform_key_press(text, **kwargs)
            elif action_type == "hotkey":
                self._perform_hotkey(text, **kwargs)
            elif action_type == "wait":
                self._perform_wait(**kwargs)
            elif action_type == "scroll":
                self._perform_scroll(**kwargs)
            else:
                print(f"Unknown action type: {action_type}")
                return False
                
            # Capture screenshot after action
            description = f"After {action_type} on {target}" if target else f"After {action_type}"
            self.capture_step_screenshot(description)
            
            return True
        except Exception as e:
            print(f"Error performing action {action_type}: {str(e)}")
            # Capture error screenshot
            self.capture_step_screenshot(f"ERROR: {action_type} failed - {str(e)}")
            return False
            
    def _perform_click(self, target, **kwargs):
        """Perform a click action"""
        if isinstance(target, tuple) and len(target) == 2:
            # Target is x, y coordinates
            x, y = target
            self._move_to_position(x, y)
            pyautogui.click(x=x, y=y)
        elif isinstance(target, str) and target in self.ui_elements:
            # Target is a UI element name
            location = self.find_ui_element(target)
            if location:
                x, y = location
                self._move_to_position(x, y)
                pyautogui.click(x=x, y=y)
            else:
                print(f"Could not find UI element: {target}")
                raise Exception(f"UI element not found: {target}")
        else:
            # Try to find target by OCR or other methods
            print(f"Target not understood: {target}")
            raise Exception(f"Unknown target: {target}")
    
    def _perform_double_click(self, target, **kwargs):
        """Perform a double click action"""
        if isinstance(target, tuple) and len(target) == 2:
            # Target is x, y coordinates
            x, y = target
            self._move_to_position(x, y)
            pyautogui.doubleClick(x=x, y=y)
        elif isinstance(target, str) and target in self.ui_elements:
            # Target is a UI element name
            location = self.find_ui_element(target)
            if location:
                x, y = location
                self._move_to_position(x, y)
                pyautogui.doubleClick(x=x, y=y)
            else:
                print(f"Could not find UI element: {target}")
                raise Exception(f"UI element not found: {target}")
        else:
            # Try to find target by OCR or other methods
            print(f"Target not understood: {target}")
            raise Exception(f"Unknown target: {target}")
    
    def _perform_right_click(self, target, **kwargs):
        """Perform a right click action"""
        if isinstance(target, tuple) and len(target) == 2:
            # Target is x, y coordinates
            x, y = target
            self._move_to_position(x, y)
            pyautogui.rightClick(x=x, y=y)
        elif isinstance(target, str) and target in self.ui_elements:
            # Target is a UI element name
            location = self.find_ui_element(target)
            if location:
                x, y = location
                self._move_to_position(x, y)
                pyautogui.rightClick(x=x, y=y)
            else:
                print(f"Could not find UI element: {target}")
                raise Exception(f"UI element not found: {target}")
                # Try to find target by OCR or other methods
        else:
            print(f"Target not understood: {target}")
            raise Exception(f"Unknown target: {target}")
    
    def _perform_move(self, target, **kwargs):
        """Perform a move action"""
        if isinstance(target, tuple) and len(target) == 2:
            # Target is x, y coordinates
            x, y = target
            self._move_to_position(x, y)
        elif isinstance(target, str) and target in self.ui_elements:
            # Target is a UI element name
            location = self.find_ui_element(target)
            if location:
                x, y = location
                self._move_to_position(x, y)
            else:
                print(f"Could not find UI element: {target}")
                raise Exception(f"UI element not found: {target}")
        else:
            # Try to find target by OCR or other methods
            print(f"Target not understood: {target}")
            raise Exception(f"Unknown target: {target}")
    
    def _perform_type(self, text, **kwargs):
        """Type text"""
        if not text:
            print("No text provided for typing")
            return
            
        pyautogui.typewrite(text, interval=0.05)
        
    def _perform_key_press(self, key, **kwargs):
        """Press a key"""
        if not key:
            print("No key provided")
            return
            
        pyautogui.press(key)
        
    def _perform_hotkey(self, keys, **kwargs):
        """Press a hotkey combination"""
        if not keys:
            print("No keys provided for hotkey")
            return
            
        # Split keys by + and press them as a hotkey
        key_list = keys.split('+')
        pyautogui.hotkey(*key_list)
        
    def _perform_wait(self, **kwargs):
        """Wait for a specified duration"""
        duration = kwargs.get('duration')
        if not duration:
            print("No duration provided for wait action")
            return
            
        try:
            # Convert to float if it's a string
            if isinstance(duration, str):
                duration = float(duration)
            time.sleep(duration)
        except ValueError:
            print(f"Invalid duration: {duration}")
            time.sleep(1.0)  # Default wait
            
    def _perform_scroll(self, **kwargs):
        """Perform a scroll action"""
        clicks = kwargs.get('clicks')
        if not clicks:
            print("No clicks amount provided for scroll action")
            return
            
        try:
            # Convert to int if it's a string
            if isinstance(clicks, str):
                clicks = int(clicks)
            pyautogui.scroll(clicks)
        except ValueError:
            print(f"Invalid clicks amount: {clicks}")
            
    def _move_to_position(self, x, y):
        """Move mouse to position with optional visual feedback"""
        if self.visual_feedback and self.move_duration > 0:
            # Visual feedback enabled - smooth movement
            pyautogui.moveTo(x, y, duration=self.move_duration)
        else:
            # No visual feedback - instant movement
            pyautogui.moveTo(x, y)

    def toggle_visual_feedback(self, enable=None):
        """Toggle visual feedback for mouse movements"""
        if enable is not None:
            self.visual_feedback = enable
        else:
            self.visual_feedback = not self.visual_feedback
        return self.visual_feedback 
        
    def set_move_duration(self, duration):
        """Set the duration for mouse movements"""
        try:
            self.move_duration = float(duration)
        except ValueError:
            print(f"Invalid duration: {duration}") 

    def execute_command_sequence(self, commands):
        """Execute a sequence of commands
        
        Args:
            commands: List of commands to execute
            
        Returns:
            str or bool: Path to session directory if successful, False otherwise
        """
        if not commands:
            print("No commands to execute")
            return False
            
        # List to store screenshots paths for reference
        screenshot_paths = []
        
        try:
            # Log execution
            print(f"Executing {len(commands)} commands...")
            
            # Iterate through commands
            for i, command in enumerate(commands):
                # Parse command
                if ':' not in command:
                    print(f"Invalid command format: {command}")
                    continue
                    
                cmd_type, cmd_value = command.split(':', 1)
                cmd_type = cmd_type.strip().lower()
                cmd_value = cmd_value.strip()
                
                print(f"Executing command {i+1}/{len(commands)}: {cmd_type} - {cmd_value}")
                
                # Execute command based on type
                if cmd_type == "click":
                    # Determine if the target is a UI element name, text description, or coordinates
                    if cmd_value.startswith('[') and cmd_value.endswith(']'):
                        # Coordinates, e.g. [100, 200]
                        try:
                            coords = eval(cmd_value)  # Safe for simple list evaluation
                            if isinstance(coords, list) and len(coords) == 2:
                                self.perform_action("click", target=tuple(coords))
                            else:
                                print(f"Invalid coordinates: {cmd_value}")
                        except Exception as e:
                            print(f"Error parsing coordinates: {str(e)}")
                    else:
                        # Text description or UI element name
                        if cmd_value in self.ui_elements:
                            # It's a known UI element
                            self.perform_action("click", target=cmd_value)
                        else:
                            # Try OCR-based click
                            success = self.click_on_text(cmd_value)
                            if not success:
                                print(f"Text not found: {cmd_value}")
                                # Capture failed attempt
                                self.capture_step_screenshot(f"ERROR: Text not found: {cmd_value}")
                                
                elif cmd_type == "type":
                    self.perform_action("type", text=cmd_value)
                    
                elif cmd_type == "wait":
                    try:
                        seconds = float(cmd_value)
                        self.perform_action("wait", duration=seconds)
                    except ValueError:
                        print(f"Invalid wait time: {cmd_value}")
                        
                elif cmd_type == "press":
                    self.perform_action("key_press", text=cmd_value)
                    
                else:
                    print(f"Unknown command type: {cmd_type}")
                    continue
                    
                # Take a screenshot after each action for AI analysis
                screenshot = self.take_screenshot()
                if screenshot:
                    # Save screenshot
                    timestamp = int(time.time())
                    filename = f"ai_analysis_{timestamp}.png"
                    filepath = os.path.join(self.session_dir, filename)
                    screenshot.save(filepath)
                    screenshot_paths.append(filepath)
                    
                    # Try to detect UI elements using AI if available
                    if self.ai_manager is not None:
                        try:
                            # Only do this if we've taken fewer than 10 screenshots to avoid API overuse
                            if len(screenshot_paths) % 3 == 0 and len(screenshot_paths) <= 9:  # Every 3rd action, up to 9 screenshots
                                # Check if the method exists
                                if callable(getattr(self.ai_manager, 'detect_ui_elements', None)):
                                    self.ai_manager.detect_ui_elements(filepath)
                                    # Optionally annotate the screenshot
                                    if callable(getattr(self.ai_manager, 'annotate_detected_ui_elements', None)):
                                        self.ai_manager.annotate_detected_ui_elements(filepath)
                        except Exception as e:
                            print(f"Error analyzing UI with AI: {str(e)}")
                
                # Wait between commands
                time.sleep(0.5)
                
            print(f"Command execution completed successfully")
            return self.session_dir
            
        except Exception as e:
            print(f"Error executing commands: {str(e)}")
            return False 

    def click_on_text(self, text, region=None):
        """Click on text found on screen using OCR (Base implementation)
        
        Args:
            text: Text to find and click on
            region: Region to search in (x, y, width, height)
            
        Returns:
            bool: True if found and clicked, False otherwise
        """
        print("Base click_on_text called - should be overridden by child class")
        return False
        
    def find_text_on_screen(self, text, region=None):
        """Find text on screen using OCR
        
        Args:
            text: Text to find
            region: Region to search in (x, y, width, height)
            
        Returns:
            tuple: (x, y) coordinates of the text or None if not found
        """
        # Capture a screenshot before searching
        self.capture_step_screenshot(f"Looking for text: {text}")
        
        # Try to use OCR to find the text
        screen_text = self.get_screen_text_ocr(region)
        
        # This is a simplified implementation - in a real application
        # you would want to do more sophisticated text matching and
        # get the actual position of the text from the OCR engine
        if text.lower() in screen_text.lower():
            # For now, just return the center of the region or screen
            if region:
                x = region[0] + region[2] // 2
                y = region[1] + region[3] // 2
            else:
                screen_width, screen_height = pyautogui.size()
                x = screen_width // 2
                y = screen_height // 2
            return x, y
        
        return None
        
    def get_screen_text_ocr(self, region=None):
        """Get text from screen using OCR
        
        Args:
            region: Region to get text from (x, y, width, height)
            
        Returns:
            str: Text found on screen or empty string if OCR failed
        """
        try:
            # Import pytesseract for OCR
            import pytesseract
            
            # Take a screenshot of the specified region or the entire screen
            screenshot = self.take_screenshot(region)
            
            if screenshot:
                # Use pytesseract to get text from the screenshot
                text = pytesseract.image_to_string(screenshot)
                return text
        except Exception as e:
            print(f"OCR error: {str(e)}")
        
        return "" 

class EnhancedAIVisionController(AIVisionController):
    """Enhanced controller with additional integration"""
    
    def __init__(self):
        """Initialize the enhanced controller"""
        super().__init__()
        
        # These will be set by the GUI
        self.ocr_utils = None
        self.command_parser = None
        self.workflow_manager = None
        self.ai_manager = None
        self.step_callback = None
        
    def set_step_callback(self, callback):
        """Set callback function for step updates
        
        Args:
            callback: Function to call with (step_number, description, image_path)
        """
        self.step_callback = callback
        self.on_step_screenshot = callback
        
    def toggle_visual_feedback(self, enable=None):
        """Toggle visual feedback mode"""
        if hasattr(self, 'visual_feedback'):
            return super().toggle_visual_feedback(enable)
        else:
            # Fallback for older versions
            return False
        
    def execute_command_sequence(self, commands):
        """Execute a sequence of commands with AI analysis at each step
        
        Args:
            commands: List of commands to execute
            
        Returns:
            str or bool: Path to session directory if successful, False otherwise
        """
        if not commands:
            print("No commands to execute")
            return False
            
        # List to store screenshots paths for reference
        screenshot_paths = []
        
        # Track overall success status
        overall_success = True
        
        try:
            # Log execution
            print(f"Executing {len(commands)} commands...")
            
            # Make sure step counter is reset
            self.step_counter = 0
            
            # Clear previous logs
            with open(os.path.join(self.session_dir, "execution_log.txt"), "w") as log_file:
                log_file.write(f"Starting execution at {datetime.datetime.now()}\n\n")
            
            # Take an initial screenshot to analyze the starting state
            initial_screenshot = self.capture_step_screenshot("Initial screen state")
            if initial_screenshot and self.ai_manager is not None:
                # Detect UI elements in the initial screenshot
                self.ai_manager.detect_ui_elements(initial_screenshot)
                # Annotate the screenshot
                if callable(getattr(self.ai_manager, 'annotate_detected_ui_elements', None)):
                    annotated_path = self.ai_manager.annotate_detected_ui_elements(initial_screenshot)
                    if annotated_path and hasattr(self, 'on_step_screenshot') and callable(self.on_step_screenshot):
                        self.on_step_screenshot(self.step_counter, "Initial screen analysis", annotated_path)
            
            # Iterate through commands
            for i, command in enumerate(commands):
                # Parse command
                if ':' not in command:
                    print(f"Invalid command format: {command}")
                    continue
                    
                cmd_type, cmd_value = command.split(':', 1)
                cmd_type = cmd_type.strip().lower()
                cmd_value = cmd_value.strip()
                
                print(f"Executing command {i+1}/{len(commands)}: {cmd_type} - {cmd_value}")
                
                # Take a screenshot before action
                before_screenshot = self.capture_step_screenshot(f"Before {cmd_type}: {cmd_value}")
                
                # Execute command based on type
                action_success = False
                
                if cmd_type == 'click':
                    # Determine if the target is a UI element name, text description, or coordinates
                    if cmd_value.startswith('[') and cmd_value.endswith(']'):
                        # Coordinates, e.g. [100, 200]
                        try:
                            coords = eval(cmd_value)  # Safe for simple list evaluation
                            if isinstance(coords, list) and len(coords) == 2:
                                self.perform_action("click", target=tuple(coords))
                                action_success = True
                            else:
                                print(f"Invalid coordinates: {cmd_value}")
                        except Exception as e:
                            print(f"Error parsing coordinates: {str(e)}")
                    else:
                        # Text description or UI element name
                        if cmd_value in self.ui_elements:
                            # It's a known UI element
                            self.perform_action("click", target=cmd_value)
                            action_success = True
                        else:
                            # Try OCR-based click
                            success = self.click_on_text(cmd_value)
                            if not success:
                                print(f"Text not found: {cmd_value}")
                                # Capture failed attempt
                                self.capture_step_screenshot(f"ERROR: Text not found: {cmd_value}")
                            else:
                                action_success = True
                                
                elif cmd_type == 'type':
                    self.perform_action("type", text=cmd_value)
                    action_success = True
                    
                elif cmd_type == 'wait':
                    try:
                        seconds = float(cmd_value)
                        self.perform_action("wait", duration=seconds)
                        action_success = True
                    except ValueError:
                        print(f"Invalid wait time: {cmd_value}")
                        
                elif cmd_type == 'press':
                    self.perform_action("key_press", text=cmd_value)
                    action_success = True
                    
                else:
                    print(f"Unknown command type: {cmd_type}")
                    continue
                
                # Always wait a bit after each action to let the UI update
                time.sleep(1.0)
                    
                # Take a screenshot after each action for AI analysis
                after_screenshot = self.capture_step_screenshot(f"After {cmd_type}: {cmd_value}")
                if after_screenshot:
                    screenshot_paths.append(after_screenshot)
                    
                    # Use AI to analyze the current step - ALWAYS do this for every step
                    if self.ai_manager is not None:
                        try:
                            # Create an action description for the analysis
                            action_desc = f"{cmd_type}: {cmd_value}"
                            
                            # First detect UI elements in the screenshot
                            ui_elements = self.ai_manager.detect_ui_elements(after_screenshot)
                            print(f"Detected {len(ui_elements) if ui_elements else 0} UI elements in screenshot")
                            
                            # Analyze this step with AI if the method exists
                            if callable(getattr(self.ai_manager, 'analyze_current_step', None)):
                                analysis = self.ai_manager.analyze_current_step(
                                    after_screenshot, 
                                    self.step_counter,
                                    action_desc
                                )
                                
                                # Log the analysis
                                if analysis:
                                    success_status = analysis.get('success')
                                    explanation = analysis.get('explanation', 'No explanation provided')
                                    next_suggestion = analysis.get('next_action_suggestion', '')
                                    
                                    print(f"Step {self.step_counter} analysis: Success={success_status}, {explanation}")
                                    
                                    # Write analysis to log file
                                    with open(os.path.join(self.session_dir, "execution_log.txt"), "a") as log_file:
                                        log_file.write(f"AI Analysis Step {self.step_counter}:\n")
                                        log_file.write(f"  Command: {action_desc}\n")
                                        log_file.write(f"  Success: {success_status}\n")
                                        log_file.write(f"  Explanation: {explanation}\n")
                                        if next_suggestion:
                                            log_file.write(f"  Next suggestion: {next_suggestion}\n")
                                        log_file.write("\n")
                                    
                                    # Update overall success status
                                    if success_status is False:  # Only update if explicitly False
                                        overall_success = False
                                        
                                    # Annotate the screenshot with analysis results
                                    annotated_path = self.ai_manager.annotate_detected_ui_elements(after_screenshot)
                                    
                                    # Update step card if callback is available
                                    if hasattr(self, 'on_step_screenshot') and callable(self.on_step_screenshot):
                                        # Add AI analysis to the description
                                        ai_desc = f"{action_desc} - {explanation}"
                                        # Use annotated image if available, otherwise use original
                                        image_to_use = annotated_path if annotated_path else after_screenshot
                                        self.on_step_screenshot(self.step_counter, ai_desc, image_to_use)
                            else:
                                print("Warning: analyze_current_step method not available in AI manager")
                                # Annotate the screenshot with detected UI elements
                                if callable(getattr(self.ai_manager, 'annotate_detected_ui_elements', None)):
                                    annotated_path = self.ai_manager.annotate_detected_ui_elements(after_screenshot)
                                    if annotated_path and hasattr(self, 'on_step_screenshot') and callable(self.on_step_screenshot):
                                        self.on_step_screenshot(self.step_counter, f"{cmd_type}: {cmd_value} - UI elements detected", annotated_path)
                        except Exception as e:
                            print(f"Error analyzing step with AI: {str(e)}")
                            import traceback
                            traceback.print_exc()
                else:
                    print("Warning: Failed to capture screenshot after action")
                
                # Wait between commands
                time.sleep(0.5)
                
            print(f"Command execution completed successfully")
            
            # Check if there was a failure detected by AI
            final_status = "✓ All steps completed successfully" if overall_success else "⚠️ Some steps had issues"
            print(final_status)
            
            # Write final status to log
            with open(os.path.join(self.session_dir, "execution_log.txt"), "a") as log_file:
                log_file.write(f"\nFinal Status: {final_status}\n")
            
            return self.session_dir
            
        except Exception as e:
            print(f"Error executing commands: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_on_text(self, text, region=None):
        """Click on text found on screen using OCR
        
        Args:
            text: Text to find and click on
            region: Region to search in (x, y, width, height)
            
        Returns:
            bool: True if found and clicked, False otherwise
        """
        location = self.find_text_on_screen(text, region)
        if location:
            x, y = location
            self.perform_action("click", target=(x, y))
            return True
        return False
        
    def find_text_on_screen(self, text, region=None):
        """Find text on screen using OCR
        
        Args:
            text: Text to find
            region: Region to search in (x, y, width, height)
            
        Returns:
            tuple: (x, y) coordinates of the text or None if not found
        """
        # Capture a screenshot before searching
        self.capture_step_screenshot(f"Looking for text: {text}")
        
        # Try to use OCR to find the text
        screen_text = self.get_screen_text_ocr(region)
        
        # This is a simplified implementation - in a real application
        # you would want to do more sophisticated text matching and
        # get the actual position of the text from the OCR engine
        if text.lower() in screen_text.lower():
            # For now, just return the center of the region or screen
            if region:
                x = region[0] + region[2] // 2
                y = region[1] + region[3] // 2
            else:
                screen_width, screen_height = pyautogui.size()
                x = screen_width // 2
                y = screen_height // 2
            return x, y
        
        return None
        
    def get_screen_text_ocr(self, region=None):
        """Get text from screen using OCR
        
        Args:
            region: Region to get text from (x, y, width, height)
            
        Returns:
            str: Text found on screen or empty string if OCR failed
        """
        try:
            # Import pytesseract for OCR
            import pytesseract
            
            # Take a screenshot of the specified region or the entire screen
            screenshot = self.take_screenshot(region)
            
            if screenshot:
                # Use pytesseract to get text from the screenshot
                text = pytesseract.image_to_string(screenshot)
                return text
        except Exception as e:
            print(f"OCR error: {str(e)}")
        
        return "" 

    def set_ai_manager(self, ai_manager):
        """Set the AI manager for this controller
        
        Args:
            ai_manager: The AI manager instance
        """
        self.ai_manager = ai_manager 