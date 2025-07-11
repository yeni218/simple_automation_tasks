#!/usr/bin/env python
# AI Vision Controller - Main application

import sys
import os
import json
import time  # Add time import
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
import threading
import tkinter.ttk as ttk

# Set appearance mode and theme
ctk.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Constants
NEVER_FOUND = "Not found yet"

# Add modules directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
try:
    from modules.ai_vision_controller import AIVisionController
    from modules.ocr_utils import OCRUtils
    from modules.command_parser import CommandParser
    from modules.workflow_manager import WorkflowManager
    from modules.ai_integration import AIIntegration
    from modules.gui.ui_controller_gui import AIControllerGUI
    from modules.gui.tab_commands import CommandsTabManager
    from modules.gui.tab_prompt import PromptTabManager
    from modules.gui.ui_dialogs import UIElementDialog
except ImportError as e:
    print(f"Error importing modules: {str(e)}")
    print("Make sure all required packages are installed using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

class EnhancedAIControllerGUI(AIControllerGUI):
    """Enhanced GUI controller that integrates all modules"""
    
    def __init__(self, controller):
        """Initialize the enhanced GUI controller"""
        # Initialize managers before calling parent constructor
        self.ocr_utils = OCRUtils(controller)
        self.command_parser = CommandParser()
        self.workflow_manager = WorkflowManager(controller)
        self.ai_manager = AIIntegration(controller)
        
        # Connect the OCR utils to controller
        controller.ocr_utils = self.ocr_utils
        controller.command_parser = self.command_parser
        controller.workflow_manager = self.workflow_manager
        controller.ai_manager = self.ai_manager
        
        # Now call the parent constructor which will call setup_gui()
        super().__init__(controller)
        
    def setup_commands_tab(self, parent):
        """Setup the Commands tab"""
        self.commands_tab = CommandsTabManager(parent, self.controller, self)
        
    def setup_ui_elements_tab(self, parent):
        """Setup the UI Elements tab"""
        # Create frame for UI elements
        ui_frame = ctk.CTkFrame(parent)
        ui_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - UI element list
        left_frame = ctk.CTkFrame(ui_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # UI Elements list with scrollbar
        ctk.CTkLabel(left_frame, text="Saved UI Elements:").pack(anchor=tk.W)
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ui_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1], 
                                    fg=ctk.ThemeManager.theme["CTkLabel"]["text_color"][1],
                                    selectbackground=ctk.ThemeManager.theme["CTkButton"]["fg_color"][1])
        self.ui_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=self.ui_listbox.yview)
        
        # Bind selection event
        self.ui_listbox.bind('<<ListboxSelect>>', self.show_element_details)
        
        # Buttons for UI elements
        btn_frame = ctk.CTkFrame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkButton(btn_frame, text="Add Element", command=self.add_ui_element).pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete Element", command=self.delete_ui_element).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Test Find", command=self.test_find_element).pack(side=tk.LEFT, padx=5)
        
        # Right side - Element details
        right_frame = ctk.CTkFrame(ui_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Element details
        ctk.CTkLabel(right_frame, text="Element Details:").pack(anchor=tk.W)
        self.element_details = ctk.CTkTextbox(right_frame, height=10, width=40)
        self.element_details.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Preview image
        ctk.CTkLabel(right_frame, text="Preview:").pack(anchor=tk.W, pady=(10, 5))
        self.preview_frame = ctk.CTkFrame(right_frame)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Update UI elements list
        self.update_ui_elements_list()
        
    def setup_workflows_tab(self, parent):
        """Setup the Workflows tab"""
        # Create frame for workflows
        workflows_frame = ctk.CTkFrame(parent)
        workflows_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Workflow list
        left_frame = ctk.CTkFrame(workflows_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Workflows list with scrollbar
        ctk.CTkLabel(left_frame, text="Saved Workflows:").pack(anchor=tk.W)
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.workflow_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1], 
                                         fg=ctk.ThemeManager.theme["CTkLabel"]["text_color"][1],
                                         selectbackground=ctk.ThemeManager.theme["CTkButton"]["fg_color"][1])
        self.workflow_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=self.workflow_listbox.yview)
        
        # Bind selection event
        self.workflow_listbox.bind('<<ListboxSelect>>', self.show_workflow_details)
        
        # Buttons for workflows
        btn_frame = ctk.CTkFrame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkButton(btn_frame, text="New Workflow", command=self.new_workflow).pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete Workflow", command=self.delete_workflow).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Run Workflow", command=self.run_workflow).pack(side=tk.LEFT, padx=5)
        
        # Right side - Workflow details
        right_frame = ctk.CTkFrame(workflows_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Workflow details
        ctk.CTkLabel(right_frame, text="Workflow Commands:").pack(anchor=tk.W)
        self.workflow_commands = ctk.CTkTextbox(right_frame, height=10)
        self.workflow_commands.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Edit buttons
        edit_frame = ctk.CTkFrame(right_frame)
        edit_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkButton(edit_frame, text="Save Changes", command=self.save_workflow_changes).pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(edit_frame, text="Record Commands", command=self.record_workflow).pack(side=tk.LEFT, padx=5)
        
        # Update workflow list
        self.update_workflow_list()
        
    def setup_prompt_tab(self, parent):
        """Setup the AI Prompt tab"""
        self.prompt_tab = PromptTabManager(parent, self.controller, self, self.ai_manager)
    
    def setup_ai_automation_tab(self, parent):
        """Setup the AI Automation tab for direct automation from instructions"""
        # Create frame for AI automation
        ai_frame = ctk.CTkFrame(parent)
        ai_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions label
        ctk.CTkLabel(ai_frame, text="Enter natural language instructions for automation:").pack(anchor=tk.W, pady=(0, 5))
        
        # Text area for instructions
        self.ai_instructions = ctk.CTkTextbox(ai_frame, height=100)
        self.ai_instructions.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Example instructions
        examples = [
            "Open Notepad and type 'Hello, world!'",
            "Open Calculator, click on 5, then +, then 3, then =",
            "Open Paint, draw a rectangle in the center"
        ]
        example_text = "Examples:\n" + "\n".join(f"• {ex}" for ex in examples)
        ctk.CTkLabel(ai_frame, text=example_text, text_color="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # Options frame
        options_frame = ctk.CTkFrame(ai_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Visual feedback option
        self.visual_feedback_var = tk.BooleanVar(value=True)
        visual_feedback_cb = ctk.CTkCheckBox(
            options_frame,
            text="Show visual feedback (slower but visible mouse movements)",
            variable=self.visual_feedback_var,
            command=self.toggle_visual_feedback
        )
        visual_feedback_cb.pack(side=tk.LEFT, padx=5)
        
        # Speed slider
        speed_frame = ctk.CTkFrame(ai_frame)
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        ctk.CTkLabel(speed_frame, text="Movement Speed:", width=120).pack(side=tk.LEFT, padx=5)
        
        self.speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            command=self.update_movement_speed
        )
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.speed_slider.set(5)  # Default value (0.5s)
        
        self.speed_label = ctk.CTkLabel(speed_frame, text="0.5s")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(ai_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Execute button
        execute_btn = ctk.CTkButton(
            btn_frame, 
            text="Execute Instructions", 
            command=self.execute_ai_instructions
        )
        execute_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Take screenshot button
        screenshot_btn = ctk.CTkButton(
            btn_frame, 
            text="Take Screenshot for Context", 
            command=self.take_screenshot_for_ai
        )
        screenshot_btn.pack(side=tk.LEFT)
        
        # Results frame
        results_frame = ctk.CTkFrame(ai_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ctk.CTkLabel(results_frame, text="Execution Results:").pack(anchor=tk.W, padx=5, pady=5)
        
        # Results text area
        self.ai_results = ctk.CTkTextbox(results_frame, height=150)
        self.ai_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Screenshot path variable and label
        self.screenshot_path = tk.StringVar()
        self.screenshot_path.set("")
        ctk.CTkLabel(ai_frame, textvariable=self.screenshot_path).pack(anchor=tk.W, pady=(5, 0))
        
    # UI Elements tab methods
    def show_element_details(self, event):
        """Show details of the selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            element = self.controller.ui_elements.get(element_name)
            
            if element:
                self.element_details.delete("0.0", "end")
                details = f"Name: {element_name}\n"
                details += f"Image: {element['image_path']}\n"
                details += f"Action: {element.get('action_type', 'click')}\n"
                
                # Handle last_found value with constant
                last_found = element.get('last_found')
                if last_found is not None:
                    details += f"Last Found: {last_found}"
                else:
                    details += f"Last Found: {NEVER_FOUND}"
                
                self.element_details.insert("0.0", details)
                
                # Display the preview image
                self.display_element_preview(element['image_path'])
                
    def update_ui_elements_list(self):
        """Update the UI elements list"""
        self.ui_listbox.delete(0, tk.END)
        for element_name in self.controller.ui_elements:
            self.ui_listbox.insert(tk.END, element_name)
            
    def add_ui_element(self):
        """Add a new UI element"""
        from modules.gui.ui_dialogs import UIElementDialog
        
        # Two options: create from file or from screenshot
        options = ["Select from existing image file", "Capture from screen"]
        choice = messagebox.askquestion("Add UI Element", "Would you like to capture from screen?")
        
        if choice == 'yes':
            # Create from screenshot
            self.create_ui_element_from_screen()
        else:
            # Create from file
            dialog = UIElementDialog(self.root, self.controller)
            
            # The dialog will handle saving the element to the controller
            # We just need to update the UI afterwards if something was added
            if dialog.result is True:
                self.update_ui_elements_list()
                
    def create_ui_element_from_screen(self):
        """Create a UI element by selecting a region from the screen"""
        # Hide window to take screenshot
        self.root.withdraw()
        time.sleep(0.5)  # Give time for window to hide
        
        try:
            # Take full screenshot
            screenshot = self.controller.take_screenshot()
            
            # Show window again
            self.root.deiconify()
            
            # Show screenshot selector dialog
            from tkinter import simpledialog
            from PIL import ImageTk
            
            class ScreenshotSelector:
                def __init__(self, parent, screenshot):
                    self.root = tk.Toplevel(parent)
                    self.root.title("Select Region")
                    self.root.attributes('-fullscreen', True)
                    
                    self.screenshot = screenshot
                    self.tk_image = ImageTk.PhotoImage(screenshot)
                    
                    self.canvas = tk.Canvas(self.root, cursor="cross")
                    self.canvas.pack(fill=tk.BOTH, expand=True)
                    
                    # Draw screenshot on canvas
                    self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
                    
                    # Variables to store selection
                    self.start_x = None
                    self.start_y = None
                    self.rect_id = None
                    self.selection = None
                    
                    # Bind events
                    self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
                    self.canvas.bind("<B1-Motion>", self.on_mouse_move)
                    self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
                    self.root.bind("<Escape>", lambda e: self.cancel())
                    
                    # Show instructions
                    instructions = tk.Label(
                        self.root,
                        text="Click and drag to select a region. Press ESC to cancel.",
                        bg="white",
                        fg="black",
                        font=("Arial", 12)
                    )
                    instructions.place(relx=0.5, rely=0.05, anchor=tk.CENTER)
                    
                def on_mouse_down(self, event):
                    """Handle mouse button down event"""
                    self.start_x = self.canvas.canvasx(event.x)
                    self.start_y = self.canvas.canvasy(event.y)
                    
                    # Create rectangle
                    if self.rect_id:
                        self.canvas.delete(self.rect_id)
                    self.rect_id = self.canvas.create_rectangle(
                        self.start_x, self.start_y, self.start_x, self.start_y,
                        outline="red", width=2
                    )
                    
                def on_mouse_move(self, event):
                    """Handle mouse movement event"""
                    if self.rect_id:
                        cur_x = self.canvas.canvasx(event.x)
                        cur_y = self.canvas.canvasy(event.y)
                        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
                        
                def on_mouse_up(self, event):
                    """Handle mouse button up event"""
                    end_x = self.canvas.canvasx(event.x)
                    end_y = self.canvas.canvasy(event.y)
                    
                    # Calculate rectangle coordinates
                    x1 = min(self.start_x, end_x)
                    y1 = min(self.start_y, end_y)
                    x2 = max(self.start_x, end_x)
                    y2 = max(self.start_y, end_y)
                    
                    # Store selection
                    self.selection = (int(x1), int(y1), int(x2-x1), int(y2-y1))
                    
                    # Close selector
                    self.root.destroy()
                    
                def cancel(self):
                    """Cancel selection"""
                    self.selection = None
                    self.root.destroy()
            
            # Create selector
            selector = ScreenshotSelector(self.root, screenshot)
            self.root.wait_window(selector.root)
            
            if selector.selection:
                # Get region from selection
                region = selector.selection
                
                # Crop the image
                cropped_image = screenshot.crop((
                    region[0], region[1], 
                    region[0] + region[2], region[1] + region[3]
                ))
                
                # Ask for element name and action type
                element_name = simpledialog.askstring(
                    "Element Name", 
                    "Enter a name for this UI element:"
                )
                
                if not element_name:
                    messagebox.showinfo("Cancelled", "Element creation cancelled")
                    return
                
                # Save cropped image
                os.makedirs("ui_elements", exist_ok=True)
                image_path = os.path.join("ui_elements", f"{element_name}.png")
                cropped_image.save(image_path)
                
                # Add to controller
                action_types = ["click", "double_click", "right_click", "type", "scroll"]
                action_type = simpledialog.askstring(
                    "Action Type",
                    "Select action type (click, double_click, right_click, type, scroll):",
                    initialvalue="click"
                )
                
                if action_type not in action_types:
                    action_type = "click"  # Default
                
                # Save UI element
                self.controller.save_ui_element(element_name, image_path, action_type)
                
                # Update UI
                self.update_ui_elements_list()
                messagebox.showinfo("Success", f"UI element '{element_name}' created successfully")
                
        except Exception as e:
            # Show main window in case of error
            self.root.deiconify()
            messagebox.showerror("Error", f"Failed to create UI element: {str(e)}")
        
    def delete_ui_element(self):
        """Delete the selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            if messagebox.askyesno("Confirm Delete", f"Delete UI element '{element_name}'?"):
                if element_name in self.controller.ui_elements:
                    del self.controller.ui_elements[element_name]
                    self.update_ui_elements_list()
                    self.element_details.delete("0.0", "end")
                    
    def test_find_element(self):
        """Test finding the selected UI element"""
        selection = self.ui_listbox.curselection()
        if selection:
            element_name = self.ui_listbox.get(selection[0])
            # Hide the window temporarily
            self.root.withdraw()
            time.sleep(0.5)  # Give time for window to hide
            
            # Try to find the element
            location = self.controller.find_ui_element(element_name)
            
            # Show the window again
            self.root.deiconify()
            
            if location:
                messagebox.showinfo("Element Found", f"Found '{element_name}' at {location}")
            else:
                messagebox.showwarning("Element Not Found", f"Could not find '{element_name}' on screen")
                
    # Workflow tab methods
    def show_workflow_details(self, event):
        """Show details of the selected workflow"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            self.workflow_name = workflow_name  # Store current workflow name
            
            workflow = self.workflow_manager.get_workflow_details(workflow_name)
            if workflow:
                self.workflow_commands.delete("0.0", "end")
                commands = workflow.get('commands', [])
                self.workflow_commands.insert("0.0", "\n".join(commands))
                
    def update_workflow_list(self):
        """Update the workflow list"""
        self.workflow_listbox.delete(0, tk.END)
        for workflow_name in self.workflow_manager.get_workflow_list():
            self.workflow_listbox.insert(tk.END, workflow_name)
            
    def new_workflow(self):
        """Create a new workflow"""
        # Clear the workflow commands
        self.workflow_commands.delete("0.0", "end")
        self.workflow_name = "new_workflow"
        messagebox.showinfo("New Workflow", "Enter commands for the new workflow")
        
    def delete_workflow(self):
        """Delete the selected workflow"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            if messagebox.askyesno("Confirm Delete", f"Delete workflow '{workflow_name}'?"):
                self.workflow_manager.delete_workflow(workflow_name)
                self.update_workflow_list()
                self.workflow_commands.delete("0.0", "end")
                
    def run_workflow(self):
        """Run the selected workflow"""
        selection = self.workflow_listbox.curselection()
        if selection:
            workflow_name = self.workflow_listbox.get(selection[0])
            if messagebox.askyesno("Confirm Run", f"Run workflow '{workflow_name}'?"):
                threading.Thread(target=self.workflow_manager.run_workflow, 
                               args=(workflow_name,)).start()
                
    def save_workflow_changes(self):
        """Save changes to the current workflow"""
        if hasattr(self, 'workflow_name'):
            commands_text = self.workflow_commands.get("0.0", "end").strip()
            commands = [cmd for cmd in commands_text.split('\n') if cmd.strip()]
            
            if not commands:
                messagebox.showwarning("Empty Workflow", "Please enter at least one command")
                return
                
            if self.workflow_name in self.workflow_manager.workflows:
                self.workflow_manager.update_workflow(self.workflow_name, commands)
            else:
                self.workflow_manager.create_workflow(self.workflow_name, commands)
                
            self.update_workflow_list()
            messagebox.showinfo("Saved", f"Workflow '{self.workflow_name}' saved")
            
    def record_workflow(self):
        """Record a new workflow"""
        messagebox.showinfo("Record Workflow", 
                          "Recording mode is not yet implemented.\n"
                          "Please enter commands manually.")
            
    def toggle_visual_feedback(self):
        """Toggle visual feedback for mouse movements"""
        enable = self.visual_feedback_var.get()
        self.controller.toggle_visual_feedback(enable)
        if enable:
            self.ai_results.insert("end", "Visual feedback enabled - mouse movements will be visible\n")
        else:
            self.ai_results.insert("end", "Visual feedback disabled - automation will run faster\n")
        
    def update_movement_speed(self, value):
        """Update the movement speed for visual feedback"""
        # Convert slider value (1-10) to duration (0.1-1.0)
        duration = float(value) / 10.0
        self.controller.move_duration = duration
        self.speed_label.configure(text=f"{duration:.1f}s")
            
    def execute_ai_instructions(self):
        """Execute instructions from the AI automation tab"""
        instructions = self.ai_instructions.get("0.0", "end").strip()
        if not instructions:
            messagebox.showwarning("Empty Instructions", "Please enter instructions for automation")
            return
            
        self.ai_results.delete("0.0", "end")
        self.ai_results.insert("0.0", f"Processing instructions: {instructions}\n\n")
        
        # Check API connection first
        api_endpoint = self.controller.api_endpoint
        self.ai_results.insert("end", f"Using API endpoint: {api_endpoint}\n")
        
        try:
            # Try a simple request to check connectivity
            import requests
            response = requests.get(api_endpoint.split('/v1')[0] + '/v1/models', timeout=2)
            if response.status_code == 200:
                self.ai_results.insert("end", "API connection successful. Processing...\n")
            else:
                self.ai_results.insert("end", f"API returned status code {response.status_code}.\n")
        except Exception as conn_err:
            self.ai_results.insert("end", f"⚠️ Warning: API connection failed. Will use fallback methods.\n")
            self.ai_results.insert("end", f"Error details: {str(conn_err)}\n\n")
        
        # Make the application window smaller but don't hide completely
        # This allows users to see the automation happening
        if self.visual_feedback_var.get():
            # Don't hide the window if visual feedback is enabled
            self.root.wm_state('iconic')  # Minimize but don't hide
            # Move to corner of screen to be less intrusive
            self.root.geometry('+0+0')
            time.sleep(0.5)  # Give less time to hide
        else:
            # Hide completely if visual feedback is disabled
            self.root.withdraw()
            time.sleep(1.0)  # Give time for window to hide
        
        try:
            # Check if we have a screenshot for context
            if self.screenshot_path.get() and os.path.exists(self.screenshot_path.get()):
                screenshot = self.screenshot_path.get()
                self.ai_results.insert("end", f"Using screenshot for context: {screenshot}\n\n")
                success = self.ai_manager.execute_vision_instructions(instructions, screenshot)
                
                # If vision instructions failed but succeeded in generating commands, show them
                if not success and hasattr(self.ai_manager, 'last_commands'):
                    commands = getattr(self.ai_manager, 'last_commands', [])
                    if commands:
                        self.ai_results.insert("end", "Generated commands (not executed successfully):\n")
                        for cmd in commands:
                            self.ai_results.insert("end", f"- {cmd}\n")
            else:
                # Use regular AI instructions (will always try API first now)
                success = self.ai_manager.execute_ai_instructions(instructions)
                
                # Show commands that were used
                if hasattr(self.ai_manager, 'last_commands'):
                    commands = getattr(self.ai_manager, 'last_commands', [])
                    if commands:
                        self.ai_results.insert("end", "\nCommands used:\n")
                        for cmd in commands:
                            self.ai_results.insert("end", f"- {cmd}\n")
                
            if success:
                self.ai_results.insert("end", "✓ Instructions executed successfully\n")
            else:
                self.ai_results.insert("end", "✗ Failed to execute instructions\n")
                self.ai_results.insert("end", "\nTo ensure AI automation works correctly:\n")
                self.ai_results.insert("end", "1. Check that your local LLM server is running\n")
                self.ai_results.insert("end", "2. Verify the API endpoint in the AI Prompt tab\n")
                self.ai_results.insert("end", "3. Try using more specific instructions\n")
                self.ai_results.insert("end", "4. Use the screenshot feature for context\n")
                
        except Exception as e:
            self.ai_results.insert("end", f"✗ Error during execution: {str(e)}\n")
        finally:
            # Show the application window again
            self.root.deiconify()
            
    def take_screenshot_for_ai(self):
        """Take a screenshot for AI context"""
        # Hide the application window temporarily
        self.root.withdraw()
        time.sleep(0.5)  # Give time for window to hide
        
        try:
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            
            # Generate a unique filename
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            
            # Save the screenshot
            screenshot.save(filename)
            
            # Update the screenshot path
            self.screenshot_path.set(filename)
            
            # Show success message
            self.ai_results.delete("0.0", "end")
            self.ai_results.insert("0.0", f"Screenshot saved to {filename}\n")
            
        except Exception as e:
            messagebox.showerror("Screenshot Error", f"Failed to take screenshot: {str(e)}")
        finally:
            # Show the application window again
            self.root.deiconify()
            
    def setup_gui(self):
        """Setup the GUI with notebook and tabs"""
        # Set the window title
        self.root.title("AI Vision Controller")
        
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.notebook.add("Commands")
        self.notebook.add("UI Elements")
        self.notebook.add("Workflows")
        self.notebook.add("AI Prompt")
        self.notebook.add("AI Automation")
        
        # Setup each tab
        self.setup_commands_tab(self.notebook.tab("Commands"))
        self.setup_ui_elements_tab(self.notebook.tab("UI Elements"))
        self.setup_workflows_tab(self.notebook.tab("Workflows"))
        self.setup_prompt_tab(self.notebook.tab("AI Prompt"))
        self.setup_ai_automation_tab(self.notebook.tab("AI Automation"))
        
        # Create menu
        self.setup_menu()

    def display_element_preview(self, image_path):
        """Display a preview of the UI element image"""
        # Clear previous image
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        # Check if image exists
        if not os.path.exists(image_path):
            label = ctk.CTkLabel(self.preview_frame, text="Image not found")
            label.pack(expand=True)
            return
            
        try:
            # Open image using PIL
            from PIL import Image, ImageTk
            
            # Load and resize image for preview
            pil_image = Image.open(image_path)
            
            # Get preview frame dimensions
            frame_width = self.preview_frame.winfo_width()
            frame_height = self.preview_frame.winfo_height()
            
            # If frame hasn't been drawn yet, use default sizes
            if frame_width <= 1:
                frame_width = 300
            if frame_height <= 1:
                frame_height = 200
                
            # Calculate resize dimensions (maintain aspect ratio)
            img_width, img_height = pil_image.size
            ratio = min(frame_width/img_width, frame_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Resize image
            # Use simple resize with no resampling filter
            resized_image = pil_image.resize((new_width, new_height))
            
            # Convert to Tkinter-compatible photo image
            tk_image = ImageTk.PhotoImage(resized_image)
            
            # Create label and display image
            image_label = tk.Label(self.preview_frame, image=tk_image, bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1])
            # Store reference to prevent garbage collection (using a different method)
            setattr(image_label, "_image_keep", tk_image)
            image_label.pack(expand=True)
            
        except Exception as e:
            error_label = ctk.CTkLabel(self.preview_frame, text=f"Error loading image: {str(e)}")
            error_label.pack(expand=True)


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
        
    def toggle_visual_feedback(self, enable=None):
        """Toggle visual feedback mode"""
        if hasattr(self, 'visual_feedback'):
            return super().toggle_visual_feedback(enable)
        else:
            # Fallback for older versions
            return False
        
    def execute_command_sequence(self, commands):
        """Execute a sequence of commands"""
        for command in commands:
            print(f"Executing: {command}")
            if self.command_parser:
                actions = self.command_parser.parse_natural_language_command(command)
                # Ensure actions is a list
                if actions is None:
                    actions = []
            else:
                # Fallback if parser not initialized
                print("Warning: Command parser not initialized")
                return
            
            if not actions:
                print(f"No actions could be parsed from command: {command}")
                continue
                
            for action in actions:
                action_type = action.get('action', '')
                target = action.get('target')
                text = action.get('text')
                
                # Handle special cases for numeric values stored as strings
                kwargs = {}
                for key, value in action.items():
                    if key in ['action', 'target', 'text']:
                        continue
                        
                    if key == 'clicks' and isinstance(value, str):
                        try:
                            kwargs[key] = int(value)
                        except (ValueError, TypeError):
                            kwargs[key] = value
                    elif key == 'duration' and isinstance(value, str):
                        try:
                            kwargs[key] = float(value)
                        except (ValueError, TypeError):
                            kwargs[key] = value
                    else:
                        kwargs[key] = value
                
                # Execute the action
                try:
                    # Convert target to actual UI element if it exists
                    if target and target in self.ui_elements:
                        self.perform_action(action_type, target=target, text=text, **kwargs)
                    else:
                        self.perform_action(action_type, target=target, text=text, **kwargs)
                except Exception as e:
                    print(f"Error executing action: {str(e)}")
                    
                # Add more delay between actions
                import time
                time.sleep(1.0)
            
            # Add delay between commands to allow applications to open
            import time
            time.sleep(2.0)
    
    def click_on_text(self, text, region=None):
        """Find and click on text visible on screen"""
        if self.ocr_utils:
            return self.ocr_utils.click_on_text(text, region)
        else:
            print("Warning: OCR utils not initialized")
            return False
    
    def find_text_on_screen(self, text, region=None):
        """Find text on screen and return its location"""
        if self.ocr_utils:
            return self.ocr_utils.find_text_on_screen(text, region)
        else:
            print("Warning: OCR utils not initialized")
            return None
            
    def get_screen_text_ocr(self, region=None):
        """Extract text from screen using OCR"""
        if self.ocr_utils:
            return self.ocr_utils.get_screen_text_ocr(region)
        else:
            print("Warning: OCR utils not initialized")
            return ""


def main():
    """Main entry point"""
    try:
        # Create the controller
        controller = EnhancedAIVisionController()
        
        # Create and run the GUI
        app = EnhancedAIControllerGUI(controller)
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        # traceback.print_exc() # Removed as per new_code
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 