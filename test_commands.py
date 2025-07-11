import sys
from modules.ai_integration import AIIntegration

# Create a dummy controller
class DummyController:
    def __init__(self):
        pass

# Test the command generation
controller = DummyController()
ai = AIIntegration(controller)

# Test notepad commands
print("=== TESTING NOTEPAD COMMANDS ===")
notepad_commands = ai.get_notepad_commands("open notepad and write hello world")
print("Notepad commands:", notepad_commands)

# Test word commands
print("\n=== TESTING WORD COMMANDS ===")
word_commands = ai.get_word_commands("open word and write hello world")
print("Word commands:", word_commands)

# Test calculator commands
print("\n=== TESTING CALCULATOR COMMANDS ===")
calc_commands = ai.get_calculator_commands("open calculator and add 5+3")
print("Calculator commands:", calc_commands)

# Test AI prompt processing
print("\n=== TESTING AI PROMPT PROCESSING ===")
prompt = "open notepad and write hello world"
print(f"Processing prompt: {prompt}")
commands = ai.extract_valid_commands(f"""
- Open Notepad by pressing Win+R and typing notepad
- Type "Hello, World!" in the notepad window
- Save the file by pressing Ctrl+S
""")
print("Extracted commands:", commands)

# Test with a direct command format
print("\n=== TESTING DIRECT COMMAND FORMAT ===")
direct_commands = ai.extract_valid_commands("""
hotkey win+r
type "notepad"
press enter
wait 2 seconds
type "Hello, World!"
""")
print("Direct commands:", direct_commands)

print("\nTest completed.") 