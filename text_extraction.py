import cv2
import numpy as np
import pyautogui
import pytesseract
# from PIL import Image
# import re

class ScreenTextLocator:
    def __init__(self):
        """Initialize the screen text locator"""
        # Disable pyautogui failsafe for smoother operation
        pyautogui.FAILSAFE = False
        
    def take_screenshot(self):
        """Take a screenshot of the entire screen"""
        screenshot = pyautogui.screenshot()
        # Convert PIL image to OpenCV format
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return screenshot_cv
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get better text recognition
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Optional: Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def extract_text_with_positions(self, image):
        """Extract text and their bounding box coordinates from image"""
        # Get detailed data from tesseract including bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        text_info = []
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            # Filter out empty text and low confidence results
            if int(data['conf'][i]) > 30 and data['text'][i].strip():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                text_info.append({
                    'text': text,
                    'bbox': (x, y, w, h),
                    'confidence': confidence,
                    'center': (x + w//2, y + h//2)
                })
        
        return text_info
    
    def find_text_location(self, target_text, case_sensitive=False, partial_match=True):
        """
        Find the geometric location of specific text on screen
        
        Args:
            target_text (str): Text to search for
            case_sensitive (bool): Whether to perform case-sensitive search
            partial_match (bool): Whether to allow partial matches
            
        Returns:
            list: List of dictionaries containing text matches with their locations
        """
        # Take screenshot
        screenshot = self.take_screenshot()
        
        # Preprocess image
        processed_image = self.preprocess_image(screenshot)
        
        # Extract text with positions
        text_info = self.extract_text_with_positions(processed_image)
        
        # Search for target text
        matches = []
        search_text = target_text if case_sensitive else target_text.lower()
        
        for info in text_info:
            text = info['text'] if case_sensitive else info['text'].lower()
            
            # Check for match
            found = False
            if partial_match:
                found = search_text in text
            else:
                found = search_text == text
            
            if found:
                matches.append({
                    'original_text': info['text'],
                    'bbox': info['bbox'],
                    'center': info['center'],
                    'confidence': info['confidence']
                })
        
        return matches, screenshot
    
    def draw_results(self, image, matches, target_text):
        """Draw bounding boxes around found text"""
        result_image = image.copy()
        
        for match in matches:
            x, y, w, h = match['bbox']
            center_x, center_y = match['center']
            
            # Draw bounding box
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(result_image, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Add text label
            label = f"{match['original_text']} ({match['confidence']}%)"
            cv2.putText(result_image, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return result_image

def main():
    """Main function to demonstrate the screen text locator"""
    locator = ScreenTextLocator()
    
    print("Screen Text Locator")
    print("===================")
    print("This tool will take a screenshot and find the location of text you specify.")
    print("Make sure you have some text visible on your screen before proceeding.\n")
    
    while True:
        try:
            # Get user input
            target_text = input("Enter the text you want to find (or 'quit' to exit): ")
            
            if target_text.lower() == 'quit':
                break
            
            if not target_text.strip():
                print("Please enter some text to search for.")
                continue
            
            # Search options
            case_sensitive = input("Case sensitive search? (y/n, default: n): ").lower() == 'y'
            partial_match = input("Allow partial matches? (y/n, default: y): ").lower() != 'n'
            
            print(f"\nSearching for '{target_text}'...")
            
            # Find text location
            matches, screenshot = locator.find_text_location(
                target_text, 
                case_sensitive=case_sensitive, 
                partial_match=partial_match
            )
            
            if matches:
                print(f"Found {len(matches)} match(es):")
                for i, match in enumerate(matches, 1):
                    x, y, w, h = match['bbox']
                    center_x, center_y = match['center']
                    print(f"  {i}. Text: '{match['original_text']}'")
                    print(f"     Bounding box: x={x}, y={y}, width={w}, height={h}")
                    print(f"     Center point: ({center_x}, {center_y})")
                    print(f"     Confidence: {match['confidence']}%")
                    print()
                
                # Draw results and show image
                result_image = locator.draw_results(screenshot, matches, target_text)
                
                # Display the image with results
                cv2.imshow('Text Location Results', result_image)
                print("Press any key to continue or 'q' to quit...")
                
                key = cv2.waitKey(0) & 0xFF
                cv2.destroyAllWindows()
                
                if key == ord('q'):
                    break
                    
            else:
                print(f"No matches found for '{target_text}'")
                print("Try adjusting your search criteria or make sure the text is visible on screen.")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Please try again.")
    
    cv2.destroyAllWindows()
    print("Thank you for using Screen Text Locator!")

if __name__ == "__main__":
    main()