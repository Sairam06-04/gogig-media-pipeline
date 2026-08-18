import cv2
import numpy as np
import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # type: ignore

def analyze_image(file_path):
    # This dictionary will hold the final results of our 4 checks
    results = {
        "blur_issue": False,
        "brightness_issue": False,
        "dimensions_issue": False,
        "ai_insights": "Not run"
    }
    
    # --- CHECKS 1, 2, & 3: OpenCV Programmatic Checks ---
    image = cv2.imread(file_path)
    if image is not None:
        # Convert image to grayscale for easier math
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Check 1: Blur Detection (Calculates the variance of the Laplacian)
        # If variance is low, edges are not sharp, meaning it is blurry.
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        results["blur_issue"] = bool(variance < 100) 
        
        # Check 2: Brightness Analysis
        # If the average pixel intensity is too low (dark) or too high (glare)
        brightness = np.mean(gray)
        results["brightness_issue"] = bool(brightness < 50 or brightness > 210)
        
        # Check 3: Dimension Validation
        # Flag if the image is unusually small for a modern smartphone photo
        height, width = image.shape[:2]
        results["dimensions_issue"] = bool(height < 400 or width < 400)
    
    # --- CHECK 4: AI Heuristics & OCR ---
    try:
        if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_api_key_here":
            model = genai.GenerativeModel('gemini-flash-latest') # type: ignore
            img = Image.open(file_path)
            
            prompt = """
            Analyze this vehicle image for a quality control system. 
            1. Is there a vehicle number plate visible? If yes, extract the text.
            2. Does this image look like a screenshot, a photo of a screen, or digitally tampered? 
            Return a short, structured summary.
            """
            response = model.generate_content([prompt, img])
            results["ai_insights"] = response.text
        else:
            results["ai_insights"] = "Skipped: No API Key configured in .env"
    except Exception as e:
        results["ai_insights"] = f"AI processing failed: {str(e)}"
        
    return results