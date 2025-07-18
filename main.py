#!/usr/bin/env python
# AI Vision Controller - Main application

import sys
import os
import json
import time  # Add time import
import datetime  # Add datetime import
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
import threading
import tkinter.ttk as ttk
from PIL import Image, ImageTk  # Add PIL imports
import pyautogui  # Add pyautogui import

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
        
        # IMPORTANT NOTICE at the top
        notice_frame = ctk.CTkFrame(ai_frame, fg_color="#ffcc00")
        notice_frame.pack(fill=tk.X, pady=(0, 10))
        
        notice_label = ctk.CTkLabel(
            notice_frame,
            text="⚠️ IMPORTANT: AI will analyze each step during automation ⚠️\n"
                 "Step-by-step results will appear below",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#000000"
        )
        notice_label.pack(pady=10)
        
        # Create main content frame with two columns
        content_frame = ctk.CTkFrame(ai_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left column - Screenshot preview and controls
        left_column = ctk.CTkFrame(content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Screenshot preview panel
        preview_frame = ctk.CTkFrame(left_column)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        preview_label = ctk.CTkLabel(
            preview_frame, 
            text="Current Context Screenshot:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        preview_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Screenshot container with border
        screenshot_container = ctk.CTkFrame(preview_frame, border_width=1, border_color="#AAAAAA")
        screenshot_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.screenshot_preview_label = ctk.CTkLabel(screenshot_container, text="No screenshot yet")
        self.screenshot_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.screenshot_preview_image = None  # To hold the PhotoImage reference
        
        # Navigation for step-by-step screenshots
        nav_frame = ctk.CTkFrame(preview_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.screenshot_list = []
        self.screenshot_index = tk.IntVar(value=0)
        
        self.prev_btn = ctk.CTkButton(nav_frame, text="< Prev", command=self.show_prev_screenshot, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.next_btn = ctk.CTkButton(nav_frame, text="Next >", command=self.show_next_screenshot, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        self.screenshot_counter_label = ctk.CTkLabel(nav_frame, text="")
        self.screenshot_counter_label.pack(side=tk.LEFT, padx=5)
        
        # Take screenshot button
        screenshot_btn = ctk.CTkButton(
            left_column, 
            text="📷 Take Screenshot",
            height=40,
            command=self.take_screenshot_for_ai
        )
        screenshot_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Right column - Instructions and controls
        right_column = ctk.CTkFrame(content_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Instructions label
        ctk.CTkLabel(right_column, text="Enter natural language instructions for automation:").pack(anchor=tk.W, pady=(0, 5))
        
        # Text area for instructions - smaller height
        self.ai_instructions = ctk.CTkTextbox(right_column, height=150)
        self.ai_instructions.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        # Example instructions
        examples = [
            "Open Notepad and type 'Hello, world!'",
            "Open Calculator, click on 5, then +, then 3, then ="
        ]
        example_text = "Examples:\n" + "\n".join(f"• {ex}" for ex in examples)
        ctk.CTkLabel(right_column, text=example_text, text_color="gray").pack(anchor=tk.W, pady=(0, 10))
        
        # AI Engine selection
        engine_frame = ctk.CTkFrame(right_column)
        engine_frame.pack(fill=tk.X, pady=(0, 10))
        
        ctk.CTkLabel(engine_frame, text="AI Engine:", width=80).pack(side=tk.LEFT, padx=5)
        
        # Dropdown for AI model selection
        ai_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"]
        self.ai_model_var = tk.StringVar(value=ai_models[0])
        ai_model_dropdown = ctk.CTkComboBox(
            engine_frame,
            values=ai_models,
            variable=self.ai_model_var,
            width=200
        )
        ai_model_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ctk.CTkFrame(right_column)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Visual feedback option
        self.visual_feedback_var = tk.BooleanVar(value=True)
        visual_feedback_cb = ctk.CTkCheckBox(
            options_frame,
            text="Show visual feedback",
            variable=self.visual_feedback_var,
            command=self.toggle_visual_feedback
        )
        visual_feedback_cb.pack(side=tk.LEFT, padx=5)
        
        # Speed slider
        speed_frame = ctk.CTkFrame(right_column)
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        ctk.CTkLabel(speed_frame, text="Speed:", width=60).pack(side=tk.LEFT, padx=5)
        
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
        
        # Execute button - make it more prominent
        execute_btn = ctk.CTkButton(
            right_column, 
            text="▶️ Execute Instructions",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",  # Green color
            hover_color="#218838",  # Darker green on hover
            height=40,
            command=self.execute_ai_instructions
        )
        execute_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Create workflow button
        create_workflow_btn = ctk.CTkButton(
            right_column, 
            text="💾 Create Workflow",
            height=30,
            command=self.create_workflow_from_ai
        )
        create_workflow_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Step cards frame
        self.step_cards_frame = ctk.CTkFrame(ai_frame, border_width=1)
        self.step_cards_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Header for step cards with more prominent styling
        header_label = ctk.CTkLabel(
            self.step_cards_frame, 
            text="Execution Steps:", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Scrollable frame for step cards with increased height
        self.steps_container = ctk.CTkScrollableFrame(self.step_cards_frame, height=200)
        self.steps_container.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Add an initial message in the steps container
        initial_msg = ctk.CTkLabel(
            self.steps_container,
            text="Steps will appear here during execution...",
            text_color="gray"
        )
        initial_msg.pack(pady=10)
        self.initial_step_msg = initial_msg  # Store reference to remove it later
        
        # Results frame
        results_frame = ctk.CTkFrame(ai_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        results_header = ctk.CTkLabel(
            results_frame, 
            text="Execution Results:", 
            font=ctk.CTkFont(weight="bold")
        )
        results_header.pack(anchor=tk.W, padx=5, pady=5)
        
        # Results text area
        self.ai_results = ctk.CTkTextbox(results_frame, height=150)
        self.ai_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Screenshot path variable and label
        self.screenshot_path = tk.StringVar()
        self.screenshot_path.set("")
        ctk.CTkLabel(ai_frame, textvariable=self.screenshot_path, text_color="gray").pack(anchor=tk.W, pady=(5, 0))
        
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
                    self.start_x = 0.0  # Initialize with default values
                    self.start_y = 0.0  # Initialize with default values
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
                    self.start_x = float(self.canvas.canvasx(event.x))
                    self.start_y = float(self.canvas.canvasy(event.y))
                    
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
                        cur_x = float(self.canvas.canvasx(event.x))
                        cur_y = float(self.canvas.canvasy(event.y))
                        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
                        
                def on_mouse_up(self, event):
                    """Handle mouse button up event"""
                    end_x = float(self.canvas.canvasx(event.x))
                    end_y = float(self.canvas.canvasy(event.y))
                    
                    # Calculate rectangle coordinates - ensure we have valid values
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
        
        # Clear previous step cards
        self.clear_step_cards()
        
        # Connect step callback to controller - CRITICAL for visual feedback
        if hasattr(self.controller, 'set_step_callback'):
            self.controller.set_step_callback(self.on_step_screenshot_callback)
            print("Connected step callback to controller")
        else:
            print("Warning: Controller does not have set_step_callback method")
        
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
                
                # Update the model in AI manager based on user selection if available
                if hasattr(self, 'ai_model_var'):
                    selected_model = self.ai_model_var.get()
                    self.ai_manager.model_name = selected_model
                    self.ai_results.insert("end", f"Using {selected_model} for visual analysis...\n")
                    # Reconfigure the API with the new model
                    if hasattr(self.ai_manager, 'configure_api'):
                        self.ai_manager.configure_api()
                        self.ai_results.insert("end", "Reconfigured API with selected model\n")
                
                # First, detect UI elements in the screenshot to ensure AI can see what's on screen
                self.ai_results.insert("end", "Detecting UI elements in screenshot...\n")
                ui_elements = self.ai_manager.detect_ui_elements(screenshot)
                
                if ui_elements and len(ui_elements) > 0:
                    self.ai_results.insert("end", f"✓ Found {len(ui_elements)} UI elements\n")
                    
                    # Create an annotated screenshot
                    annotated_path = self.ai_manager.annotate_detected_ui_elements(screenshot)
                    if annotated_path:
                        # Display the annotated screenshot
                        self.update_screenshot_preview(annotated_path)
                        self.ai_results.insert("end", f"UI elements annotated in preview\n")
                else:
                    self.ai_results.insert("end", "No UI elements detected in screenshot. This may cause issues.\n")
                
                # Execute the instructions with visual context
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
                self.ai_results.insert("end", "No screenshot provided. Taking one now for context...\n")
                
                # Take a screenshot automatically if none exists
                new_screenshot = self.take_screenshot_for_ai()
                if new_screenshot and os.path.exists(new_screenshot):
                    self.ai_results.insert("end", f"Using new screenshot: {new_screenshot}\n")
                    success = self.ai_manager.execute_vision_instructions(instructions, new_screenshot)
                else:
                    # Fall back to text-only if screenshot fails
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
                
                # If success is a string, it might be the path to the session directory
                if isinstance(success, str) and os.path.exists(success):
                    self.ai_results.insert("end", f"Execution logs saved to: {success}\n")
                
                # Update screenshot list for navigation
                self.screenshot_list = []
                for root, dirs, files in os.walk(success):
                    for file in files:
                        if file.endswith(".png"):
                            self.screenshot_list.append(os.path.join(root, file))
                    
                    # Sort screenshots by name (which includes step number)
                    self.screenshot_list.sort()
                    
                    # Update navigation
                    if self.screenshot_list:
                        self.screenshot_index.set(0)
                        self.update_screenshot_preview(self.screenshot_list[0])
                self.update_screenshot_counter()
                self.prev_btn.configure(state=tk.DISABLED)
                self.next_btn.configure(state=tk.NORMAL if len(self.screenshot_list) > 1 else tk.DISABLED)
            else:
                self.ai_results.insert("end", "✗ Failed to execute instructions\n")
                self.ai_results.insert("end", "\nTo ensure AI automation works correctly:\n")
                self.ai_results.insert("end", "1. Check that your local LLM server is running\n")
                self.ai_results.insert("end", "2. Verify the API endpoint in the AI Prompt tab\n")
                self.ai_results.insert("end", "3. Try using more specific instructions\n")
                self.ai_results.insert("end", "4. Use the screenshot feature for context\n")
                
        except Exception as e:
            self.ai_results.insert("end", f"✗ Error during execution: {str(e)}\n")
            import traceback
            traceback_info = traceback.format_exc()
            self.ai_results.insert("end", f"Traceback:\n{traceback_info}\n")
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
            
            return filename # Return the path for use in execute_ai_instructions
            
        except Exception as e:
            messagebox.showerror("Screenshot Error", f"Failed to take screenshot: {str(e)}")
            return None
        finally:
            # Always show the application window again
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

    def show_prev_screenshot(self):
        """Show previous screenshot in the navigation"""
        if self.screenshot_list and self.screenshot_index.get() > 0:
            self.screenshot_index.set(self.screenshot_index.get() - 1)
            self.update_screenshot_preview(self.screenshot_list[self.screenshot_index.get()])
            self.update_screenshot_counter()
            
            # Enable/disable navigation buttons
            self.next_btn.configure(state=tk.NORMAL)
            if self.screenshot_index.get() == 0:
                self.prev_btn.configure(state=tk.DISABLED)

    def show_next_screenshot(self):
        """Show next screenshot in the navigation"""
        if self.screenshot_list and self.screenshot_index.get() < len(self.screenshot_list) - 1:
            self.screenshot_index.set(self.screenshot_index.get() + 1)
            self.update_screenshot_preview(self.screenshot_list[self.screenshot_index.get()])
            self.update_screenshot_counter()
            
            # Enable/disable navigation buttons
            self.prev_btn.configure(state=tk.NORMAL)
            if self.screenshot_index.get() == len(self.screenshot_list) - 1:
                self.next_btn.configure(state=tk.DISABLED)

    def update_screenshot_counter(self):
        """Update the screenshot counter label"""
        if self.screenshot_list:
            self.screenshot_counter_label.configure(text=f"{self.screenshot_index.get() + 1} / {len(self.screenshot_list)}")
        else:
            self.screenshot_counter_label.configure(text="")
            
    def update_screenshot_preview(self, image_path):
        """Update the screenshot preview with the given image"""
        import os
        from PIL import Image, ImageTk
        
        if not image_path or not os.path.exists(image_path):
            self.screenshot_preview_label.configure(text="No screenshot available", image=None)
            self.screenshot_preview_image = None
            return
            
        try:
            # Load and resize the image
            img = Image.open(image_path)
            img.thumbnail((400, 250))  # Resize to fit in preview area
            self.screenshot_preview_image = ImageTk.PhotoImage(img)
            self.screenshot_preview_label.configure(image=self.screenshot_preview_image, text="")
        except Exception as e:
            self.screenshot_preview_label.configure(text=f"Error loading image: {str(e)}", image=None)
            self.screenshot_preview_image = None
            
    def add_step_card(self, step_num, description, image_path):
        """Add a new step card with screenshot to the UI
        
        Args:
            step_num: Step number
            description: Description of the step
            image_path: Path to the step screenshot
        """
        try:
            # Remove the initial message on first card
            if hasattr(self, 'initial_step_msg') and self.initial_step_msg is not None:
                self.initial_step_msg.destroy()
                self.initial_step_msg = None
                
            print(f"Adding step card: {step_num} - {description} - {image_path}")
            
            # Create a frame for this step card
            card_frame = ctk.CTkFrame(self.steps_container)
            card_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
            
            # Step header with number and description
            header_frame = ctk.CTkFrame(card_frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Check if this is an AI analysis result (contains a status indicator)
            is_ai_analysis = " - " in description and any(indicator in description.lower() for indicator in ["success", "failed", "error", "not found"])
            
            step_label = ctk.CTkLabel(header_frame, text=f"Step {step_num}:", width=60)
            step_label.pack(side=tk.LEFT, padx=5)
            
            # If this is an AI analysis, format it nicely with status indicator
            if is_ai_analysis:
                # Split description into action and analysis
                parts = description.split(" - ", 1)
                action = parts[0]
                analysis = parts[1] if len(parts) > 1 else ""
                
                # Determine status color based on text
                status_color = "#00CC00"  # Default green for success
                if any(word in analysis.lower() for word in ["failed", "error", "not found"]):
                    status_color = "#FF3300"  # Red for failure
                elif any(word in analysis.lower() for word in ["trying", "searching"]):
                    status_color = "#FFCC00"  # Yellow for in-progress
                
                # Create action label
                action_label = ctk.CTkLabel(header_frame, text=action, anchor="w")
                action_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                
                # Create analysis frame
                analysis_frame = ctk.CTkFrame(card_frame)
                analysis_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
                
                # Add AI icon and analysis text
                ai_label = ctk.CTkLabel(analysis_frame, text="🤖", width=20)
                ai_label.pack(side=tk.LEFT, padx=(5, 0))
                
                analysis_text = ctk.CTkLabel(
                    analysis_frame, 
                    text=analysis,
                    text_color=status_color,
                    anchor="w"
                )
                analysis_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            else:
                # Regular description without special formatting
                desc_label = ctk.CTkLabel(header_frame, text=description, anchor="w")
                desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Image frame (if image path is provided)
            if image_path and os.path.exists(image_path):
                image_frame = ctk.CTkFrame(card_frame)
                image_frame.pack(fill=tk.X, padx=5, pady=5)
                
                try:
                    # Load and resize the image
                    img = Image.open(image_path)
                    img.thumbnail((300, 200))  # Resize image to fit in card
                    photo_img = ImageTk.PhotoImage(img)
                    
                    # Create label with image
                    img_label = tk.Label(
                        image_frame, 
                        image=photo_img,
                        bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]
                    )
                    # Store reference to prevent garbage collection
                    # We need to store it in a way the linter won't complain about
                    setattr(img_label, "_image_keep", photo_img)
                    img_label.pack(pady=5)
                except Exception as e:
                    # If image loading fails, show error text
                    error_label = ctk.CTkLabel(image_frame, text=f"Error loading image: {str(e)}")
                    error_label.pack(pady=5)
            
            # Add the card to our list for reference
            if not hasattr(self, 'step_cards'):
                self.step_cards = []
                
            self.step_cards.append({
                'frame': card_frame,
                'step_num': step_num,
                'description': description,
                'image_path': image_path
            })
            
            # Make sure the UI updates
            self.root.update_idletasks()
            
            return card_frame
            
        except Exception as e:
            print(f"Error creating step card: {str(e)}")
            return None
            
    def clear_step_cards(self):
        """Clear all step cards from the UI"""
        if hasattr(self, 'step_cards'):
            for card in self.step_cards:
                if card.get('frame'):
                    card['frame'].destroy()
            self.step_cards = []
            
        # Restore the initial message
        if not hasattr(self, 'initial_step_msg') or self.initial_step_msg is None:
            self.initial_step_msg = ctk.CTkLabel(
                self.steps_container,
                text="Steps will appear here during execution...",
                text_color="gray"
            )
            self.initial_step_msg.pack(pady=10)
            
    def create_workflow_from_ai(self):
        """Create a workflow from the current AI instructions"""
        instructions = self.ai_instructions.get("0.0", "end").strip()
        if not instructions:
            messagebox.showwarning("Empty Instructions", "Please enter instructions for automation")
            return
            
        # Get commands from AI manager if available
        if hasattr(self.ai_manager, 'last_commands') and self.ai_manager.last_commands:
            commands = self.ai_manager.last_commands
            
            # Ask for workflow name
            from tkinter import simpledialog
            workflow_name = simpledialog.askstring(
                "Workflow Name", 
                "Enter a name for this workflow:",
                initialvalue="ai_workflow"
            )
            
            if workflow_name:
                # Create the workflow
                self.workflow_manager.create_workflow(workflow_name, commands)
                messagebox.showinfo("Workflow Created", f"Workflow '{workflow_name}' created successfully")
                
                # Update the workflow list if we're on that tab
                self.update_workflow_list()
        else:
            messagebox.showwarning("No Commands", "No commands available to create workflow")
            
    def on_step_screenshot_callback(self, step_num, description, image_path):
        """Callback for step screenshots to add step cards
        
        Args:
            step_num: Step number
            description: Description of the step
            image_path: Path to the screenshot image
        """
        print(f"Step callback received: {step_num} - {description} - {image_path}")
        
        # This needs to be run in the main thread since it updates the UI
        self.root.after(0, lambda: self.add_step_card(step_num, description, image_path))
        
        # Update the current preview
        self.root.after(0, lambda: self.update_screenshot_preview(image_path))
        
        # Make sure the UI updates
        self.root.update_idletasks()


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
        if screen_text and text.lower() in screen_text.lower():
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