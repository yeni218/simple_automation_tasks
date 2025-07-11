import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import pyautogui
import traceback
import difflib

class OCRUtils:
    def __init__(self, controller):
        """Initialize OCR utilities with a reference to the controller"""
        self.controller = controller
        
    def get_screen_text_ocr(self, region=None) -> str:
        """Extract text from screen using OCR (requires pytesseract)"""
        try:
            import pytesseract
            
            screenshot = self.controller.take_screenshot(region=region)
            
            # Preprocess the image for better OCR results
            # Convert to grayscale
            grayscale = screenshot.convert('L')
            
            # Apply threshold to make text more visible
            threshold = 150
            # Use correct syntax for point transformation
            processed_image = grayscale.point(lambda p: 0 if p < threshold else 255)
            
            # Optional: Resize for better OCR (can help with small text)
            # scale = 2.0
            # width, height = processed_image.size
            # processed_image = processed_image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
            
            # Perform OCR
            config = '--psm 6'  # Assume a single block of text
            text = pytesseract.image_to_string(processed_image, config=config)
            
            return text.strip()
        except ImportError:
            print("pytesseract not installed. Install with: pip install pytesseract")
            print("You also need to install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
            return ""
        except Exception as e:
            print(f"OCR error: {str(e)}")
            traceback.print_exc()
            return ""
            
    def find_text_on_screen(self, text: str, region=None) -> Optional[Tuple[int, int]]:
        """Find text on screen and return its location using OCR"""
        try:
            import pytesseract
            
            screenshot = self.controller.take_screenshot(region=region)
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to make text more visible
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Use pytesseract to get word boxes
            custom_config = r'--oem 3 --psm 11'
            data = pytesseract.image_to_data(binary, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Search for the target text
            target_text = text.lower()
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                word = data['text'][i].lower().strip()
                
                # Check if this word matches or contains the target text
                if word and (word == target_text or target_text in word):
                    # Get box coordinates
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    # Calculate center of the word
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # If region was provided, adjust coordinates
                    if region:
                        center_x += region[0]
                        center_y += region[1]
                        
                    print(f"Found text '{text}' at ({center_x}, {center_y})")
                    return (center_x, center_y)
                    
                # Also check for consecutive words that form the target
                if i < n_boxes - 1:
                    two_words = f"{word} {data['text'][i+1].lower().strip()}"
                    if two_words == target_text or target_text in two_words:
                        # Calculate center between two words
                        x1 = data['left'][i]
                        x2 = data['left'][i+1] + data['width'][i+1]
                        y1 = data['top'][i] + data['height'][i] // 2
                        y2 = data['top'][i+1] + data['height'][i+1] // 2
                        
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        # If region was provided, adjust coordinates
                        if region:
                            center_x += region[0]
                            center_y += region[1]
                            
                        print(f"Found text '{text}' at ({center_x}, {center_y})")
                        return (center_x, center_y)
                        
            # If text is not found directly, check for partial matches
            best_match = None
            best_ratio = 0
            
            for i in range(n_boxes):
                word = data['text'][i].lower().strip()
                if len(word) >= 3:  # Ignore very short words
                    # Calculate similarity ratio
                    ratio = difflib.SequenceMatcher(None, word, target_text).ratio()
                    
                    if ratio > 0.7 and ratio > best_ratio:  # At least 70% similar
                        best_match = i
                        best_ratio = ratio
            
            if best_match is not None:
                x = data['left'][best_match]
                y = data['top'][best_match]
                w = data['width'][best_match]
                h = data['height'][best_match]
                
                center_x = x + w // 2
                center_y = y + h // 2
                
                # If region was provided, adjust coordinates
                if region:
                    center_x += region[0]
                    center_y += region[1]
                    
                print(f"Found closest match for '{text}' at ({center_x}, {center_y}) with {best_ratio:.2f} confidence")
                return (center_x, center_y)
            
            print(f"Text '{text}' not found on screen")
            return None
            
        except ImportError:
            print("Required libraries not installed. Install with: pip install pytesseract opencv-python")
            return None
        except Exception as e:
            print(f"Error finding text: {str(e)}")
            traceback.print_exc()
            return None
            
    def click_on_text(self, text: str, region=None) -> bool:
        """Find and click on text visible on screen"""
        text_pos = self.find_text_on_screen(text, region)
        if text_pos:
            pyautogui.click(text_pos[0], text_pos[1])
            self.controller.log_action(f"Clicked on text '{text}' at {text_pos}")
            return True
        else:
            print(f"Could not find text '{text}' to click on")
            return False 