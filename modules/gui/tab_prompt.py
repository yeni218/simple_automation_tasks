import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import time

class PromptTabManager:
    def __init__(self, parent, controller, gui_controller, ai_manager):
        """Initialize the AI Prompt tab manager"""
        self.controller = controller
        self.gui_controller = gui_controller
        self.ai_manager = ai_manager
        self.parent = parent
        self.generated_commands = []
        self.setup_tab()
        
    def setup_tab(self):
        """Setup the AI Prompt tab interface"""
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # API settings section
        api_frame = ctk.CTkFrame(main_frame)
        api_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkLabel(api_frame, text="API Settings").pack(anchor=tk.W, padx=5, pady=5)
        
        # API endpoint
        endpoint_row = ctk.CTkFrame(api_frame)
        endpoint_row.pack(fill=tk.X, padx=5, pady=5)
        ctk.CTkLabel(endpoint_row, text="API Endpoint:", width=120).pack(side=tk.LEFT, padx=5)
        self.endpoint_entry = ctk.CTkEntry(endpoint_row, width=400)
        self.endpoint_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.endpoint_entry.insert(0, self.controller.api_endpoint)
        
        # API key (optional)
        key_row = ctk.CTkFrame(api_frame)
        key_row.pack(fill=tk.X, padx=5, pady=5)
        ctk.CTkLabel(key_row, text="API Key (optional):", width=120).pack(side=tk.LEFT, padx=5)
        self.api_key_entry = ctk.CTkEntry(key_row, width=400, show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Model selection
        model_row = ctk.CTkFrame(api_frame)
        model_row.pack(fill=tk.X, padx=5, pady=5)
        ctk.CTkLabel(model_row, text="Model:", width=120).pack(side=tk.LEFT, padx=5)
        
        models = ["qwen/qwen3-14b", "phi-3-mini-4k-instruct", "phi-3-medium-4k-instruct", "gpt-4-vision-preview"]
        self.model_var = tk.StringVar(value=self.controller.ai_manager.model_name if hasattr(self.controller, 'ai_manager') and hasattr(self.controller.ai_manager, 'model_name') else "")
        self.model_combo = ctk.CTkComboBox(model_row, values=models, variable=self.model_var, width=250)
        self.model_combo.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(model_row, text="Save Settings", 
                  command=self.save_api_settings).pack(side=tk.RIGHT, padx=5)
        
        # Prompt input section
        prompt_frame = ctk.CTkFrame(main_frame)
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ctk.CTkLabel(prompt_frame, text="Natural Language Prompt").pack(anchor=tk.W, padx=10, pady=5)
        
        self.prompt_text = ctk.CTkTextbox(prompt_frame, height=100)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        example_prompt = "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop"
        self.prompt_text.insert("0.0", example_prompt)
        
        # Buttons
        button_frame = ctk.CTkFrame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ctk.CTkButton(button_frame, text="Process Prompt", 
                  command=self.process_prompt).pack(side=tk.LEFT, padx=5)
                  
        ctk.CTkButton(button_frame, text="Execute Commands", 
                  command=self.execute_prompt_commands).pack(side=tk.LEFT, padx=5)
                  
        ctk.CTkButton(button_frame, text="With Vision", 
                  command=self.process_with_vision).pack(side=tk.LEFT, padx=5)
        
        # Results section
        ctk.CTkLabel(main_frame, text="Generated Commands:").pack(anchor=tk.W, pady=5)
        
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_text = ctk.CTkTextbox(results_frame, height=150)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ctk.CTkScrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
    def save_api_settings(self):
        """Save API settings"""
        endpoint = self.endpoint_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        model = self.model_var.get()
        
        if endpoint:
            self.ai_manager.set_api_endpoint(endpoint)
            self.controller.api_endpoint = endpoint
        
        if api_key:
            self.ai_manager.set_api_key(api_key)
            self.controller.api_key = api_key
        
        if model:
            self.ai_manager.set_model(model)
            self.controller.ai_manager.model_name = model
            
        messagebox.showinfo("Success", "API settings updated")
            
    def process_prompt(self):
        """Process natural language prompt to generate commands"""
        prompt = self.prompt_text.get("0.0", "end").strip()
        
        if not prompt or prompt == "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop":
            messagebox.showerror("Error", "Please enter a prompt")
            return
            
        try:
            self.results_text.delete("0.0", "end")
            self.results_text.insert("0.0", "Processing prompt...\n")
            self.parent.update()
            
            # Process in a separate thread
            def process_thread():
                commands = self.ai_manager.process_prompt(prompt)
                
                # Update UI in main thread
                self.parent.after(0, lambda: self.update_results(commands))
                
            threading.Thread(target=process_thread).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error processing prompt: {str(e)}")
            
    def update_results(self, commands):
        """Update results after processing"""
        self.generated_commands = commands
        
        self.results_text.delete("0.0", "end")
        if commands:
            for cmd in commands:
                self.results_text.insert("end", cmd + "\n")
        else:
            self.results_text.insert("end", "No commands were generated")
            
    def execute_prompt_commands(self):
        """Execute the commands generated from the prompt"""
        if not self.generated_commands:
            messagebox.showerror("Error", "No commands to execute. Process a prompt first.")
            return
            
        if messagebox.askyesno("Confirm", f"Execute {len(self.generated_commands)} commands?"):
            threading.Thread(target=self.controller.execute_command_sequence, 
                           args=(self.generated_commands,)).start()
            
    def process_with_vision(self):
        """Process prompt with screenshot context"""
        prompt = self.prompt_text.get("0.0", "end").strip()
        
        if not prompt or prompt == "Example: Open Notepad, type 'Hello World', save the file as test.txt on the desktop":
            messagebox.showerror("Error", "Please enter a prompt")
            return
            
        # Check if vision-capable model is selected
        model = self.model_var.get()
        if "vision" not in model.lower():
            if not messagebox.askyesno("Model Warning", 
                                     "The current model may not support vision. Continue anyway?"):
                return
            
        try:
            self.results_text.delete("0.0", "end")
            self.results_text.insert("0.0", "Taking screenshot and processing...\n")
            self.parent.update()
            
            # Minimize window to avoid it being in the screenshot
            self.gui_controller.root.iconify()
            time.sleep(1)  # Wait for window to minimize
            
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            screenshot_path = f"screenshot_prompt_{int(time.time())}.png"
            screenshot.save(screenshot_path)
            
            # Process in a separate thread
            def process_thread():
                commands = self.ai_manager.process_with_vision(prompt, screenshot_path)
                
                # Update UI in main thread
                self.gui_controller.root.after(0, lambda: self.update_results_and_restore(commands))
                
            threading.Thread(target=process_thread).start()
                
        except Exception as e:
            # Restore window if error occurs
            self.gui_controller.root.deiconify()
            messagebox.showerror("Error", f"Error processing vision prompt: {str(e)}")
            
    def update_results_and_restore(self, commands):
        """Update results and restore window"""
        self.gui_controller.root.deiconify()
        self.update_results(commands) 