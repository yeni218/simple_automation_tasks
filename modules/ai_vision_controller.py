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

class AIVisionController:
    def __init__(self):
        self.setup_pyautogui()
        self.ui_elements = {}
        self.action_history = []
        self.confidence_threshold = 0.8
        self.workflows = {}  # Store automation workflows
        self.api_key = None  # API key for AI models
        self.model = "phi-3-mini-4k-instruct"  # Default model
        self.api_endpoint = "http://localhost:1234/v1/chat/completions"  # Local API endpoint
        self.visual_feedback = True  # Enable visual feedback for automation
        self.move_duration = 0.5  # Duration of mouse movements (slower for visibility)
        
    def setup_pyautogui(self):
        """Configure PyAutoGUI settings"""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        self.screen_width, self.screen_height = pyautogui.size()
        
    def take_screenshot(self, region=None) -> Image.Image:
        """Take screenshot of screen or specific region"""
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        return screenshot
        
    def save_ui_element(self, name: str, image_path: str, action_type: str = "click"):
        """Save UI element reference for later recognition"""
        if os.path.exists(image_path):
            self.ui_elements[name] = {
                'image_path': image_path,
                'action_type': action_type,
                'last_found': None
            }
            print(f"UI element '{name}' saved successfully")
        else:
            print(f"Image file not found: {image_path}")
            
    def find_ui_element(self, element_name: str) -> Optional[Tuple[int, int, int, int]]:
        """Find UI element on screen using template matching"""
        if element_name not in self.ui_elements:
            print(f"UI element '{element_name}' not found in saved elements")
            return None
            
        element = self.ui_elements[element_name]
        try:
            # Use PyAutoGUI's built-in image recognition
            location = pyautogui.locateOnScreen(element['image_path'], confidence=self.confidence_threshold)
            if location:
                element['last_found'] = location
                return location
            else:
                print(f"Could not find '{element_name}' on screen")
                return None
        except pyautogui.ImageNotFoundException:
            print(f"Image not found for '{element_name}'")
            return None
            
    def move_with_visual_feedback(self, x, y):
        """Move mouse with visual feedback"""
        if self.visual_feedback:
            # Move with a slow duration for visibility
            pyautogui.moveTo(x, y, duration=self.move_duration)
        else:
            pyautogui.moveTo(x, y)
            
    def click_with_visual_feedback(self, x, y):
        """Click with visual feedback"""
        if self.visual_feedback:
            # Move visibly to position
            self.move_with_visual_feedback(x, y)
            # Draw a temporary circle around click location
            try:
                # Use a tiny screenshot for blinking effect
                orig_x, orig_y = pyautogui.position()
                pyautogui.moveTo(x, y)
                time.sleep(0.1)
                pyautogui.moveTo(x+10, y+10)
                time.sleep(0.1)
                pyautogui.moveTo(x-10, y-10)
                time.sleep(0.1)
                pyautogui.moveTo(x, y)
                # Then click
                pyautogui.click(x, y)
            except Exception as e:
                print(f"Visual feedback error: {e}")
                # Fall back to regular click
                pyautogui.click(x, y)
        else:
            pyautogui.click(x, y)

    def perform_action(self, action_type: str, target=None, text=None, **kwargs):
        """Perform various automation actions"""
        try:
            if not action_type:
                print("Warning: No action type specified")
                return
                
            if action_type == "click":
                if target:
                    if isinstance(target, str):  # UI element name
                        try:
                            location = self.find_ui_element(target)
                            if location:
                                center_x = location[0] + location[2] // 2
                                center_y = location[1] + location[3] // 2
                                self.click_with_visual_feedback(center_x, center_y)
                                self.log_action(f"Clicked on '{target}' at ({center_x}, {center_y})")
                            else:
                                # If UI element not found, try to find by text
                                if self.click_on_text(target):
                                    pass  # Successfully clicked by text
                                else:
                                    print(f"Could not find UI element or text: {target}")
                        except Exception as e:
                            print(f"Error clicking on element '{target}': {str(e)}")
                    elif isinstance(target, tuple):  # Coordinates
                        try:
                            self.click_with_visual_feedback(target[0], target[1])
                            self.log_action(f"Clicked at coordinates {target}")
                        except Exception as e:
                            print(f"Error clicking at coordinates {target}: {str(e)}")
                else:
                    try:
                        x, y = pyautogui.position()
                        self.click_with_visual_feedback(x, y)
                        self.log_action("Clicked at current mouse position")
                    except Exception as e:
                        print(f"Error clicking at current position: {str(e)}")
                    
            elif action_type == "double_click":
                if target and isinstance(target, str):
                    try:
                        location = self.find_ui_element(target)
                        if location:
                            center_x = location[0] + location[2] // 2
                            center_y = location[1] + location[3] // 2
                            self.move_with_visual_feedback(center_x, center_y)
                            pyautogui.doubleClick()
                            self.log_action(f"Double-clicked on '{target}'")
                        else:
                            # Try to find by text
                            text_pos = self.find_text_on_screen(target)
                            if text_pos:
                                self.move_with_visual_feedback(text_pos[0], text_pos[1])
                                pyautogui.doubleClick()
                                self.log_action(f"Double-clicked on text '{target}'")
                            else:
                                print(f"Could not find UI element or text: {target}")
                    except Exception as e:
                        print(f"Error double-clicking on element '{target}': {str(e)}")
                elif target and isinstance(target, tuple):
                    try:
                        self.move_with_visual_feedback(target[0], target[1])
                        pyautogui.doubleClick()
                        self.log_action(f"Double-clicked at {target}")
                    except Exception as e:
                        print(f"Error double-clicking at coordinates {target}: {str(e)}")
                    
            elif action_type == "right_click":
                if target and isinstance(target, str):
                    location = self.find_ui_element(target)
                    if location:
                        center_x = location[0] + location[2] // 2
                        center_y = location[1] + location[3] // 2
                        self.move_with_visual_feedback(center_x, center_y)
                        pyautogui.rightClick()
                        self.log_action(f"Right-clicked on '{target}'")
                    else:
                        print(f"Could not find UI element: {target}")
                        
            elif action_type == "type":
                if text:
                    # Add slight delay between characters for visibility
                    if self.visual_feedback:
                        for char in text:
                            pyautogui.typewrite(char)
                            time.sleep(0.05)  # Small delay between characters
                    else:
                        pyautogui.typewrite(text)
                    self.log_action(f"Typed: '{text}'")
                    
            elif action_type == "key_press":
                if text:
                    pyautogui.press(text)
                    self.log_action(f"Pressed key: '{text}'")
                    
            elif action_type == "hotkey":
                if text:
                    keys = text.split('+')
                    pyautogui.hotkey(*keys)
                    self.log_action(f"Pressed hotkey: '{text}'")
                    
            elif action_type == "scroll":
                clicks = kwargs.get('clicks', 3)
                if target and isinstance(target, str):
                    location = self.find_ui_element(target)
                    if location:
                        center_x = location[0] + location[2] // 2
                        center_y = location[1] + location[3] // 2
                        self.move_with_visual_feedback(center_x, center_y)
                        pyautogui.scroll(clicks)
                        self.log_action(f"Scrolled {clicks} clicks at '{target}'")
                else:
                    pyautogui.scroll(clicks)
                    self.log_action(f"Scrolled {clicks} clicks")
                    
            elif action_type == "drag":
                start = kwargs.get('start')
                end = kwargs.get('end')
                if start and end:
                    self.move_with_visual_feedback(start[0], start[1])
                    pyautogui.dragTo(end[0], end[1], duration=1.0 if self.visual_feedback else 0.5)
                    self.log_action(f"Dragged from {start} to {end}")
                    
            elif action_type == "wait":
                duration = kwargs.get('duration', 1)
                if isinstance(duration, str):
                    try:
                        duration = float(duration)
                    except ValueError:
                        duration = 1.0
                time.sleep(duration)
                self.log_action(f"Waited {duration} seconds")
                
            elif action_type == "move":
                if target and isinstance(target, tuple):
                    self.move_with_visual_feedback(target[0], target[1])
                    self.log_action(f"Moved to {target}")
                else:
                    print("Move action requires coordinates target")
            
            # Log errors for unsupported action types
            else:
                print(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            print(f"Error performing action '{action_type}': {str(e)}")
            import traceback
            traceback.print_exc()  # Print detailed error information
            
    def log_action(self, action: str):
        """Log performed actions"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.action_history.append(f"[{timestamp}] {action}")
        print(f"Action: {action}")
        
    def create_ui_element_from_screen(self, name: str, region: Tuple[int, int, int, int]):
        """Create UI element by capturing screen region"""
        screenshot = self.take_screenshot(region=region)
        
        # Create directory if it doesn't exist
        os.makedirs("ui_elements", exist_ok=True)
        
        # Save the image
        image_path = f"ui_elements/{name}.png"
        screenshot.save(image_path)
        
        # Add to UI elements
        self.save_ui_element(name, image_path)
        
        print(f"UI element '{name}' created and saved to {image_path}")

    def toggle_visual_feedback(self, enable=None):
        """Toggle visual feedback mode"""
        if enable is not None:
            self.visual_feedback = enable
        else:
            self.visual_feedback = not self.visual_feedback
        return self.visual_feedback 
        
    def save_all_data(self, filename: str):
        """Save all configuration data to a JSON file"""
        try:
            # Create data structure with all settings
            data = {
                'ui_elements': self.ui_elements,
                'workflows': self.workflows,
                'confidence_threshold': self.confidence_threshold,
                'api_key': self.api_key,
                'model': self.model,
                'api_endpoint': self.api_endpoint,
                'visual_feedback': self.visual_feedback,
                'move_duration': self.move_duration
            }
            
            # Convert any non-serializable data
            for element_name, element in data['ui_elements'].items():
                # Convert location tuples to lists if present
                if 'last_found' in element and element['last_found'] is not None:
                    if isinstance(element['last_found'], tuple):
                        element['last_found'] = list(element['last_found'])
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            print(f"Configuration saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def load_all_data(self, filename: str):
        """Load configuration data from a JSON file"""
        try:
            # Load from file
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Update controller attributes
            if 'ui_elements' in data:
                self.ui_elements = data['ui_elements']
                
                # Convert any lists back to tuples
                for element_name, element in self.ui_elements.items():
                    if 'last_found' in element and element['last_found'] is not None:
                        if isinstance(element['last_found'], list):
                            element['last_found'] = tuple(element['last_found'])
                
            if 'workflows' in data:
                self.workflows = data['workflows']
                
            if 'confidence_threshold' in data:
                self.confidence_threshold = data['confidence_threshold']
                
            if 'api_key' in data:
                self.api_key = data['api_key']
                
            if 'model' in data:
                self.model = data['model']
                
            if 'api_endpoint' in data:
                self.api_endpoint = data['api_endpoint']
                
            if 'visual_feedback' in data:
                self.visual_feedback = data['visual_feedback']
                
            if 'move_duration' in data:
                self.move_duration = data['move_duration']
                
            print(f"Configuration loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False 