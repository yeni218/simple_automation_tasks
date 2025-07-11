import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkinter import filedialog
import os
import time
import threading

class UIElementDialog:
    """Dialog for adding or editing UI elements"""
    def __init__(self, parent, controller):
        self.controller = controller
        self.result = None
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Add UI Element")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """Setup the dialog interface"""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Element name
        ctk.CTkLabel(main_frame, text="Element Name:").pack(anchor=tk.W, pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=350)
        self.name_entry.pack(fill=tk.X, pady=5)
        
        # Image file
        ctk.CTkLabel(main_frame, text="Image File:").pack(anchor=tk.W, pady=5)
        
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_entry = ctk.CTkEntry(file_frame, width=250)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ctk.CTkButton(file_frame, text="Browse", command=self.browse_file).pack(side=tk.RIGHT, padx=5)
        
        # Action type
        ctk.CTkLabel(main_frame, text="Action Type:").pack(anchor=tk.W, pady=5)
        action_values = ["click", "double_click", "right_click", "type", "scroll"]
        self.action_var = tk.StringVar(value="click")
        self.action_combo = ctk.CTkComboBox(main_frame, values=action_values, variable=self.action_var, width=350)
        self.action_combo.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def browse_file(self):
        """Browse for image file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            
    def ok_clicked(self):
        """Handle OK button click"""
        name = self.name_entry.get().strip()
        file_path = self.file_entry.get().strip()
        action_type = self.action_var.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter an element name")
            return
            
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid image file")
            return
            
        self.controller.save_ui_element(name, file_path, action_type)
        self.result = True
        self.dialog.destroy()
        
    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()


class RecordingDialog:
    """Dialog for recording automation steps"""
    def __init__(self, parent, controller, target_text):
        self.controller = controller
        self.target_text = target_text
        self.is_recording = False
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Record Actions")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        
        self.setup_dialog()
        self.start_recording()
        
    def setup_dialog(self):
        """Setup the dialog interface"""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="Recording started...", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10)
        
        # Instructions
        instructions = (
            "Perform the actions you want to record.\n"
            "All your actions will be tracked and added to the workflow.\n\n"
            "Click 'Stop Recording' when finished."
        )
        
        instruction_text = ctk.CTkTextbox(main_frame, height=80)
        instruction_text.pack(fill=tk.X, pady=10)
        instruction_text.insert("0.0", instructions)
        instruction_text.configure(state="disabled")
        
        # Recorded actions
        ctk.CTkLabel(main_frame, text="Recorded Actions:").pack(anchor=tk.W, pady=5)
        
        self.actions_text = ctk.CTkTextbox(main_frame, height=100)
        self.actions_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.record_btn = ctk.CTkButton(button_frame, text="Stop Recording", command=self.stop_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
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
            current_text = self.target_text.get("0.0", "end").strip()
            if current_text:
                # Append to existing commands
                self.target_text.insert("end", "\n")
            
            for cmd in commands:
                self.target_text.insert("end", cmd + "\n")
        
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
                self.actions_text.delete("0.0", "end")
                for action in self.controller.action_history[-5:]:  # Show last 5 actions
                    self.actions_text.insert("end", action + "\n")
                self.actions_text.see("end")
                
                last_count = current_count
                
            time.sleep(0.5)  # Check every half second 