import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import threading

class CommandsTabManager:
    def __init__(self, parent, controller, gui_controller):
        """Initialize the Commands tab manager"""
        self.controller = controller
        self.gui_controller = gui_controller
        self.parent = parent
        self.setup_tab()
        
    def setup_tab(self):
        """Setup the Commands tab interface"""
        # Main frame
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Command input
        ctk.CTkLabel(main_frame, text="Enter Command:").pack(anchor=tk.W, pady=5)
        self.command_entry = ctk.CTkEntry(main_frame, width=400)
        self.command_entry.pack(fill=tk.X, pady=5)
        
        # Execute button with keyboard binding
        execute_button = ctk.CTkButton(main_frame, text="Execute", command=self.execute_command)
        execute_button.pack(anchor=tk.W, pady=5)
        self.command_entry.bind('<Return>', lambda event: self.execute_command())
        
        # Action history
        ctk.CTkLabel(main_frame, text="Action History:").pack(anchor=tk.W, pady=5)
        
        history_frame = ctk.CTkFrame(main_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.history_text = ctk.CTkTextbox(history_frame, height=150)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for history
        scrollbar = ctk.CTkScrollbar(history_frame, command=self.history_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        # Recent commands section
        ctk.CTkLabel(main_frame, text="Recent Commands:").pack(anchor=tk.W, pady=5)
        
        # Listbox can't be directly replaced with CTk widget, so style it to match CTk theme
        self.recent_commands_list = tk.Listbox(main_frame, height=5, 
                                             bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1],
                                             fg=ctk.ThemeManager.theme["CTkLabel"]["text_color"][1],
                                             selectbackground=ctk.ThemeManager.theme["CTkButton"]["fg_color"][1])
        self.recent_commands_list.pack(fill=tk.X, pady=5)
        
        # Double-click to execute recent command
        self.recent_commands_list.bind('<Double-Button-1>', self.execute_recent_command)
        
        # Control buttons
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(pady=10)
        
        ctk.CTkButton(control_frame, text="Clear History", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(control_frame, text="Clear Recent", 
                  command=self.clear_recent).pack(side=tk.LEFT, padx=5)
        
        # Store recent commands
        self.recent_commands = []
        
        # Make the gui_controller aware of the history_text widget
        self.gui_controller.history_text = self.history_text
        
    def execute_command(self):
        """Execute the command entered by user"""
        command = self.command_entry.get().strip()
        if command:
            try:
                # Start command execution in a separate thread
                threading.Thread(target=self.controller.execute_command_sequence, 
                               args=([command],)).start()
                
                # Add to recent commands if not already there
                if command not in self.recent_commands:
                    self.recent_commands.insert(0, command)
                    # Keep only the last 10 commands
                    if len(self.recent_commands) > 10:
                        self.recent_commands = self.recent_commands[:10]
                    self.update_recent_commands()
                
                self.gui_controller.update_history()
                self.command_entry.delete(0, tk.END)
                
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to execute command: {str(e)}")
    
    def execute_recent_command(self, event):
        """Execute a command from the recent commands list"""
        selection = self.recent_commands_list.curselection()
        if selection:
            command = self.recent_commands_list.get(selection[0])
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command)
            self.execute_command()
    
    def update_recent_commands(self):
        """Update the recent commands list"""
        self.recent_commands_list.delete(0, tk.END)
        for cmd in self.recent_commands:
            self.recent_commands_list.insert(tk.END, cmd)
    
    def clear_history(self):
        """Clear action history"""
        self.controller.action_history.clear()
        self.gui_controller.update_history()
    
    def clear_recent(self):
        """Clear recent commands"""
        self.recent_commands = []
        self.update_recent_commands() 