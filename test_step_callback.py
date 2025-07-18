#!/usr/bin/env python
# Test script for step callback functionality

import sys
import os
import time
from PIL import Image
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

# Add modules directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
try:
    from modules.ai_vision_controller import EnhancedAIVisionController
    from modules.ai_integration import AIIntegration
except ImportError as e:
    print(f"Error importing modules: {str(e)}")
    sys.exit(1)

class TestApp:
    """Simple test application for step callback functionality"""
    
    def __init__(self):
        """Initialize the test application"""
        self.root = ctk.CTk()
        self.root.title("Step Callback Test")
        self.root.geometry("800x600")
        
        # Create controller
        self.controller = EnhancedAIVisionController()
        self.ai_manager = AIIntegration(self.controller)
        self.controller.ai_manager = self.ai_manager
        
        # Set step callback
        self.controller.set_step_callback(self.on_step_screenshot)
        
        # Create UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for testing"""
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Test controls
        controls_frame = ctk.CTkFrame(frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkButton(controls_frame, text="Take Screenshot", 
                     command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(controls_frame, text="Test Step Callback", 
                     command=self.test_step_callback).pack(side=tk.LEFT, padx=5)
        
        # Step display
        ctk.CTkLabel(frame, text="Step Cards:").pack(anchor=tk.W)
        
        self.steps_container = ctk.CTkScrollableFrame(frame, height=400)
        self.steps_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.step_cards = []
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ctk.CTkLabel(frame, textvariable=self.status_var).pack(anchor=tk.W, pady=5)
        
    def take_screenshot(self):
        """Take a screenshot for testing"""
        self.root.withdraw()
        time.sleep(0.5)
        
        try:
            # Take screenshot
            screenshot = self.controller.take_screenshot()
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"test_screenshot_{timestamp}.png"
            
            # Save screenshot
            screenshot.save(filename)
            
            self.status_var.set(f"Screenshot saved to {filename}")
            self.screenshot_path = filename
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            
        finally:
            self.root.deiconify()
            
    def test_step_callback(self):
        """Test the step callback functionality"""
        if not hasattr(self, 'screenshot_path'):
            messagebox.showwarning("No Screenshot", "Please take a screenshot first")
            return
            
        # Simulate steps
        for i in range(1, 4):
            description = f"Test step {i}"
            self.controller.step_counter = i
            
            # Capture step screenshot
            step_path = os.path.join(self.controller.session_dir, f"step_{i:03d}_test.png")
            
            # Copy the test screenshot to the step path
            Image.open(self.screenshot_path).save(step_path)
            
            # Call the step callback directly
            self.controller.on_step_screenshot(i, description, step_path)
            
            # Wait a bit between steps
            time.sleep(0.5)
            
        self.status_var.set(f"Test completed with {3} steps")
            
    def on_step_screenshot(self, step_num, description, image_path):
        """Callback for step screenshots"""
        print(f"Step callback received: {step_num} - {description} - {image_path}")
        
        # Create a step card
        self.add_step_card(step_num, description, image_path)
        
    def add_step_card(self, step_num, description, image_path):
        """Add a step card to the UI"""
        try:
            # Create a frame for this card
            card_frame = ctk.CTkFrame(self.steps_container)
            card_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
            
            # Header with step number and description
            header_frame = ctk.CTkFrame(card_frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)
            
            step_label = ctk.CTkLabel(header_frame, text=f"Step {step_num}:", width=60)
            step_label.pack(side=tk.LEFT, padx=5)
            
            desc_label = ctk.CTkLabel(header_frame, text=description, anchor="w")
            desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Image (if available)
            if image_path and os.path.exists(image_path):
                image_frame = ctk.CTkFrame(card_frame)
                image_frame.pack(fill=tk.X, padx=5, pady=5)
                
                try:
                    # Load and resize image
                    img = Image.open(image_path)
                    img.thumbnail((300, 200))
                    photo_img = ctk.CTkImage(light_image=img, size=(300, 200))
                    
                    # Create label with image
                    img_label = ctk.CTkLabel(image_frame, image=photo_img, text="")
                    img_label.pack(pady=5)
                    
                except Exception as e:
                    error_label = ctk.CTkLabel(image_frame, text=f"Error loading image: {str(e)}")
                    error_label.pack(pady=5)
            
            # Store reference to card
            self.step_cards.append({
                'frame': card_frame,
                'step_num': step_num,
                'description': description,
                'image_path': image_path
            })
            
            # Update UI
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error creating step card: {str(e)}")
            
    def run(self):
        """Run the test application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = TestApp()
    app.run()
    
if __name__ == "__main__":
    main() 