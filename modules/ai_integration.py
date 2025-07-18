import os
import time
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.generative_models import GenerativeModel
# The client configure function is now directly under the genai namespace
# from google.generativeai.client import configure # This is deprecated
from PIL import Image # Import the Image class from Pillow
import numpy as np
import cv2

class AIIntegration:
    """AI integration module that uses Gemini API for visual understanding and automation"""
    
    def __init__(self, controller):
        """Initialize the AI integration module
        
        Args:
            controller: The main controller instance
        """
        self.controller = controller
        # IMPORTANT: Replace with your actual API key. The key provided is a placeholder format.
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAJ8PUjtePFcUpnCtc3fUAzQ1lBOQxDUk0")
        # Use a valid model that supports vision capabilities
        self.model_name = "gemini-2.5-flash" 
        self.model = None
        self.configure_api()
        self.last_commands = []
        self.last_response = None
        self.last_detected_ui_elements = []
        self.current_task = ""
        self.step_analysis = []
        self.automation_steps = []
        
    def configure_api(self):
        """Configure the Gemini API with the provided key"""
        if self.api_key == "YOUR_API_KEY_HERE":
            print("Error: Gemini API key not set. Please set the GEMINI_API_KEY environment variable or replace the placeholder in the code.")
            return False
        try:
            # Configure the Gemini API - different versions have different configuration methods
            # Instead of using configure, directly set the environment variable
            # which works with all versions
            import os
            os.environ["GOOGLE_API_KEY"] = self.api_key
            
            # Create the model
            self.model = GenerativeModel(self.model_name)
            print("Gemini API configured successfully")
            return True
        except Exception as e:
            print(f"Error configuring Gemini API: {str(e)}")
            return False
            
    def execute_ai_instructions(self, instructions):
        """Execute natural language instructions using AI without visual context
        
        Args:
            instructions: Natural language instructions for automation
            
        Returns:
            bool: Success or failure of execution
        """
        try:
            # For text-only tasks, a non-vision model can be used, 
            # but vision models also handle text perfectly well.
            text_model = GenerativeModel("gemini-2.5-flash")
            if not text_model:
                print("Gemini model not configured.")
                return False
            
            # Create a prompt that asks for automation commands
            prompt = f"""
            I need to automate the following task on a Windows computer:
            
            {instructions}
            
            Provide a list of precise automation commands to accomplish this task. 
            Each command should be on a new line and follow this format:
            
            click: [x coordinate, y coordinate] or [element name]
            type: [text to type]
            wait: [seconds]
            press: [key name like enter, tab, etc.]
            
            Only provide the command list, without any explanation or markdown formatting.
            """
            
            # Send the prompt to the model
            response = text_model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            self.last_response = response.text

            print("AI Response:", response.text)  # DEBUG
            
            # Parse the commands from the response
            commands = self._parse_commands(response.text)
            self.last_commands = commands
            
            print("Executing commands:", commands)
            
            # Execute the commands
            return self.controller.execute_command_sequence(commands)
            
        except Exception as e:
            print(f"Error in AI instructions: {str(e)}")
            return False
            
    def execute_vision_instructions(self, instructions, screenshot_path):
        """Execute automation instructions using Gemini's visual capabilities
        
        Args:
            instructions: Natural language instructions for automation
            screenshot_path: Path to the screenshot file
            
        Returns:
            bool: Success or failure of execution
        """
        try:
            # Use the vision model configured in __init__
            model = self.model
            if not model:
                print("Gemini vision model not configured.")
                return False

            # Open the image file using Pillow
            try:
                img = Image.open(screenshot_path)
            except FileNotFoundError:
                print(f"Error: Screenshot file not found at {screenshot_path}")
                return False

            # Store the current task description for step analysis
            self.current_task = instructions
            # Clear previous step analysis
            self.step_analysis = []
            
            # Make sure the controller's step callback is connected to the UI
            if hasattr(self.controller, 'set_step_callback') and not hasattr(self.controller, 'on_step_screenshot'):
                print("Warning: Controller step callback is not set. Trying to connect from GUI...")
                try:
                    # Look for any attribute that might be the GUI controller
                    for attr_name in dir(self.controller):
                        attr = getattr(self.controller, attr_name)
                        # Check if this attribute has the on_step_screenshot_callback method
                        if hasattr(attr, 'on_step_screenshot_callback') and callable(getattr(attr, 'on_step_screenshot_callback')):
                            print("Found GUI callback, connecting...")
                            self.controller.set_step_callback(attr.on_step_screenshot_callback)
                            break
                except Exception as e:
                    print(f"Error trying to connect step callback: {str(e)}")
                    # Continue without the callback

            # First, create a detailed step-by-step plan
            print("Creating step-by-step automation plan...")
            prompt = f"""
            Based on this screenshot of a Windows computer screen, I need to automate the following task:
            
            {instructions}
            
            Analyze the UI elements visible in the screenshot and provide a detailed step-by-step plan.
            For each step, include:
            1. A clear description of the action to take
            2. The specific UI element to interact with
            3. The expected result after the action
            
            Format your response as a JSON array of steps:
            [
                {{
                    "step_number": 1,
                    "action": "click",
                    "target": "Windows Start button",
                    "description": "Click on the Windows Start button in the bottom left corner",
                    "expected_result": "Start menu should open"
                }},
                ...
            ]
            
            Only provide the JSON array, without any surrounding text or explanation.
            """
            
            # Send the prompt and image to the model
            if model:
                response = model.generate_content(
                    [prompt, img],
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                # Clean and parse the response
                cleaned_response = self._clean_json_response(response.text)
                
                try:
                    # Parse the JSON output
                    steps = json.loads(cleaned_response)
                    print(f"Generated {len(steps)} steps for automation")
                    
                    # Store the steps for reference
                    self.automation_steps = steps
                    
                    # Execute each step individually with verification
                    return self._execute_steps_with_verification(steps, screenshot_path)
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing step plan: {str(e)}")
                    # Fall back to the old method
                    print("Falling back to basic command generation...")
                    return self._fallback_execute_vision_instructions(instructions, screenshot_path)
            else:
                print("Model not initialized. Falling back to basic command generation...")
                return self._fallback_execute_vision_instructions(instructions, screenshot_path)
                
        except Exception as e:
            print(f"Error in vision instructions: {str(e)}")
            return False
            
    def _execute_steps_with_verification(self, steps, initial_screenshot_path):
        """Execute steps with verification after each step
        
        Args:
            steps: List of step dictionaries
            initial_screenshot_path: Path to the initial screenshot
            
        Returns:
            bool: Success or failure of execution
        """
        current_screenshot_path = initial_screenshot_path
        overall_success = True
        
        print(f"Starting execution of {len(steps)} steps...")
        
        # Reset step counter
        if hasattr(self.controller, 'step_counter'):
            self.controller.step_counter = 0
            
        for i, step in enumerate(steps):
            step_num = step.get('step_number', i + 1)
            action = step.get('action', '').lower()
            target = step.get('target', '')
            description = step.get('description', f"Step {step_num}: {action} on {target}")
            expected_result = step.get('expected_result', '')
            
            print(f"\nExecuting step {step_num}/{len(steps)}: {description}")
            print(f"Expected result: {expected_result}")
            
            # Take a screenshot before the step if needed
            if current_screenshot_path != initial_screenshot_path:
                # We already have a screenshot from the previous step verification
                before_screenshot = current_screenshot_path
            else:
                # Take a new screenshot before the first step
                before_screenshot = self.controller.capture_step_screenshot(f"Before step {step_num}: {description}")
                current_screenshot_path = before_screenshot
                
            # Detect UI elements relevant to this specific step
            relevant_elements = self._detect_relevant_ui_elements(current_screenshot_path, step)
            
            # Create a command for this step
            command = self._create_command_from_step(step)
            
            if not command:
                print(f"Could not create command for step {step_num}. Skipping.")
                continue
                
            # Execute the command
            print(f"Executing command: {command}")
            
            # Convert to a list for execute_command_sequence
            commands = [command]
            
            # Execute the command
            success = self.controller.execute_command_sequence(commands)
            
            if not success:
                print(f"Failed to execute step {step_num}")
                overall_success = False
                continue
                
            # Take a screenshot after the step
            after_screenshot = self.controller.capture_step_screenshot(f"After step {step_num}: {description}")
            current_screenshot_path = after_screenshot
            
            # Verify the step was successful
            verification = self._verify_step_success(after_screenshot, step)
            
            if verification.get('success'):
                print(f"✓ Step {step_num} completed successfully: {verification.get('explanation', '')}")
            else:
                print(f"✗ Step {step_num} failed: {verification.get('explanation', '')}")
                overall_success = False
                # Consider whether to continue or stop on failure
                
        return overall_success
        
    def _detect_relevant_ui_elements(self, screenshot_path, step):
        """Detect UI elements relevant to the current step
        
        Args:
            screenshot_path: Path to the screenshot
            step: Step dictionary
            
        Returns:
            list: Relevant UI elements
        """
        try:
            # Open the image file using Pillow
            img = Image.open(screenshot_path)
            
            # Create a prompt to find elements relevant to this step
            action = step.get('action', '').lower()
            target = step.get('target', '')
            description = step.get('description', '')
            
            prompt = f"""
            I need to {action} on "{target}" in this screenshot.
            Description: {description}
            
            Identify the specific UI elements relevant to this step.
            Focus only on elements needed for this specific action, not all UI elements.
            
            Return a JSON array of elements:
            [
                {{
                    "label": "element description",
                    "box_2d": [x1, y1, x2, y2],
                    "relevance": "high/medium/low"
                }}
            ]
            
            Only include elements directly relevant to this step.
            """
            
            # Send the prompt and image to the model
            if self.model:
                response = self.model.generate_content(
                    [prompt, img],
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                # Clean and parse the response
                cleaned_response = self._clean_json_response(response.text)
                
                try:
                    # Parse the JSON output
                    elements = json.loads(cleaned_response)
                    print(f"Detected {len(elements)} elements relevant to step")
                    
                    # Store for annotation
                    self.last_detected_ui_elements = elements
                    
                    # Annotate the screenshot
                    annotated_path = self.annotate_detected_ui_elements(screenshot_path)
                    
                    # Update the UI if callback exists
                    if hasattr(self.controller, 'on_step_screenshot') and callable(self.controller.on_step_screenshot):
                        self.controller.on_step_screenshot(
                            self.controller.step_counter, 
                            f"Detected elements for: {description}", 
                            annotated_path or screenshot_path
                        )
                    
                    return elements
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing UI elements: {str(e)}")
                    return []
            else:
                print("Model not initialized. Cannot detect UI elements.")
                return []
                
        except Exception as e:
            print(f"Error detecting relevant UI elements: {str(e)}")
            return []
            
    def _create_command_from_step(self, step):
        """Create a command from a step dictionary
        
        Args:
            step: Step dictionary
            
        Returns:
            str: Command string
        """
        action = step.get('action', '').lower()
        target = step.get('target', '')
        
        if action == 'click':
            return f"click: {target}"
        elif action == 'type' or action == 'input':
            text = step.get('text', step.get('input_text', ''))
            return f"type: {text}"
        elif action == 'press':
            key = step.get('key', '')
            return f"press: {key}"
        elif action == 'wait':
            duration = step.get('duration', 1)
            return f"wait: {duration}"
        else:
            # Handle other action types
            return f"{action}: {target}"
            
    def _verify_step_success(self, screenshot_path, step):
        """Verify if a step was successful
        
        Args:
            screenshot_path: Path to the screenshot after the step
            step: Step dictionary
            
        Returns:
            dict: Verification result
        """
        try:
            # Open the image file using Pillow
            img = Image.open(screenshot_path)
            
            # Create a prompt to verify the step
            action = step.get('action', '').lower()
            target = step.get('target', '')
            description = step.get('description', '')
            expected_result = step.get('expected_result', '')
            
            prompt = f"""
            I just performed this action: {description}
            
            Expected result: {expected_result}
            
            Analyze this screenshot and determine:
            1. Was this action successful? (yes/no)
            2. What evidence supports your conclusion?
            3. What should be the next logical action based on the current screen state?
            
            Return your response in JSON format:
            {{
                "success": true/false,
                "explanation": "brief explanation of what happened",
                "next_action_suggestion": "suggested next action"
            }}
            """
            
            # Send the prompt and image to the model
            if self.model:
                response = self.model.generate_content(
                    [prompt, img],
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                # Clean and parse the response
                cleaned_response = self._clean_json_response(response.text)
                
                try:
                    # Parse the JSON output
                    result = json.loads(cleaned_response)
                    
                    # Store analysis for this step
                    self.step_analysis.append({
                        "step": step,
                        "analysis": result
                    })
                    
                    # Update the UI if callback exists
                    if hasattr(self.controller, 'on_step_screenshot') and callable(self.controller.on_step_screenshot):
                        success_status = "✓ Success" if result.get('success') else "✗ Failed"
                        explanation = result.get('explanation', 'No explanation provided')
                        self.controller.on_step_screenshot(
                            self.controller.step_counter, 
                            f"{description} - {success_status}: {explanation}", 
                            screenshot_path
                        )
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing verification result: {str(e)}")
                    return {"success": False, "explanation": f"Error parsing AI response: {str(e)}"}
            else:
                print("Model not initialized. Cannot verify step success.")
                return {"success": False, "explanation": "AI model not available"}
                
        except Exception as e:
            print(f"Error verifying step success: {str(e)}")
            return {"success": False, "explanation": f"Error: {str(e)}"}
            
    def _fallback_execute_vision_instructions(self, instructions, screenshot_path):
        """Fall back to the old method of executing instructions
        
        Args:
            instructions: Natural language instructions for automation
            screenshot_path: Path to the screenshot file
            
        Returns:
            bool: Success or failure of execution
        """
        print("Using fallback execution method...")
        
        try:
            # Open the image file using Pillow
            img = Image.open(screenshot_path)
            
            # Create a prompt that asks for automation commands
            prompt = f"""
            Based on this screenshot of a Windows computer screen, I need to automate the following task:
            
            {instructions}
            
            Analyze the UI elements visible in the screenshot and provide a list of precise automation commands 
            to accomplish this task. Each command should be on a new line and follow this format:
            
            click: [element name or description]
            type: [text to type]
            wait: [seconds]
            press: [key name]
            
            Only provide the raw list of commands, without any surrounding text, comments, or markdown formatting like ```.
            """
            
            # Send the prompt and image to the model
            if self.model:
                response = self.model.generate_content(
                    [prompt, img],
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                self.last_response = response.text
                
                # Parse the commands from the response
                commands = self._parse_commands(response.text)
                self.last_commands = commands
                
                # Execute the commands
                return self.controller.execute_command_sequence(commands)
            else:
                print("Model not initialized. Cannot generate commands.")
                return False
            
        except Exception as e:
            print(f"Error in fallback execution: {str(e)}")
            return False
    
    def detect_ui_elements(self, screenshot_path):
        """Detect UI elements in the given screenshot using Gemini Vision API
        
        Args:
            screenshot_path: Path to the screenshot file
            
        Returns:
            list: List of detected UI elements with bounding boxes
        """
        try:
            model = self.model
            if not model:
                print("Gemini vision model not configured.")
                return []
                
            # Open the image file using Pillow
            try:
                img = Image.open(screenshot_path)
            except FileNotFoundError:
                print(f"Error: Screenshot file not found at {screenshot_path}")
                return []
                
            # Create prompt for UI element detection
            prompt = """
            Detect all 2d bounding boxes of the ui elements in the provided screenshot of a microsoft windows.
            return just box_2d and labels, no additional text.
            example output: {"box_2d": [435, 87, 727, 281], "label": "window icon"}
            """
            
            # Send the prompt and image to the model
            response = model.generate_content(
                [prompt, img],
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Clean and parse the response
            cleaned_response = self._clean_ui_elements_response(response.text)
            
            try:
                # Parse the JSON output
                ui_elements = json.loads(cleaned_response)
                self.last_detected_ui_elements = ui_elements
                print(f"Successfully detected {len(ui_elements)} UI elements")
                return ui_elements
            except json.JSONDecodeError as e:
                print(f"Error parsing UI element detection response: {str(e)}")
                return []
                
        except Exception as e:
            print(f"Error detecting UI elements: {str(e)}")
            return []
            
    def _clean_ui_elements_response(self, response_text):
        """Clean the UI element detection response for JSON parsing
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            str: Cleaned JSON string
        """
        # Remove markdown code blocks
        cleaned = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        return cleaned
    
    def _parse_commands(self, response_text):
        """Parse commands from the model's response
        
        Args:
            response_text: Text response from the model
            
        Returns:
            list: List of commands to execute
        """
        commands = []
        # Clean up potential markdown code blocks from the response
        cleaned_text = response_text.replace("```", "").strip()

        for line in cleaned_text.split('\n'):
            line = line.strip()
            
            # Skip empty lines or lines that are not valid commands
            if not line or ':' not in line:
                continue
                
            # Basic validation for command format
            command_part = line.split(':', 1)[0].lower()
            if command_part in ['click', 'type', 'wait', 'press']:
                commands.append(line)
        
        return commands
    
    def save_response_to_file(self, filename="ai_response.txt"):
        """Save the last response to a file for debugging
        
        Args:
            filename: Name of the file to save the response to
        """
        if self.last_response:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("--- LAST RESPONSE ---\n")
                    f.write(self.last_response)
                    f.write("\n\n--- PARSED COMMANDS ---\n")
                    f.write("\n".join(self.last_commands))
                print(f"Successfully saved AI response and commands to {filename}")
                return True
            except Exception as e:
                print(f"Error saving response to file: {str(e)}")
                return False
        else:
            print("No response to save.")
            return False
            
    def get_suggested_workflow(self, task_description):
        """Get a suggested workflow for a given task
        
        Args:
            task_description: Description of the task
            
        Returns:
            dict: Suggested workflow with name and commands, or None on failure
        """
        try:
            text_model = GenerativeModel("gemini-2.5-flash")
            if not text_model:
                print("Gemini model not configured.")
                return None
            
            # Create a prompt that asks for a workflow
            prompt = f"""
            Create a workflow for the following automation task:
            
            {task_description}
            
            Provide a list of commands that can be saved as a workflow.
            Each command should be on a new line and follow automation patterns like:
            click: [description]
            type: [text]
            wait: [seconds]
            press: [key]

            Only output the list of commands. Do not include any explanations or markdown.
            """
            
            # Send the prompt to the model
            response = text_model.generate_content(prompt)
            
            # Parse the commands
            commands = self._parse_commands(response.text)
            
            if not commands:
                print("AI did not return any valid commands for the workflow.")
                return None

            # Generate a workflow name
            workflow_name = "".join(c if c.isalnum() else "_" for c in task_description.lower()).replace("__", "_")
            workflow_name = workflow_name.strip('_')[:30]
            
            return {
                "name": workflow_name,
                "commands": commands
            }
            
        except Exception as e:
            print(f"Error generating workflow: {str(e)}")
            return None
        
    def get_detected_ui_elements(self):
        """Get the last detected UI elements
        
        Returns:
            list: List of detected UI elements with bounding boxes and labels
        """
        return self.last_detected_ui_elements
        
    def annotate_detected_ui_elements(self, screenshot_path):
        """Annotate the screenshot with detected UI elements
        
        Args:
            screenshot_path: Path to the screenshot file
            
        Returns:
            str: Path to the annotated image
        """
        try:
            if not self.last_detected_ui_elements:
                print("No UI elements detected to annotate")
                return None
                
            # Open the original image
            img = Image.open(screenshot_path)
            img_array = np.array(img)
            
            # Convert to OpenCV format (RGB to BGR)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Get image dimensions
            h, w = img_cv.shape[:2]
            
            # Draw bounding boxes on the image
            for idx, element in enumerate(self.last_detected_ui_elements):
                # Extract coordinates and normalize if needed
                box = element.get("box_2d", [])
                if len(box) != 4:
                    continue
                    
                x1, y1, x2, y2 = box
                
                # If coordinates are normalized (0-1000), scale them to image dimensions
                if max(box) > 0 and max(box) <= 1000:
                    x1 = int(x1 / 1000 * w)
                    y1 = int(y1 / 1000 * h)
                    x2 = int(x2 / 1000 * w)
                    y2 = int(y2 / 1000 * h)
                
                # Ensure coordinates are in correct order
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                    
                # Generate a color based on index
                color = (0, 255, 0)  # Default green
                
                # Draw rectangle
                cv2.rectangle(img_cv, (x1, y1), (x2, y2), color, 2)
                
                # Add label
                label = element.get("label", f"Element {idx}")
                cv2.putText(img_cv, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
            # Save the annotated image
            output_filename = os.path.splitext(screenshot_path)[0] + "_annotated.png"
            cv2.imwrite(output_filename, img_cv)
            return output_filename
            
        except Exception as e:
            print(f"Error annotating UI elements: {str(e)}")
            return None

    def analyze_current_step(self, screenshot_path, step_num, action_description):
        """Analyze the current step screenshot and determine if it was successful
        
        Args:
            screenshot_path: Path to the screenshot after the action
            step_num: The current step number
            action_description: Description of the action that was performed
            
        Returns:
            dict: Analysis results with success status and explanation
        """
        try:
            model = self.model
            if not model:
                print("Gemini vision model not configured.")
                return {"success": None, "explanation": "AI model not configured"}
                
            # First detect UI elements in the screenshot
            ui_elements = self.detect_ui_elements(screenshot_path)
            
            # Open the image file using Pillow
            try:
                img = Image.open(screenshot_path)
            except FileNotFoundError:
                print(f"Error: Screenshot file not found at {screenshot_path}")
                return {"success": False, "explanation": "Screenshot not found"}
                
            # Create a prompt that asks to analyze the current step
            prompt = f"""
            I'm automating this task: "{self.current_task}".
            
            Current step #{step_num}: {action_description}
            
            Analyze this screenshot and determine:
            1. Was this action successful? (yes/no)
            2. What UI elements are currently visible?
            3. What should be the next logical action based on the current screen state?
            
            Return your response in JSON format:
            {{
                "success": true/false,
                "visible_elements": ["list of key UI elements visible"],
                "explanation": "brief explanation of what happened",
                "next_action_suggestion": "suggested next action"
            }}
            """
            
            # Send the prompt and image to the model
            response = model.generate_content(
                [prompt, img],
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Clean and parse the response
            cleaned_response = self._clean_json_response(response.text)
            
            try:
                # Parse the JSON output
                result = json.loads(cleaned_response)
                
                # Store analysis for this step
                self.step_analysis.append({
                    "step_num": step_num,
                    "action": action_description,
                    "analysis": result
                })
                
                print(f"Step {step_num} analysis: {'Success' if result.get('success') else 'Failed'}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"Error parsing step analysis response: {str(e)}")
                return {"success": None, "explanation": f"Error parsing AI response: {str(e)}"}
                
        except Exception as e:
            print(f"Error analyzing step: {str(e)}")
            return {"success": None, "explanation": f"Error: {str(e)}"}
    
    def _clean_json_response(self, response_text):
        """Clean the JSON response for parsing
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            str: Cleaned JSON string
        """
        # Remove markdown code blocks and find JSON content
        cleaned = response_text.strip()
        
        # Find JSON between triple backticks if present
        json_start = cleaned.find("```json")
        json_end = cleaned.rfind("```")
        
        if json_start != -1 and json_end > json_start:
            # Extract content between backticks
            cleaned = cleaned[json_start + 7:json_end].strip()
        
        # If there's no JSON formatting but still has backticks
        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned[3:-3].strip()
            
        return cleaned