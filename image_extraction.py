import cv2
import numpy as np
import pyautogui
from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog, messagebox

class ScreenImageLocator:
    def __init__(self):
        """Initialize the screen image locator"""
        # Disable pyautogui failsafe for smoother operation
        pyautogui.FAILSAFE = False
        
    def take_screenshot(self):
        """Take a screenshot of the entire screen"""
        screenshot = pyautogui.screenshot()
        # Convert PIL image to OpenCV format
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return screenshot_cv
    
    def load_template_image(self, image_path):
        """Load and validate template image"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load template image
        template = cv2.imread(image_path)
        if template is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        return template
    
    def find_image_matches(self, screenshot, template, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
        """
        Find matches of template image in screenshot using template matching
        
        Args:
            screenshot: Screenshot image (BGR format)
            template: Template image to find (BGR format)
            threshold: Matching threshold (0.0 to 1.0)
            method: OpenCV template matching method
            
        Returns:
            list: List of match locations with confidence scores
        """
        # Convert to grayscale for template matching
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Get template dimensions
        template_height, template_width = template_gray.shape
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot_gray, template_gray, method)
        
        # Find all matches above threshold
        locations = np.where(result >= threshold)
        matches = []
        
        # Group nearby matches to avoid duplicates
        for pt in zip(*locations[::-1]):
            x, y = pt
            confidence = result[y, x]
            
            # Check if this match is too close to an existing match
            is_duplicate = False
            for existing_match in matches:
                existing_x, existing_y = existing_match['top_left']
                distance = np.sqrt((x - existing_x)**2 + (y - existing_y)**2)
                if distance < min(template_width, template_height) * 0.5:
                    is_duplicate = True
                    # Keep the match with higher confidence
                    if confidence > existing_match['confidence']:
                        matches.remove(existing_match)
                        break
                    else:
                        break
            
            if not is_duplicate:
                matches.append({
                    'top_left': (x, y),
                    'bottom_right': (x + template_width, y + template_height),
                    'center': (x + template_width // 2, y + template_height // 2),
                    'confidence': confidence,
                    'width': template_width,
                    'height': template_height
                })
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches
    
    def find_image_multiscale(self, screenshot, template, threshold=0.8, scales=None):
        """
        Find image matches at multiple scales to handle size variations
        
        Args:
            screenshot: Screenshot image
            template: Template image
            threshold: Matching threshold
            scales: List of scale factors to try
            
        Returns:
            list: List of matches across all scales
        """
        if scales is None:
            scales = [0.5, 0.75, 1.0, 1.25, 1.5]
        
        all_matches = []
        
        for scale in scales:
            # Resize template
            width = int(template.shape[1] * scale)
            height = int(template.shape[0] * scale)
            resized_template = cv2.resize(template, (width, height))
            
            # Find matches at this scale
            matches = self.find_image_matches(screenshot, resized_template, threshold)
            
            # Add scale info to matches
            for match in matches:
                match['scale'] = scale
                all_matches.append(match)
        
        # Remove duplicates and sort by confidence
        all_matches = self.remove_duplicate_matches(all_matches)
        all_matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return all_matches
    
    def remove_duplicate_matches(self, matches):
        """Remove overlapping matches, keeping the one with highest confidence"""
        if not matches:
            return matches
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered_matches = []
        for match in matches:
            is_duplicate = False
            x1, y1 = match['top_left']
            x2, y2 = match['bottom_right']
            
            for existing in filtered_matches:
                ex1, ey1 = existing['top_left']
                ex2, ey2 = existing['bottom_right']
                
                # Check for overlap
                if (x1 < ex2 and x2 > ex1 and y1 < ey2 and y2 > ey1):
                    overlap_area = max(0, min(x2, ex2) - max(x1, ex1)) * max(0, min(y2, ey2) - max(y1, ey1))
                    match_area = (x2 - x1) * (y2 - y1)
                    existing_area = (ex2 - ex1) * (ey2 - ey1)
                    
                    # If significant overlap, consider it a duplicate
                    if overlap_area > 0.3 * min(match_area, existing_area):
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                filtered_matches.append(match)
        
        return filtered_matches
    
    def draw_matches(self, screenshot, matches, template_path):
        """Draw bounding boxes around found matches"""
        result_image = screenshot.copy()
        
        for i, match in enumerate(matches):new
            x1, y1 = match['top_left']
            x2, y2 = match['bottom_right']
            center_x, center_y = match['center']
            
            # Draw bounding box
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(result_image, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Add confidence label
            confidence_text = f"Match {i+1}: {match['confidence']:.2f}"
            if 'scale' in match:
                confidence_text += f" (scale: {match['scale']:.2f})"
            
            cv2.putText(result_image, confidence_text, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return result_image
    
    def select_image_file(self):
        """Open file dialog to select template image"""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        file_path = filedialog.askopenfilename(
            title="Select Template Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        return file_path

def main():
    """Main function to demonstrate the screen image locator"""
    locator = ScreenImageLocator()
    
    print("Screen Image Locator")
    print("====================")
    print("This tool will take a screenshot and find the location of an uploaded image.")
    print("Make sure the image you want to find is visible on your screen.\n")
    
    while True:
        try:
            # Get template image
            print("Please select the template image you want to find on screen...")
            template_path = locator.select_image_file()
            
            if not template_path:
                print("No image selected. Exiting...")
                break
            
            print(f"Selected template: {os.path.basename(template_path)}")
            
            # Load template image
            template = locator.load_template_image(template_path)
            print(f"Template size: {template.shape[1]}x{template.shape[0]} pixels")
            
            # Get search parameters
            threshold = float(input("Enter matching threshold (0.0-1.0, default: 0.8): ") or "0.8")
            multiscale = input("Use multiscale matching? (y/n, default: y): ").lower() != 'n'
            
            print(f"\nTaking screenshot and searching for image...")
            
            # Take screenshot
            screenshot = locator.take_screenshot()
            
            # Find matches
            if multiscale:
                matches = locator.find_image_multiscale(screenshot, template, threshold)
            else:
                matches = locator.find_image_matches(screenshot, template, threshold)
            
            if matches:
                print(f"Found {len(matches)} match(es):")
                for i, match in enumerate(matches, 1):
                    x1, y1 = match['top_left']
                    x2, y2 = match['bottom_right']
                    center_x, center_y = match['center']
                    
                    print(f"  {i}. Match confidence: {match['confidence']:.3f}")
                    print(f"     Top-left: ({x1}, {y1})")
                    print(f"     Bottom-right: ({x2}, {y2})")
                    print(f"     Center: ({center_x}, {center_y})")
                    print(f"     Size: {match['width']}x{match['height']}")
                    if 'scale' in match:
                        print(f"     Scale: {match['scale']:.2f}")
                    print()
                
                # Draw results and show image
                result_image = locator.draw_matches(screenshot, matches, template_path)
                
                # Display the image with results
                cv2.imshow('Image Location Results', result_image)
                print("Press any key to continue or 'q' to quit...")
                
                key = cv2.waitKey(0) & 0xFF
                cv2.destroyAllWindows()
                
                if key == ord('q'):
                    break
                    
            else:
                print(f"No matches found for the template image.")
                print("Try adjusting the threshold or make sure the image is visible on screen.")
            
            print("\n" + "="*50 + "\n")
            
            # Ask if user wants to continue
            continue_search = input("Search for another image? (y/n): ").lower() == 'y'
            if not continue_search:
                break
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Please try again.")
    
    cv2.destroyAllWindows()
    print("Thank you for using Screen Image Locator!")

if __name__ == "__main__":
    main()