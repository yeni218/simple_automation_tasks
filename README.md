# AI Vision Controller

A powerful automation tool that uses computer vision and AI to control your PC through natural language commands.

## Features

- **Image Recognition**: Find and interact with UI elements using image templates
- **Natural Language Commands**: Control your PC using simple commands like "click on login button" or "type 'hello world'"
- **OCR Integration**: Recognize text on screen and interact with it
- **Workflow Management**: Create, save, and run sequences of automation commands
- **GPT Integration**: Generate automation commands from natural language prompts
- **Vision Analysis**: Use GPT-4 Vision to analyze screenshots and generate appropriate commands

## Installation

1. Ensure you have Python 3.7+ installed
2. Install Tesseract OCR:
   - Windows: Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - Mac: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Getting Started

1. Run the application:
   ```
   python advanced_automation.py
   ```

2. Adding UI Elements:
   - Go to the "UI Elements" tab
   - Click "Add Element"
   - Enter a name for the element
   - Select an image file that represents the UI element
   - Choose an action type (click, double-click, etc.)

3. Using Natural Language Commands:
   - Go to the "Commands" tab
   - Enter a command like "click on login_button" or "type 'hello world'"
   - Click "Execute"

4. Creating Workflows:
   - Go to the "Workflows" tab
   - Enter a name for your workflow
   - Add commands (one per line) in the editor
   - Click "Save" and then "Run" to execute the workflow

5. Using GPT for Automation:
   - Go to the "GPT Prompt" tab
   - Enter your OpenAI API key and select a model
   - Enter a natural language prompt describing what you want to automate
   - Click "Process Prompt" to generate commands
   - Click "Execute Commands" to run them

## Command Examples

- `click on element_name` - Click on a UI element
- `double-click on element_name` - Double-click on a UI element
- `right-click on element_name` - Right-click on a UI element
- `type "text to enter"` - Type the specified text
- `press enter` - Press a key (enter, tab, esc, etc.)
- `hotkey ctrl+c` - Press a key combination
- `wait 3 seconds` - Wait for the specified time
- `scroll up` or `scroll down` - Scroll the page
- `open notepad` - Open an application

## Advanced Usage

### Using OCR to Find Text

The tool can find and click on text visible on the screen:

```python
controller = AIVisionController()
controller.click_on_text("Login")  # Finds and clicks on "Login" text
```

### Recording Workflows

You can record your actions to create workflows:

1. Go to the "Workflows" tab
2. Click "Record"
3. Perform actions you want to record
4. Click "Stop Recording"

### Using GPT-4 Vision

For advanced automation that adapts to what's on screen:

1. Go to the "GPT Prompt" tab
2. Enter your prompt
3. Click "With Vision"
4. The app will take a screenshot and generate commands based on what it sees

## Troubleshooting

- **UI Element Not Found**: Try increasing the confidence threshold or recreate the element with a clearer image
- **OCR Not Working**: Ensure Tesseract OCR is properly installed and in your PATH
- **GPT Integration Issues**: Verify your API key is correct and you have sufficient credits

## License

This project is licensed under the MIT License - see the LICENSE file for details. 