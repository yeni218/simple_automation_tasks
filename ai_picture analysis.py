import os
import tkinter as tk
from tkinter import filedialog
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def setup_api_key():
    """Securely configure the API key from environment variables."""
    try:
        # NOTE: Make sure you have set your GOOGLE_API_KEY in your terminal!
        # PowerShell: $env:GOOGLE_API_KEY = "YOUR_API_KEY"
        # CMD: set GOOGLE_API_KEY=YOUR_API_KEY
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    except KeyError:
        print("--- CRITICAL ERROR ---")
        print("The GOOGLE_API_KEY environment variable was not found.")
        print("Please set the key in your terminal before running the script.")
        return False
    return True

def get_image_path_with_gui():
    """Opens a file dialog window for the user to select an image."""
    # Create a hidden root window
    root = tk.Tk()
    root.withdraw() # Hide the main window

    # Open the file dialog
    filepath = filedialog.askopenfilename(
        title="Select an Image File",
        filetypes=[
            ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("All files", "*.*")
        ]
    )
    
    return filepath # Returns the full path of the selected file, or "" if canceled

def analyze_image(model_name, image_path, prompt):
    """Analyzes an image using the specified Gemini model."""
    if not image_path:
        print("[*] No file was selected. Exiting program.")
        return

    print(f"\n[*] Using model: {model_name}")
    print(f"[*] Loading selected image: {image_path}")

    # Initialize the Generative Model
    model = genai.GenerativeModel(model_name)
    uploaded_file = None
    try:
        # Prepare the image for the API
        uploaded_file = genai.upload_file(path=image_path)
        print(f"[*] Successfully uploaded file: {uploaded_file.display_name}")

        # Send the prompt and image to the model
        print("[*] Generating content... (This may take a moment)")
        response = model.generate_content(
            [prompt, uploaded_file],
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Print the model's response
        print("\n--- Gemini Analysis ---")
        print(response.text)
        print("--- End of Analysis ---\n")

    except Exception as e:
        print(f"\n--- An error occurred during the API call ---")
        print(e)
    finally:
        # IMPORTANT: Clean up the uploaded file from Google's servers
        if uploaded_file:
            genai.delete_file(uploaded_file.name)
            print("[*] Cloud file resource cleaned up.")

# --- Main Program Execution ---
if __name__ == "__main__":
    if setup_api_key():
        # --- Configuration ---
        MODEL_NAME = "gemini-2.5-flash"
        PROMPT = "Analyze this image in extreme detail. Describe everything you see: objects, people (including their expressions and apparent actions), the environment, colors, textures, and any text. Infer the context, the potential story, and the overall mood of the scene."
        
        # --- Run the Analysis ---
        # This will now pop up the file window first
        user_image_path = get_image_path_with_gui()
        
        # The rest of the script will only run if a file was actually chosen
        analyze_image(MODEL_NAME, user_image_path, PROMPT)