import requests
import json
import time
import base64
import re
from typing import List, Dict, Any, Optional
import traceback

class AIIntegration:
    def __init__(self, controller):
        """Initialize AI integration with reference to controller"""
        self.controller = controller
        self.api_endpoint = "http://localhost:1234/v1/chat/completions"  # Local model endpoint
        self.model = "qwen/qwen3-14b"  # Default model
        self.api_key = None  # Optional API key
        self.last_commands = []  # Store last generated commands for debugging
        
        # Valid command patterns - precise format
        self.valid_command_patterns = [
            r'^hotkey\s+[\w+]+$',                 # hotkey win+r
            r'^type\s+.+$',                       # type hello world
            r'^press\s+\w+$',                     # press enter
            r'^click\s+on\s+.+$',                 # click on start menu
            r'^click\s+at\s+\d+,\s*\d+$',         # click at 100,200
            r'^double-click\s+on\s+.+$',          # double-click on file
            r'^right-click\s+on\s+.+$',           # right-click on icon
            r'^wait\s+\d+(\.\d+)?\s+seconds?$',   # wait 2 seconds
            r'^scroll\s+up\s+\d+$',               # scroll up 3
            r'^scroll\s+down\s+\d+$',             # scroll down 2
            r'^move\s+to\s+\d+,\s*\d+$',          # move to 100,200
            r'^open\s+.+$'                        # open notepad
        ]
        
    def set_api_endpoint(self, endpoint: str):
        """Set the API endpoint for the model"""
        self.api_endpoint = endpoint
        print(f"AI API endpoint set to: {endpoint}")
        
    def set_model(self, model: str):
        """Set the model name to use"""
        self.model = model
        print(f"AI model set to: {model}")
        
    def set_api_key(self, api_key: str):
        """Set API key if needed"""
        self.api_key = api_key
        print("API key set")
    
    def extract_valid_commands(self, text: str) -> List[str]:
        """Extract only valid automation commands from text"""
        # Split text into lines and normalize
        lines = [line.strip().lower() for line in text.split('\n')]
        valid_commands = []
        
        # Process each line
        for line in lines:
            # Skip empty lines
            if not line:
                continue
                
            # Skip lines that start with markdown indicators or numbers
            if line.startswith(('- ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ', '0. ', '#', '>')):
                # Try to extract command from the line by removing the prefix
                clean_line = re.sub(r'^[-*\d.#>]+\s*', '', line).strip().lower()
                if clean_line:
                    line = clean_line
                    
            # Remove markdown formatting and quotes
            line = line.replace('**', '').replace('`', '').replace('"', '').replace("'", "")
            # Remove trailing periods and capitalization
            line = line.rstrip('.').lower()
            
            # Check if line is a valid command
            is_valid = False
            for pattern in self.valid_command_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_valid = True
                    break
                    
            # Handle special cases and fix common issues
            if not is_valid:
                # Fix click patterns like "click notepad" -> "click on notepad"
                if line.startswith('click ') and not line.startswith('click on ') and not line.startswith('click at '):
                    line = 'click on ' + line[6:]
                    is_valid = True
                # Fix double click patterns
                elif line.startswith('double click '):
                    line = 'double-click on ' + line[12:]
                    is_valid = True
                # Fix right click patterns
                elif line.startswith('right click '):
                    line = 'right-click on ' + line[12:]
                    is_valid = True
                # Fix "click button x" -> "click on button x"
                elif re.match(r'^click\s+\w+\s+.+$', line):
                    line = re.sub(r'^click\s+(\w+)\s+', r'click on ', line)
                    is_valid = True
            
            if is_valid:
                valid_commands.append(line)
        
        # If we couldn't extract any valid commands, use task detection to create appropriate commands
        if not valid_commands:
            # Detect common tasks from the text
            if "notepad" in text.lower():
                valid_commands = self.get_notepad_commands(text)
            elif "word" in text.lower() or "microsoft word" in text.lower() or "ms word" in text.lower():
                valid_commands = self.get_word_commands(text)
            elif "calculator" in text.lower():
                valid_commands = self.get_calculator_commands(text)
            elif "paint" in text.lower():
                valid_commands = self.get_paint_commands(text)
            elif "browser" in text.lower() or "chrome" in text.lower() or "firefox" in text.lower() or "edge" in text.lower():
                valid_commands = self.get_browser_commands(text)
            else:
                # Generic commands for unknown tasks
                valid_commands = [
                    "hotkey win+r",
                    "wait 1 seconds",
                    "press enter",
                    "wait 2 seconds"
                ]
        
        # Debug the commands
        print("Extracted commands:", valid_commands)
                
        return valid_commands
        
    def get_notepad_commands(self, text: str) -> List[str]:
        """Get predefined commands for Notepad tasks"""
        # Print debug info
        print("Generating notepad commands for:", text)
        
        commands = [
            "hotkey win+r",
            "type \"notepad\"",  # Make sure there's no colon
            "press enter",
            "wait 2 seconds"
        ]
        
        # Debug the commands
        print("Initial notepad commands:", commands)
        
        # Check if we need to type something
        if "write" in text.lower() or "type" in text.lower():
            text_to_type = "Hello, World!"
            if "hello world" in text.lower():
                text_to_type = "Hello, World!"
            commands.append(f"type \"{text_to_type}\"")
            
        # Check if we need to save
        if "save" in text.lower():
            commands.extend([
                "hotkey ctrl+s",
                "wait 1 seconds",
                "type \"document.txt\"",
                "press enter"
            ])
        
        # Debug the final commands
        print("Final notepad commands:", commands)
            
        return commands
        
    def get_word_commands(self, text: str) -> List[str]:
        """Get predefined commands for MS Word tasks"""
        commands = [
            "hotkey win+r",
            "type \"winword\"",
            "press enter",
            "wait 3 seconds"
        ]
        
        # Check if we need to type something
        if "write" in text.lower() or "type" in text.lower():
            text_to_type = "Hello, World!"
            if "hello world" in text.lower():
                text_to_type = "Hello, World!"
            commands.append(f"type \"{text_to_type}\"")
            
        # Check if we need to save
        if "save" in text.lower():
            commands.extend([
                "hotkey ctrl+s",
                "wait 1 seconds",
                "type \"document.docx\"",
                "press enter"
            ])
            
        return commands
        
    def get_calculator_commands(self, text: str) -> List[str]:
        """Get predefined commands for Calculator tasks"""
        commands = [
            "hotkey win+r",
            "type \"calc\"",
            "press enter",
            "wait 4 seconds"  # Increase wait time to ensure calculator opens
        ]
        
        # Check for common operations
        if "add" in text.lower() or "+" in text or "plus" in text.lower() or "sum" in text.lower():
            # Extract numbers if possible
            num1 = 5
            num2 = 3
            
            # Try to extract numbers from the text
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                num1 = numbers[0]
                num2 = numbers[1]
            
            commands.extend([
                f"press {num1}",
                "press +",
                f"press {num2}",
                "press ="
            ])
        elif "subtract" in text.lower() or "-" in text or "minus" in text.lower():
            commands.extend([
                "press 8",
                "press -",
                "press 3",
                "press ="
            ])
        elif "multiply" in text.lower() or "*" in text or "times" in text.lower():
            commands.extend([
                "press 4",
                "press *",
                "press 5",
                "press ="
            ])
        elif "divide" in text.lower() or "/" in text:
            commands.extend([
                "press 1",
                "press 0",
                "press /",
                "press 2",
                "press ="
            ])
            
        return commands
        
    def get_paint_commands(self, text: str) -> List[str]:
        """Get predefined commands for Paint tasks"""
        commands = [
            "hotkey win+r",
            "type \"mspaint\"",
            "press enter",
            "wait 2 seconds"
        ]
        
        # Check for common drawing operations
        if "rectangle" in text.lower():
            commands.extend([
                "press r",  # Rectangle tool shortcut in some versions
                "click on [200, 200]",
                "move to [400, 400]",
                "click on [400, 400]"
            ])
        elif "circle" in text.lower() or "ellipse" in text.lower():
            commands.extend([
                "press o",  # Ellipse tool shortcut in some versions
                "click on [200, 200]",
                "move to [300, 300]",
                "click on [300, 300]"
            ])
        elif "line" in text.lower():
            commands.extend([
                "press l",  # Line tool shortcut in some versions
                "click on [100, 100]",
                "move to [400, 400]",
                "click on [400, 400]"
            ])
            
        return commands
        
    def get_browser_commands(self, text: str) -> List[str]:
        """Get predefined commands for browser tasks"""
        browser = "chrome"
        if "firefox" in text.lower():
            browser = "firefox"
        elif "edge" in text.lower():
            browser = "msedge"
            
        commands = [
            "hotkey win+r",
            f"type \"{browser}\"",
            "press enter",
            "wait 3 seconds"
        ]
        
        # Check for common websites
        if "google" in text.lower():
            commands.append("type \"google.com\"")
            commands.append("press enter")
        elif "youtube" in text.lower():
            commands.append("type \"youtube.com\"")
            commands.append("press enter")
        elif "gmail" in text.lower():
            commands.append("type \"gmail.com\"")
            commands.append("press enter")
        elif "search" in text.lower():
            search_term = "automation with python"
            commands.append(f"type \"{search_term}\"")
            commands.append("press enter")
            
        return commands
        
    def process_prompt(self, prompt: str) -> List[str]:
        """Process natural language prompt to generate commands"""
        try:
            # Create system message with command reference
            system_message = """
            You are an automation assistant that converts natural language instructions into specific commands for a PC automation tool.
            
            Your task is to output ONLY the exact commands to execute, one per line, with NO explanations, 
            descriptions, markdown formatting, or commentary. Be extremely precise with your format.
            
            DO NOT include any explanations, headers, or descriptions in your response.
            DO NOT use markdown formatting like asterisks or backticks.
            DO NOT number your commands or add bullet points.
            DO NOT include any text that isn't a direct command.
            DO NOT use capital letters in commands - all commands must be lowercase.
            DO NOT include quotes or periods in your commands.
            
            IMPORTANT: ALWAYS use direct coordinates for clicking instead of trying to find UI elements by name.
            For example, use "click at 100,200" instead of "click on file".
            
            The EXACT FORMAT for commands (use precisely these formats with no variations):
            
            - click at [x],[y]          # Example: click at 100,200
            - double-click at [x],[y]   # Example: double-click at 100,200
            - right-click at [x],[y]    # Example: right-click at 100,200
            - type [text]               # Example: type hello world
            - press [key]               # Example: press enter
            - hotkey [key1+key2]        # Example: hotkey win+r
            - wait [number] seconds     # Example: wait 2 seconds
            - scroll up [number]        # Example: scroll up 3
            - scroll down [number]      # Example: scroll down 2
            - move to [x],[y]           # Example: move to 100,200
            
            Example:
            User: Open Notepad and type Hello World
            Output:
            hotkey win+r
            type notepad
            press enter
            wait 2 seconds
            type Hello World
            
            User: Open calculator and add 5 and 3
            Output:
            hotkey win+r
            type calc
            press enter
            wait 2 seconds
            click at 200,300
            wait 1 seconds
            click at 100,400
            wait 1 seconds
            click at 200,400
            wait 1 seconds
            click at 150,350
            """
            
            # Check if the prompt contains keywords for specific applications
            notepad_keywords = ["notepad", "text editor", "write text"]
            calculator_keywords = ["calculator", "calc", "compute", "add numbers"]
            
            if any(keyword in prompt.lower() for keyword in notepad_keywords):
                return self.get_direct_notepad_commands(prompt)
            elif any(keyword in prompt.lower() for keyword in calculator_keywords):
                return self.get_direct_calculator_commands(prompt)
            
            # Prepare request data for local model
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": -1,
                "stream": False
            }
            
            # Call the local API
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            command_text = result["choices"][0]["message"]["content"].strip()
            
            print("Raw API response:", command_text)
            
            # Extract valid commands from the response
            commands = self.extract_valid_commands(command_text)
            
            # Store the commands for debugging
            self.last_commands = commands.copy()
            
            print(f"Generated {len(commands)} commands")
            return commands
            
        except Exception as e:
            print(f"Error processing prompt: {str(e)}")
            traceback.print_exc()
            self.last_commands = []
            return []
    
    def get_direct_notepad_commands(self, text: str) -> List[str]:
        """Get predefined commands for Notepad tasks with direct coordinates"""
        print("Using direct coordinate commands for Notepad")
        
        # Base commands to open Notepad
        commands = [
            "hotkey win+r",
            "wait 1 seconds",
            "type notepad",
            "press enter",
            "wait 2 seconds"
        ]
        
        # Add typing command if needed
        if "type" in text.lower() or "write" in text.lower():
            # Extract text to type from the prompt
            type_text = "Hello World"
            if "type" in text.lower() and "'" in text:
                # Try to extract quoted text
                match = re.search(r"type\s+'([^']+)'", text, re.IGNORECASE) or re.search(r'type\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    type_text = match.group(1)
            commands.append(f"type {type_text}")
        
        # Add save commands if needed
        if "save" in text.lower():
            commands.extend([
                "wait 1 seconds",
                "hotkey alt+f",  # Open File menu
                "wait 1 seconds",
                "press s",       # Select Save
                "wait 1 seconds"
            ])
            
            # If saving with specific name
            if "as" in text.lower():
                filename = "document.txt"
                # Try to extract filename
                match = re.search(r"save\s+as\s+'([^']+)'", text, re.IGNORECASE) or re.search(r'save\s+as\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                elif "as" in text.lower() and "." in text:
                    # Try to find a word that looks like a filename
                    words = text.split()
                    for word in words:
                        if "." in word:
                            filename = word.strip(".,;:'\"")
                
                commands.append(f"type {filename}")
                commands.append("press enter")
            
        print(f"Generated {len(commands)} direct Notepad commands")
        return commands
        
    def get_direct_calculator_commands(self, text: str) -> List[str]:
        """Get predefined commands for Calculator tasks with direct coordinates"""
        print("Using direct coordinate commands for Calculator")
        
        # Base commands to open Calculator
        commands = [
            "hotkey win+r",
            "wait 1 seconds",
            "type calc",
            "press enter",
            "wait 2 seconds"
        ]
        
        # Map of calculator operations to keyboard commands
        calc_operations = {
            "+": "press +",
            "-": "press -",
            "*": "press *",
            "/": "press /",
            "=": "press ="
        }
        
        # Try to extract numbers and operations
        numbers = re.findall(r'\d+', text)
        operations = re.findall(r'[\+\-\*/=]', text)
        
        # If we have at least two numbers, simulate the calculation
        if len(numbers) >= 2:
            # First number
            commands.append(f"type {numbers[0]}")
            
            # Operation and second number
            if operations:
                op = operations[0]
                if op in calc_operations:
                    commands.append(calc_operations[op])
                    commands.append(f"type {numbers[1]}")
                    commands.append("press =")
            else:
                # Default to addition if no operation found
                commands.append("press +")
                commands.append(f"type {numbers[1]}")
                commands.append("press =")
        else:
            # If no specific calculation found, just open calculator
            pass
            
        print(f"Generated {len(commands)} direct Calculator commands")
        return commands
    
    def execute_ai_instructions(self, prompt: str) -> bool:
        """Execute natural language instructions using AI processing"""
        try:
            print(f"Processing prompt: {prompt}")
            
            # First try AI processing for all tasks
            try:
                # Always try the API first for any instruction
                commands = self.process_prompt(prompt)
                print("Successfully received commands from API")
            except requests.exceptions.ConnectionError:
                print("Error: Cannot connect to API endpoint. Is your local LLM server running at", self.api_endpoint, "?")
                commands = []
            except Exception as api_err:
                print(f"API error: {str(api_err)}")
                commands = []
            
            # If API failed or returned no commands, use fallbacks
            if not commands:
                print("API didn't return valid commands, using fallbacks")
                # Fallback to built-in patterns
                if "calculator" in prompt.lower():
                    commands = self.get_calculator_commands(prompt)
                elif "notepad" in prompt.lower():
                    commands = self.get_notepad_commands(prompt)
                elif "paint" in prompt.lower():
                    commands = self.get_paint_commands(prompt)
                elif "browser" in prompt.lower() or "chrome" in prompt.lower() or "edge" in prompt.lower():
                    commands = self.get_browser_commands(prompt)
                else:
                    # Very basic fallback commands
                    commands = [
                        "hotkey win+r",
                        f"type \"{prompt.split()[0]}\"",  # Use the first word as app name
                        "press enter",
                        "wait 3 seconds"
                    ]
                
            if not commands:
                print("No commands generated")
                return False
                
            # Log the commands to be executed
            print(f"Generated {len(commands)} commands")
            print("Executing " + str(len(commands)) + " commands:")
            for cmd in commands:
                print(f"  - {cmd}")
                
            # Execute commands with longer initial delay
            import time
            time.sleep(1.0)  # Small delay before starting
            
            # Execute the commands
            self.controller.execute_command_sequence(commands)
            return True
            
        except Exception as e:
            print(f"Error executing instructions: {str(e)}")
            traceback.print_exc()
            return False
            
    def process_with_vision(self, prompt: str, screenshot_path: str) -> List[str]:
        """Process prompt with screenshot context (requires vision-capable model)"""
        try:
            print(f"Processing vision prompt: {prompt}")
            
            # Encode image to base64
            with open(screenshot_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
            # Create system message with command reference
            system_message = """
            You are an automation assistant that analyzes screenshots and converts natural language instructions 
            into specific commands for a PC automation tool. Look at the screenshot and generate the appropriate
            commands to accomplish the user's goal.
            
            Your task is to output ONLY the exact commands to execute, one per line, with NO explanations, 
            descriptions, markdown formatting, or commentary. Be extremely precise with your format.
            
            DO NOT include any explanations, headers, or descriptions in your response.
            DO NOT use markdown formatting like asterisks or backticks.
            DO NOT number your commands or add bullet points.
            DO NOT include any text that isn't a direct command.
            DO NOT use capital letters in commands - all commands must be lowercase.
            DO NOT include quotes or periods in your commands.
            
            The EXACT FORMAT for commands (use precisely these formats with no variations):
            
            - click on [text]           # Example: click on start menu
            - click at [x],[y]          # Example: click at 100,200
            - double-click on [text]    # Example: double-click on file
            - right-click on [text]     # Example: right-click on desktop
            - type [text]               # Example: type hello world
            - press [key]               # Example: press enter
            - hotkey [key1+key2]        # Example: hotkey win+r
            - wait [number] seconds     # Example: wait 2 seconds
            - scroll up [number]        # Example: scroll up 3
            - scroll down [number]      # Example: scroll down 2
            - move to [x],[y]           # Example: move to 100,200
            
            Example:
            User: Click on the Start menu and open Notepad
            Output:
            click at 10,985
            wait 1 seconds
            type notepad
            press enter
            wait 2 seconds
            """
            
            # Prepare request with image data
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]}
                ],
                "temperature": 0.7,
                "max_tokens": -1,
                "stream": False
            }
            
            # Call the local API
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            command_text = result["choices"][0]["message"]["content"].strip()
            
            print("Raw vision API response:", command_text)
            
            # Extract valid commands from the response
            commands = self.extract_valid_commands(command_text)
            
            # Store the commands for debugging
            self.last_commands = commands.copy()
            
            print(f"Generated {len(commands)} commands with vision context")
            return commands
            
        except Exception as e:
            print(f"Error processing vision prompt: {str(e)}")
            traceback.print_exc()
            self.last_commands = []
            return []
    
    def execute_vision_instructions(self, prompt: str, screenshot_path: str) -> bool:
        """Process AI vision instructions and execute them directly"""
        try:
            # Get commands from AI with vision context
            commands = self.process_with_vision(prompt, screenshot_path)
            
            # Store commands for reference (already done in process_with_vision but being explicit)
            self.last_commands = commands.copy() if commands else []
            
            if not commands:
                print("No commands were generated from the vision prompt")
                return False
                
            print(f"Executing {len(commands)} vision-based commands:")
            for cmd in commands:
                print(f"  - {cmd}")
                
            # Execute the commands
            if hasattr(self.controller, 'execute_command_sequence'):
                self.controller.execute_command_sequence(commands)
                return True
            else:
                print("Controller does not support command sequence execution")
                return False
                
        except Exception as e:
            print(f"Error executing vision instructions: {str(e)}")
            traceback.print_exc()
            return False 