import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageDraw
import base64
import io
import json
import time
import os
import re
from typing import Dict, List, Tuple, Optional
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import openai

class AIVisionController:
    def __init__(self):
        self.setup_pyautogui()
        self.ui_elements = {}
        self.action_history = []
        self.confidence_threshold = 0.8
        self.workflows = {}  # Store automation workflows
        self.api_key = None  # OpenAI API key
        self.model = "gpt-3.5-turbo"  # Default model
        
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
            
    def find_ui_element_opencv(self, element_name: str) -> Optional[Tuple[int, int, int, int]]:
        """Alternative UI element finding using OpenCV"""
        if element_name not in self.ui_elements:
            return None
            
        # Take screenshot
        screenshot = self.take_screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Load template
        template = cv2.imread(self.ui_elements[element_name]['image_path'])
        if template is None:
            print(f"Could not load template for '{element_name}'")
            return None
            
        # Template matching
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.confidence_threshold:
            h, w = template.shape[:2]
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            return (top_left[0], top_left[1], w, h)
        else:
            return None
            
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
                                pyautogui.click(center_x, center_y)
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
                            pyautogui.click(target[0], target[1])
                            self.log_action(f"Clicked at coordinates {target}")
                        except Exception as e:
                            print(f"Error clicking at coordinates {target}: {str(e)}")
                else:
                    try:
                        pyautogui.click()
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
                            pyautogui.doubleClick(center_x, center_y)
                            self.log_action(f"Double-clicked on '{target}'")
                        else:
                            # Try to find by text
                            text_pos = self.find_text_on_screen(target)
                            if text_pos:
                                pyautogui.doubleClick(text_pos[0], text_pos[1])
                                self.log_action(f"Double-clicked on text '{target}'")
                            else:
                                print(f"Could not find UI element or text: {target}")
                    except Exception as e:
                        print(f"Error double-clicking on element '{target}': {str(e)}")
                elif target and isinstance(target, tuple):
                    try:
                        pyautogui.doubleClick(target[0], target[1])
                        self.log_action(f"Double-clicked at {target}")
                    except Exception as e:
                        print(f"Error double-clicking at coordinates {target}: {str(e)}")
                        
            elif action_type == "right_click":
                if target and isinstance(target, str):
                    location = self.find_ui_element(target)
                    if location:
                        center_x = location[0] + location[2] // 2
                        center_y = location[1] + location[3] // 2
                        pyautogui.rightClick(center_x, center_y)
                        self.log_action(f"Right-clicked on '{target}'")
                        
            elif action_type == "type":
                if text:
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
                        pyautogui.scroll(clicks, x=center_x, y=center_y)
                        self.log_action(f"Scrolled {clicks} clicks at '{target}'")
                else:
                    pyautogui.scroll(clicks)
                    self.log_action(f"Scrolled {clicks} clicks")
                    
            elif action_type == "drag":
                start = kwargs.get('start')
                end = kwargs.get('end')
                if start and end:
                    pyautogui.dragTo(end[0], end[1], duration=0.5)
                    self.log_action(f"Dragged from {start} to {end}")
                    
            elif action_type == "wait":
                duration = kwargs.get('duration', 1)
                time.sleep(duration)
                self.log_action(f"Waited {duration} seconds")
                
        except Exception as e:
            print(f"Error performing action '{action_type}': {str(e)}")
            import traceback
            traceback.print_exc()  # Print detailed error information
            
    def log_action(self, action: str):
        """Log performed actions"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.action_history.append(f"[{timestamp}] {action}")
        print(f"Action: {action}")
        
    def parse_natural_language_command(self, command: str) -> List[Dict]:
        """Parse natural language commands into actionable instructions"""
        actions = []
        command = command.lower().strip()
        
        # Define command patterns with enhanced coverage
        patterns = {
            # Basic UI interactions
            r'click (?:on )?(.+?)(?:\s|$)': {'action': 'click', 'target': 'group1'},
            r'double.?click (?:on )?(.+?)(?:\s|$)': {'action': 'double_click', 'target': 'group1'},
            r'right.?click (?:on )?(.+?)(?:\s|$)': {'action': 'right_click', 'target': 'group1'},
            
            # Text entry
            r'type "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'type \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            r'enter "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'enter \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            r'input "([^"]+)"': {'action': 'type', 'text': 'group1'},
            r'input \'([^\']+)\'': {'action': 'type', 'text': 'group1'},
            
            # Key actions
            r'press ([a-zA-Z0-9_+^]+)': {'action': 'key_press', 'text': 'group1'},
            r'key ([a-zA-Z0-9_+^]+)': {'action': 'key_press', 'text': 'group1'},
            r'hotkey ([a-zA-Z0-9_+^]+(?:\+[a-zA-Z0-9_+^]+)+)': {'action': 'hotkey', 'text': 'group1'},
            r'shortcut ([a-zA-Z0-9_+^]+(?:\+[a-zA-Z0-9_+^]+)+)': {'action': 'hotkey', 'text': 'group1'},
            
            # Navigation
            r'scroll (up|down)(?: (\d+))?': {'action': 'scroll', 'direction': 'group1', 'amount': 'group2'},
            r'drag from (.+?) to (.+)': {'action': 'drag', 'start': 'group1', 'end': 'group2'},
            r'move (to|mouse) (.+?)(?:\s|$)': {'action': 'move', 'target': 'group2'},
            
            # Waiting and timing
            r'wait (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            r'pause (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            r'sleep (\d+\.?\d*)(?:\s?s(?:ec(?:ond)?s?)?)?': {'action': 'wait', 'duration': 'group1'},
            
            # Application control
            r'open (.+)': {'action': 'open', 'target': 'group1'},
            r'close (.+)': {'action': 'close', 'target': 'group1'},
            r'maximize (.+)': {'action': 'maximize', 'target': 'group1'},
            r'minimize (.+)': {'action': 'minimize', 'target': 'group1'},
            
            # Screenshot and OCR
            r'screenshot(?: of)? (.+?)(?:\s|$)': {'action': 'screenshot', 'target': 'group1'},
            r'capture(?: of)? (.+?)(?:\s|$)': {'action': 'screenshot', 'target': 'group1'},
            r'read text(?: from)? (.+?)(?:\s|$)': {'action': 'read_text', 'target': 'group1'},
            r'ocr(?: on)? (.+?)(?:\s|$)': {'action': 'read_text', 'target': 'group1'},
        }
        
        # Check for command patterns
        for pattern, action_info in patterns.items():
            match = re.search(pattern, command)
            if match:
                action = action_info.copy()
                
                # Replace group references with actual matched text
                for key, value in list(action.items()):
                    if isinstance(value, str) and value.startswith('group'):
                        group_num = int(value.replace('group', ''))
                        try:
                            if group_num <= len(match.groups()) and match.group(group_num) is not None:
                                action[key] = match.group(group_num)
                            else:
                                # Remove the key if the group wasn't matched
                                del action[key]
                        except IndexError:
                            # Group doesn't exist in the match, remove it from action
                            del action[key]
                
                # Handle special cases
                if action.get('action') == 'scroll':
                    direction = action.get('direction', 'down')
                    amount = action.get('amount')
                    if amount:
                        try:
                            amount = int(amount)
                        except ValueError:
                            amount = 3
                    else:
                        amount = 3
                    
                    action['clicks'] = amount if direction == 'up' else -amount
                    # Clean up temporary keys
                    if 'direction' in action:
                        del action['direction']
                    if 'amount' in action:
                        del action['amount']
                
                # Handle wait durations to convert to float
                if action.get('action') == 'wait' and 'duration' in action:
                    try:
                        action['duration'] = float(action['duration'])
                    except ValueError:
                        action['duration'] = 1.0
                
                # Handle new action types
                if action.get('action') == 'open':
                    # Convert to a sequence of actions for opening applications
                    action = {'action': 'hotkey', 'text': 'win+r', 'follow_up': 'type', 'follow_text': action.get('target', '')}
                
                actions.append(action)
                
                # Check for follow-up actions
                if 'follow_up' in action:
                    follow_action = {'action': action.get('follow_up')}
                    if 'follow_text' in action:
                        follow_action['text'] = action.get('follow_text')
                    actions.append(follow_action)
                break
        
        # If no pattern matched, look for generic actions
        if not actions:
            # Check for composite commands (multiple actions in one command)
            composite_patterns = [
                r'first (.+?) then (.+)',
                r'(.+?) and then (.+)',
                r'(.+?) followed by (.+)',
                r'(.+?),? then (.+)',
            ]
            
            for pattern in composite_patterns:
                match = re.search(pattern, command)
                if match:
                    first_command = match.group(1)
                    second_command = match.group(2)
                    
                    # Recursively parse each part
                    first_actions = self.parse_natural_language_command(first_command)
                    second_actions = self.parse_natural_language_command(second_command)
                    
                    actions = first_actions + second_actions
                    break
        
        return actions
        
    def execute_command_sequence(self, commands: List[str]):
        """Execute a sequence of commands"""
        for command in commands:
            print(f"Executing: {command}")
            actions = self.parse_natural_language_command(command)
            
            for action in actions:
                action_type = action.get('action', '')  # Default to empty string if not found
                target = action.get('target')
                text = action.get('text')
                
                # Convert target to actual UI element if it exists
                if target and target in self.ui_elements:
                    self.perform_action(action_type, target=target, text=text, **action)
                else:
                    self.perform_action(action_type, target=target, text=text, **action)
                    
                time.sleep(0.5)  # Small delay between actions
                
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
        
    def get_screen_text_ocr(self, region=None) -> str:
        """Extract text from screen using OCR (requires pytesseract)"""
        try:
            import pytesseract
            from PIL import Image
            
            screenshot = self.take_screenshot(region=region)
            
            # Preprocess the image for better OCR results
            # Convert to grayscale
            grayscale = screenshot.convert('L')
            
            # Apply threshold to make text more visible
            threshold = 150
            processed_image = grayscale.point(lambda x: 0 if x < threshold else 255)
            
            # Optional: Resize for better OCR (can help with small text)
            # scale = 2.0
            # width, height = processed_image.size
            # processed_image = processed_image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
            
            # Perform OCR
            config = '--psm 6'  # Assume a single block of text
            text = pytesseract.image_to_string(processed_image, config=config)
            
            return text.strip()
        except ImportError:
            print("pytesseract not installed. Install with: pip install pytesseract")
            print("You also need to install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
            return ""
        except Exception as e:
            print(f"OCR error: {str(e)}")
            return ""
            
    def find_text_on_screen(self, text: str, region=None) -> Optional[Tuple[int, int]]:
        """Find text on screen and return its location using OCR"""
        try:
            import pytesseract
            import cv2
            
            screenshot = self.take_screenshot(region=region)
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to make text more visible
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Use pytesseract to get word boxes
            custom_config = r'--oem 3 --psm 11'
            data = pytesseract.image_to_data(binary, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Search for the target text
            target_text = text.lower()
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                word = data['text'][i].lower().strip()
                
                # Check if this word matches or contains the target text
                if word and (word == target_text or target_text in word):
                    # Get box coordinates
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    # Calculate center of the word
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # If region was provided, adjust coordinates
                    if region:
                        center_x += region[0]
                        center_y += region[1]
                        
                    print(f"Found text '{text}' at ({center_x}, {center_y})")
                    return (center_x, center_y)
                    
                # Also check for consecutive words that form the target
                if i < n_boxes - 1:
                    two_words = f"{word} {data['text'][i+1].lower().strip()}"
                    if two_words == target_text or target_text in two_words:
                        # Calculate center between two words
                        x1 = data['left'][i]
                        x2 = data['left'][i+1] + data['width'][i+1]
                        y1 = data['top'][i] + data['height'][i] // 2
                        y2 = data['top'][i+1] + data['height'][i+1] // 2
                        
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        # If region was provided, adjust coordinates
                        if region:
                            center_x += region[0]
                            center_y += region[1]
                            
                        print(f"Found text '{text}' at ({center_x}, {center_y})")
                        return (center_x, center_y)
                        
            # If text is not found directly, check for partial matches
            best_match = None
            best_ratio = 0
            
            for i in range(n_boxes):
                word = data['text'][i].lower().strip()
                if len(word) >= 3:  # Ignore very short words
                    # Calculate similarity ratio
                    import difflib
                    ratio = difflib.SequenceMatcher(None, word, target_text).ratio()
                    
                    if ratio > 0.7 and ratio > best_ratio:  # At least 70% similar
                        best_match = i
                        best_ratio = ratio
            
            if best_match is not None:
                x = data['left'][best_match]
                y = data['top'][best_match]
                w = data['width'][best_match]
                h = data['height'][best_match]
                
                center_x = x + w // 2
                center_y = y + h // 2
                
                # If region was provided, adjust coordinates
                if region:
                    center_x += region[0]
                    center_y += region[1]
                    
                print(f"Found closest match for '{text}' at ({center_x}, {center_y}) with {best_ratio:.2f} confidence")
                return (center_x, center_y)
            
            print(f"Text '{text}' not found on screen")
            return None
            
        except ImportError:
            print("Required libraries not installed. Install with: pip install pytesseract opencv-python")
            return None
        except Exception as e:
            print(f"Error finding text: {str(e)}")
            return None
            
    def click_on_text(self, text: str, region=None) -> bool:
        """Find and click on text visible on screen"""
        text_pos = self.find_text_on_screen(text, region)
        if text_pos:
            pyautogui.click(text_pos[0], text_pos[1])
            self.log_action(f"Clicked on text '{text}' at {text_pos}")
            return True
        else:
            print(f"Could not find text '{text}' to click on")
            return False
        
    def create_workflow(self, name: str, commands: List[str]) -> bool:
        """Create a new automation workflow with a sequence of commands"""
        if name in self.workflows:
            print(f"Workflow '{name}' already exists. Use update_workflow to modify.")
            return False
            
        self.workflows[name] = {
            'commands': commands,
            'created': time.strftime("%Y-%m-%d %H:%M:%S"),
            'last_run': None
        }
        
        print(f"Created workflow '{name}' with {len(commands)} commands")
        return True
        
    def update_workflow(self, name: str, commands: List[str]) -> bool:
        """Update an existing workflow"""
        if name not in self.workflows:
            print(f"Workflow '{name}' does not exist")
            return False
            
        self.workflows[name]['commands'] = commands
        self.workflows[name]['last_modified'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Updated workflow '{name}'")
        return True
        
    def delete_workflow(self, name: str) -> bool:
        """Delete a workflow"""
        if name in self.workflows:
            del self.workflows[name]
            print(f"Deleted workflow '{name}'")
            return True
        else:
            print(f"Workflow '{name}' not found")
            return False
            
    def run_workflow(self, name: str) -> bool:
        """Run a saved workflow by name"""
        if name not in self.workflows:
            print(f"Workflow '{name}' not found")
            return False
            
        workflow = self.workflows[name]
        commands = workflow['commands']
        
        print(f"Running workflow '{name}' with {len(commands)} commands")
        
        # Update last run time
        self.workflows[name]['last_run'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.execute_command_sequence(commands)
            print(f"Workflow '{name}' completed successfully")
            return True
        except Exception as e:
            print(f"Error running workflow '{name}': {str(e)}")
            return False
            
    def save_all_data(self, filename: str):
        """Save UI elements and workflows configuration"""
        config = {
            'ui_elements': self.ui_elements,
            'workflows': self.workflows,
            'screen_size': (self.screen_width, self.screen_height),
            'confidence_threshold': self.confidence_threshold
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"All data saved to {filename}")
        
    def load_all_data(self, filename: str):
        """Load UI elements and workflows configuration"""
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
                
            self.ui_elements = config.get('ui_elements', {})
            self.workflows = config.get('workflows', {})
            self.confidence_threshold = config.get('confidence_threshold', 0.8)
            
            print(f"Data loaded from {filename}")
            print(f"Loaded {len(self.ui_elements)} UI elements and {len(self.workflows)} workflows")
            
        except FileNotFoundError:
            print(f"Configuration file not found: {filename}")
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")

    def set_openai_key(self, api_key: str):
        """Set OpenAI API key for GPT integration"""
        self.api_key = api_key
        openai.api_key = api_key
        print("OpenAI API key set")
        
    def process_prompt(self, prompt: str) -> List[str]:
        """Process natural language prompt using GPT to generate automation commands"""
        if not self.api_key:
            print("OpenAI API key not set. Use set_openai_key() first.")
            return []
            
        try:
            print(f"Processing prompt: {prompt}")
            
            # Create system message with command reference
            system_message = """
            You are an automation assistant that converts natural language instructions into specific commands
            for a PC automation tool. Output ONLY the commands, one per line, without explanations.
            
            Available commands:
            - click on [element_name]
            - double-click on [element_name]
            - right-click on [element_name]
            - type "[text]"
            - press [key_name]
            - hotkey [key1+key2]
            - wait [seconds] seconds
            - scroll up/down [number]
            - open [application_name]
            
            Example 1:
            User: Open Chrome, navigate to Gmail, and check my inbox
            Output:
            open chrome
            wait 3 seconds
            type "gmail.com"
            press enter
            wait 5 seconds
            click on inbox
            
            Example 2:
            User: Create a new Word document and type Hello World
            Output:
            open word
            wait 3 seconds
            type "Hello World"
            """
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            # Extract and parse the response
            command_text = response.choices[0].message.content.strip()
            commands = [cmd.strip() for cmd in command_text.split('\n') if cmd.strip()]
            
            print(f"Generated {len(commands)} commands")
            return commands
            
        except Exception as e:
            print(f"Error processing prompt: {str(e)}")
            return []
            
    def execute_prompt(self, prompt: str):
        """Process a natural language prompt and execute the resulting commands"""
        commands = self.process_prompt(prompt)
        if commands:
            print("Executing commands generated from prompt:")
            for cmd in commands:
                print(f"  - {cmd}")
                
            self.execute_command_sequence(commands)
            return True
        else:
            print("No commands were generated from the prompt")
            return False
            
    def process_prompt_with_vision(self, prompt: str, screenshot_path: str = None) -> List[str]:
        """Process natural language prompt with a screenshot for context using GPT-4 Vision"""
        if not self.api_key:
            print("OpenAI API key not set. Use set_openai_key() first.")
            return []
            
        try:
            print(f"Processing vision prompt: {prompt}")
            
            # Take screenshot if not provided
            if not screenshot_path:
                screenshot = self.take_screenshot()
                screenshot_path = f"screenshot_prompt_{int(time.time())}.png"
                screenshot.save(screenshot_path)
                print(f"Saved screenshot to {screenshot_path}")
                
            # Encode image to base64
            with open(screenshot_path, "rb") as image_file:
                import base64
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            # System message with command reference
            system_message = """
            You are an automation assistant that analyzes screenshots and converts natural language instructions 
            into specific commands for a PC automation tool. Look at the screenshot and generate the appropriate
            commands to accomplish the user's goal. Output ONLY the commands, one per line, without explanations.
            
            Available commands:
            - click on [x,y] coordinates
            - type "[text]"
            - press [key_name]
            - hotkey [key1+key2]
            - wait [seconds] seconds
            - scroll up/down [number]
            """
            
            # Call OpenAI API with Vision support
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",  # Vision-capable model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            # Extract and parse the response
            command_text = response.choices[0].message.content.strip()
            commands = [cmd.strip() for cmd in command_text.split('\n') if cmd.strip()]
            
            print(f"Generated {len(commands)} commands with vision context")
            return commands
            
        except Exception as e:
            print(f"Error processing vision prompt: {str(e)}")
            return []

class AIControllerGUI:
    def __init__(self):
        self.controller = AIVisionController()
        self.root = tk.Tk()
        self.root.title("AI PC Controller")
        self.root.geometry("800x600")
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        commands_tab = ttk.Frame(notebook)
        ui_elements_tab = ttk.Frame(notebook)
        workflows_tab = ttk.Frame(notebook)
        prompt_tab = ttk.Frame(notebook)  # New prompt tab
        
        notebook.add(commands_tab, text="Commands")
        notebook.add(ui_elements_tab, text="UI Elements")
        notebook.add(workflows_tab, text="Workflows")
        notebook.add(prompt_tab, text="GPT Prompt")
        
        # Setup each tab
        self.setup_commands_tab(commands_tab)
        self.setup_ui_elements_tab(ui_elements_tab)
        self.setup_workflows_tab(workflows_tab)
        self.setup_prompt_tab(prompt_tab)  # Setup the new tab
        
    def setup_commands_tab(self, parent):
        """Setup the commands tab interface"""
        # Main frame
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Command input
        ttk.Label(main_frame, text="Enter Command:").pack(anchor=tk.W, pady=5)
        self.command_entry = ttk.Entry(main_frame, width=50)
        self.command_entry.pack(fill=tk.X, pady=5)
        
        ttk.Button(main_frame, text="Execute", command=self.execute_command).pack(anchor=tk.W, pady=5)
        
        # Action history
        ttk.Label(main_frame, text="Action History:").pack(anchor=tk.W, pady=5)
        
        history_frame = ttk.Frame(main_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.history_text = tk.Text(history_frame, height=10, width=70)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for history
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="Take Screenshot", command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
    def setup_ui_elements_tab(self, parent):
        """Setup the UI elements tab interface"""
        # Main frame
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # UI Elements list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="UI Elements:").pack(anchor=tk.W, pady=5)
        
        # UI Elements listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.ui_listbox = tk.Listbox(list_container, height=15)
        self.ui_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.ui_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ui_listbox.configure(yscrollcommand=scrollbar.set)
        
        # UI Element details frame
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(details_frame, text="Element Details:").pack(anchor=tk.W, pady=5)
        
        # Details text area
        self.element_details = tk.Text(details_frame, height=10, width=40)
        self.element_details.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Add Element", command=self.add_ui_element).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Element", command=self.test_ui_element).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Element", command=self.remove_ui_element).pack(side=tk.LEFT, padx=5)
        
        # Bind selection event
        self.ui_listbox.bind("<<ListboxSelect>>", self.show_element_details)
        
    def setup_workflows_tab(self, parent):
        """Setup the workflows tab interface"""
        # Main frame
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Split into two sections
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Workflow list section
        ttk.Label(left_frame, text="Workflows:").pack(anchor=tk.W, pady=5)
        
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.workflow_listbox = tk.Listbox(list_container, height=15)
        self.workflow_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.workflow_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.workflow_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Workflow action buttons
        action_frame = ttk.Frame(left_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="New", command=self.new_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Run", command=self.run_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_workflow).pack(side=tk.LEFT, padx=5)
        
        # Workflow editor section
        ttk.Label(right_frame, text="Workflow Commands:").pack(anchor=tk.W, pady=5)
        
        self.workflow_name = ttk.Entry(right_frame)
        self.workflow_name.pack(fill=tk.X, pady=5)
        
        editor_container = ttk.Frame(right_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        self.workflow_editor = tk.Text(editor_container, height=15)
        self.workflow_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(editor_container, orient=tk.VERTICAL, command=self.workflow_editor.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.workflow_editor.configure(yscrollcommand=scrollbar.set)
        
        # Editor buttons
        editor_buttons = ttk.Frame(right_frame)
        editor_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(editor_buttons, text="Save", command=self.save_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(editor_buttons, text="Test", command=self.test_workflow).pack(side=tk.LEFT, padx=5)
        ttk.Button(editor_buttons, text="Record", command=self.start_recording).pack(side=tk.LEFT, padx=5)
        
        # Bind selection event
        self.workflow_listbox.bind("<<ListboxSelect>>", self.load_workflow_to_editor)
        
        # Initialize workflow display
        self.update_workflow_list()
        
    def setup_prompt_tab(self, parent):
        """Setup the GPT prompt interface tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API key section
        api_frame = ttk.LabelFrame(main_frame, text="OpenAI API Settings")
        api_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.api_key_entry = ttk.Entry(api_frame, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        
        ttk.Button(api_frame, text="Save Key", 
                  command=self.save_api_key).grid(row=0, column=2, padx=5, pady=5)
                  
        ttk.Label(api_frame, text="Model:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.model_combo = ttk.Combobox(api_frame, values=[
            "gpt-3.5-turbo", "gpt-4", "gpt-4-vision-preview"
        ])
        self.model_combo.current(0)
        self.model_combo.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        
        # Prompt input section
        prompt_frame = ttk.LabelFrame(main_frame, text="Natural Language Prompt")
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.prompt_text = tk.Text(prompt_frame, height=5)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        example_prompt = "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop"
        self.prompt_text.insert(tk.END, example_prompt)
        
        # Buttons
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Process Prompt", 
                  command=self.process_prompt).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="Execute Commands", 
                  command=self.execute_prompt_commands).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(button_frame, text="With Vision", 
                  command=self.process_with_vision).pack(side=tk.LEFT, padx=5)
        
        # Results section
        ttk.Label(main_frame, text="Generated Commands:").pack(anchor=tk.W, pady=5)
        
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_text = tk.Text(results_frame, height=10)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Store generated commands
        self.generated_commands = []
        
    def show_element_details(self, event):
        """Show details of the selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            element = self.controller.ui_elements.get(element_name)
            
            if element:
                self.element_details.delete(1.0, tk.END)
                details = f"Name: {element_name}\n"
                details += f"Image: {element['image_path']}\n"
                details += f"Action: {element.get('action_type', 'click')}\n"
                details += f"Last Found: {element.get('last_found', 'Never')}"
                
                self.element_details.insert(tk.END, details)
            
    def new_workflow(self):
        """Create a new workflow"""
        self.workflow_name.delete(0, tk.END)
        self.workflow_editor.delete(1.0, tk.END)
        self.workflow_name.insert(0, "new_workflow")
        
    def save_workflow(self):
        """Save the current workflow"""
        name = self.workflow_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Please provide a workflow name")
            return
            
        # Get commands (one per line)
        commands_text = self.workflow_editor.get(1.0, tk.END).strip()
        commands = [cmd.strip() for cmd in commands_text.split("\n") if cmd.strip()]
        
        if not commands:
            messagebox.showerror("Error", "Workflow is empty")
            return
            
        # Check if workflow exists
        if name in self.controller.workflows:
            self.controller.update_workflow(name, commands)
        else:
            self.controller.create_workflow(name, commands)
            
        self.update_workflow_list()
        messagebox.showinfo("Success", f"Workflow '{name}' saved")
        
    def load_workflow_to_editor(self, event):
        """Load the selected workflow into the editor"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            workflow = self.controller.workflows.get(workflow_name)
            
            if workflow:
                self.workflow_name.delete(0, tk.END)
                self.workflow_name.insert(0, workflow_name)
                
                self.workflow_editor.delete(1.0, tk.END)
                for cmd in workflow['commands']:
                    self.workflow_editor.insert(tk.END, cmd + "\n")
                    
    def run_workflow(self):
        """Run the selected workflow"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            
            if messagebox.askyesno("Confirm", f"Run workflow '{workflow_name}'?"):
                threading.Thread(target=self.controller.run_workflow, args=(workflow_name,)).start()
                self.update_workflow_list()
                
    def delete_workflow(self):
        """Delete the selected workflow"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            
            if messagebox.askyesno("Confirm", f"Delete workflow '{workflow_name}'?"):
                self.controller.delete_workflow(workflow_name)
                self.update_workflow_list()
                
                # Clear editor if the current workflow was deleted
                if self.workflow_name.get() == workflow_name:
                    self.workflow_name.delete(0, tk.END)
                    self.workflow_editor.delete(1.0, tk.END)
                    
    def test_workflow(self):
        """Test the current workflow in editor"""
        commands_text = self.workflow_editor.get(1.0, tk.END).strip()
        commands = [cmd.strip() for cmd in commands_text.split("\n") if cmd.strip()]
        
        if not commands:
            messagebox.showerror("Error", "No commands to test")
            return
            
        if messagebox.askyesno("Confirm", f"Test {len(commands)} commands?"):
            threading.Thread(target=self.controller.execute_command_sequence, args=(commands,)).start()
            
    def update_workflow_list(self):
        """Update the workflows listbox"""
        self.workflow_listbox.delete(0, tk.END)
        for workflow_name in sorted(self.controller.workflows.keys()):
            self.workflow_listbox.insert(tk.END, workflow_name)
            
    def start_recording(self):
        """Start recording user actions for a workflow"""
        # Clear previous recordings
        self.controller.action_history.clear()
        
        # Open recording dialog
        RecordingDialog(self.root, self.controller, self.workflow_editor)
        
    def execute_command(self):
        """Execute the command entered by user"""
        command = self.command_entry.get().strip()
        if command:
            try:
                threading.Thread(target=self.controller.execute_command_sequence, args=([command],)).start()
                self.update_history()
                self.command_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to execute command: {str(e)}")
                
    def add_ui_element(self):
        """Add a new UI element"""
        dialog = UIElementDialog(self.root, self.controller)
        if dialog.result:
            self.update_ui_list()
            
    def test_ui_element(self):
        """Test selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            location = self.controller.find_ui_element(element_name)
            if location:
                messagebox.showinfo("Success", f"Found '{element_name}' at {location}")
            else:
                messagebox.showwarning("Not Found", f"Could not find '{element_name}' on screen")
                
    def remove_ui_element(self):
        """Remove selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Remove UI element '{element_name}'?"):
                del self.controller.ui_elements[element_name]
                self.update_ui_list()
                
    def update_ui_list(self):
        """Update the UI elements listbox"""
        self.ui_listbox.delete(0, tk.END)
        for element_name in sorted(self.controller.ui_elements.keys()):
            self.ui_listbox.insert(tk.END, element_name)
            
    def update_history(self):
        """Update the action history display"""
        self.history_text.delete(1.0, tk.END)
        for action in self.controller.action_history[-20:]:  # Show last 20 actions
            self.history_text.insert(tk.END, action + "\n")
        self.history_text.see(tk.END)
        
    def clear_history(self):
        """Clear action history"""
        self.controller.action_history.clear()
        self.history_text.delete(1.0, tk.END)
        
    def take_screenshot(self):
        """Take and save screenshot"""
        screenshot = self.controller.take_screenshot()
        filename = f"screenshot_{int(time.time())}.png"
        screenshot.save(filename)
        messagebox.showinfo("Screenshot", f"Screenshot saved as {filename}")
        
    def save_config(self):
        """Save configuration"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.controller.save_all_data(filename)
            
    def load_config(self):
        """Load configuration"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.controller.load_all_data(filename)
            self.update_ui_list()
            self.update_workflow_list()
            
    def save_api_key(self):
        """Save OpenAI API key"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.controller.set_openai_key(api_key)
            self.controller.model = self.model_combo.get()
            messagebox.showinfo("Success", "API key saved and model selected")
        else:
            messagebox.showerror("Error", "Please enter an API key")
            
    def process_prompt(self):
        """Process natural language prompt to generate commands"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        
        if not prompt or prompt == "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop":
            messagebox.showerror("Error", "Please enter a prompt")
            return
            
        if not self.controller.api_key:
            messagebox.showerror("Error", "Please set your OpenAI API key first")
            return
            
        try:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Processing prompt...\n")
            self.root.update()
            
            commands = self.controller.process_prompt(prompt)
            self.generated_commands = commands
            
            self.results_text.delete(1.0, tk.END)
            if commands:
                for cmd in commands:
                    self.results_text.insert(tk.END, cmd + "\n")
            else:
                self.results_text.insert(tk.END, "No commands were generated")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error processing prompt: {str(e)}")
            
    def execute_prompt_commands(self):
        """Execute the commands generated from the prompt"""
        if not self.generated_commands:
            messagebox.showerror("Error", "No commands to execute. Process a prompt first.")
            return
            
        if messagebox.askyesno("Confirm", f"Execute {len(self.generated_commands)} commands?"):
            threading.Thread(target=self.controller.execute_command_sequence, 
                           args=(self.generated_commands,)).start()
            
    def process_with_vision(self):
        """Process prompt with screenshot context using GPT-4 Vision"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        
        if not prompt or prompt == "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop":
            messagebox.showerror("Error", "Please enter a prompt")
            return
            
        if not self.controller.api_key:
            messagebox.showerror("Error", "Please set your OpenAI API key first")
            return
            
        # Check if vision model is selected
        model = self.model_combo.get()
        if model != "gpt-4-vision-preview":
            if not messagebox.askyesno("Model Warning", 
                                     "Vision requires gpt-4-vision-preview model. Switch to it?"):
                return
            self.model_combo.set("gpt-4-vision-preview")
            self.controller.model = "gpt-4-vision-preview"
            
        try:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Taking screenshot and processing...\n")
            self.root.update()
            
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            screenshot_path = f"screenshot_prompt_{int(time.time())}.png"
            screenshot.save(screenshot_path)
            
            # Minimize window to avoid it being in the screenshot
            self.root.iconify()
            time.sleep(1)  # Wait for window to minimize
            
            commands = self.controller.process_prompt_with_vision(prompt, screenshot_path)
            self.generated_commands = commands
            
            # Restore window
            self.root.deiconify()
            
            self.results_text.delete(1.0, tk.END)
            if commands:
                for cmd in commands:
                    self.results_text.insert(tk.END, cmd + "\n")
            else:
                self.results_text.insert(tk.END, "No commands were generated")
                
        except Exception as e:
            # Restore window if error occurs
            self.root.deiconify()
            messagebox.showerror("Error", f"Error processing vision prompt: {str(e)}")
            
    def run(self):
        """Run the GUI application"""
        # Create menu
        self.create_menu()
        self.root.mainloop()
        
    def create_menu(self):
        """Create the application menu"""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Take Screenshot", command=self.take_screenshot)
        tools_menu.add_command(label="Clear History", command=self.clear_history)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Command Help", command=self.show_command_help)
        
        # Add menus to menu bar
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
        
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "AI PC Controller\n"
            "An automation tool for controlling your PC with AI vision\n\n"
            "Version 1.0"
        )
        
    def show_command_help(self):
        """Show command help dialog"""
        help_text = (
            "Command Examples:\n\n"
            "- click on <element_name>\n"
            "- double-click on <element_name>\n"
            "- right-click on <element_name>\n"
            "- type \"text to type\"\n"
            "- press enter\n"
            "- hotkey ctrl+c\n"
            "- wait 2 seconds\n"
            "- scroll up\n"
            "- scroll down 5\n"
            "- open notepad\n"
            "- click on button1 then type \"hello\"\n"
        )
        
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Command Help")
        help_dialog.geometry("500x400")
        
        text = tk.Text(help_dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text.insert(tk.END, help_text)
        text.configure(state=tk.DISABLED)
        
class RecordingDialog:
    """Dialog for recording automation steps"""
    def __init__(self, parent, controller, target_text):
        self.controller = controller
        self.target_text = target_text
        self.is_recording = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Record Actions")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        
        self.setup_dialog()
        self.start_recording()
        
    def setup_dialog(self):
        """Setup the dialog interface"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Recording started...", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10)
        
        # Instructions
        instructions = (
            "Perform the actions you want to record.\n"
            "All your actions will be tracked and added to the workflow.\n\n"
            "Click 'Stop Recording' when finished."
        )
        
        instruction_text = tk.Text(main_frame, height=5, wrap=tk.WORD)
        instruction_text.pack(fill=tk.X, pady=10)
        instruction_text.insert(tk.END, instructions)
        instruction_text.configure(state=tk.DISABLED)
        
        # Recorded actions
        ttk.Label(main_frame, text="Recorded Actions:").pack(anchor=tk.W, pady=5)
        
        self.actions_text = tk.Text(main_frame, height=5)
        self.actions_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.record_btn = ttk.Button(button_frame, text="Stop Recording", command=self.stop_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
    def start_recording(self):
        """Start recording user actions"""
        self.is_recording = True
        self.controller.action_history.clear()
        
        # Start action monitor in a thread
        self.monitor_thread = threading.Thread(target=self.monitor_actions)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_recording(self):
        """Stop recording and save actions"""
        self.is_recording = False
        
        # Extract commands from action history
        commands = []
        for action in self.controller.action_history:
            # Simple parsing - extract the action part after timestamp
            parts = action.split("] ", 1)
            if len(parts) > 1:
                action_text = parts[1]
                # Convert to command format
                if "Clicked on" in action_text:
                    element = action_text.split("'")[1]
                    commands.append(f"click on {element}")
                elif "Typed:" in action_text:
                    text = action_text.split("'")[1]
                    commands.append(f"type \"{text}\"")
                elif "Pressed key" in action_text:
                    key = action_text.split("'")[1]
                    commands.append(f"press {key}")
                elif "Waited" in action_text:
                    seconds = action_text.split(" ")[1]
                    commands.append(f"wait {seconds} seconds")
                    
        # Add commands to workflow editor
        if commands:
            current_text = self.target_text.get(1.0, tk.END).strip()
            if current_text:
                # Append to existing commands
                self.target_text.insert(tk.END, "\n")
            
            for cmd in commands:
                self.target_text.insert(tk.END, cmd + "\n")
        
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel recording"""
        self.is_recording = False
        self.dialog.destroy()
        
    def monitor_actions(self):
        """Monitor and display recorded actions"""
        last_count = 0
        
        while self.is_recording:
            current_count = len(self.controller.action_history)
            
            if current_count > last_count:
                # Update display with new actions
                self.actions_text.delete(1.0, tk.END)
                for action in self.controller.action_history[-5:]:  # Show last 5 actions
                    self.actions_text.insert(tk.END, action + "\n")
                self.actions_text.see(tk.END)
                
                last_count = current_count
                
            time.sleep(0.5)  # Check every half second

# Example usage and testing
if __name__ == "__main__":
    # Create the AI controller
    controller = AIVisionController()
    
    # Example: Add some UI elements programmatically
    # controller.save_ui_element("start_button", "ui_elements/start_button.png", "click")
    # controller.save_ui_element("text_field", "ui_elements/text_field.png", "click")
    
    # Example commands
    example_commands = [
        "click on start_button",
        "type \"Hello World\"",
        "press enter",
        "scroll down",
        "wait 2 seconds",
        "double click on text_field"
    ]
    
    print("AI PC Controller initialized!")
    print("\nExample commands:")
    for cmd in example_commands:
        print(f"  - {cmd}")
    
    # Launch GUI
    print("\nLaunching GUI...")
    app = AIControllerGUI()
    app.run()