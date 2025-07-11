import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys

class AIControllerGUI:
    """Base GUI controller class"""
    
    def __init__(self, controller):
        """Initialize the GUI controller"""
        self.controller = controller
        self.root = ctk.CTk()
        self.root.title("AI Vision Controller")
        self.root.geometry("800x600")
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI - to be implemented by subclasses"""
        pass
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Take Screenshot", command=self.take_screenshot)
        tools_menu.add_command(label="OCR Test", command=self.ocr_test)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
    def save_config(self):
        """Save configuration to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration"
        )
        if filename:
            self.controller.save_all_data(filename)
            
    def load_config(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        if filename:
            self.controller.load_all_data(filename)
            # Update UI elements list
            self.update_ui_elements_list()
            
    def take_screenshot(self):
        """Take a screenshot"""
        # Hide the window temporarily
        self.root.withdraw()
        
        try:
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            
            # Show the window again
            self.root.deiconify()
            
            # Save dialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Save Screenshot"
            )
            
            if filename:
                screenshot.save(filename)
                messagebox.showinfo("Success", f"Screenshot saved to {filename}")
                
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", f"Failed to take screenshot: {str(e)}")
            
    def ocr_test(self):
        """Test OCR functionality"""
        # Hide the window temporarily
        self.root.withdraw()
        
        try:
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            
            # Show the window again
            self.root.deiconify()
            
            # Perform OCR
            if hasattr(self.controller, 'ocr_utils'):
                text = self.controller.ocr_utils.extract_text_from_image(screenshot)
                if text:
                    # Show OCR results
                    result_window = ctk.CTkToplevel(self.root)
                    result_window.title("OCR Results")
                    result_window.geometry("400x300")
                    
                    text_widget = ctk.CTkTextbox(result_window)
                    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_widget.insert("0.0", text)
                else:
                    messagebox.showinfo("OCR Results", "No text detected in the screenshot")
            else:
                messagebox.showerror("Error", "OCR utils not initialized")
                
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", f"OCR test failed: {str(e)}")
            
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About AI Vision Controller",
            "AI Vision Controller\n\n"
            "A tool for automating UI interactions using computer vision and AI.\n\n"
            "Version 1.0"
        )
        
    def run(self):
        """Run the GUI application"""
        self.root.mainloop() 