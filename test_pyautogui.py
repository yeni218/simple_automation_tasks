import pyautogui
import time

def test_basic_functions():
    """Test basic PyAutoGUI functions"""
    # Print screen size
    print(f"Screen size: {pyautogui.size()}")
    
    # Current mouse position
    print(f"Current mouse position: {pyautogui.position()}")
    
    # Wait for user to prepare
    print("Get ready for automation test in 3 seconds...")
    time.sleep(3)
    
    # Move the mouse to coordinates
    print("Moving mouse to position (100, 100)")
    pyautogui.moveTo(100, 100, duration=1)
    time.sleep(1)
    
    # Move the mouse to another position
    print("Moving mouse to position (400, 300)")
    pyautogui.moveTo(400, 300, duration=1)
    time.sleep(1)
    
    # Press Win+R to open Run dialog
    print("Opening Run dialog with Win+R")
    pyautogui.hotkey('win', 'r')
    time.sleep(1)
    
    # Type notepad
    print("Typing 'notepad'")
    pyautogui.typewrite('notepad')
    time.sleep(1)
    
    # Press Enter
    print("Pressing Enter")
    pyautogui.press('enter')
    time.sleep(2)
    
    # Type some text
    print("Typing text in Notepad")
    pyautogui.typewrite('This is a PyAutoGUI test')
    time.sleep(2)
    
    # Close with Alt+F4
    print("Closing with Alt+F4")
    pyautogui.hotkey('alt', 'f4')
    time.sleep(1)
    
    # Press N to not save
    print("Pressing N to not save")
    pyautogui.press('n')
    
    print("Test completed!")

if __name__ == "__main__":
    test_basic_functions() 