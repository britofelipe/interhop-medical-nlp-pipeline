import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import os

class OCRService:
    def __init__(self):
        # Ensure Tesseract knows where the data files are (standard linux path)
        # In the Dockerfile we installed tesseract-ocr-fra
        self.lang = 'fra'

    def process_file(self, file_path: str) -> str:
        """
        Main entry point: Handles both PDF and Images.
        Returns the combined extracted text.
        """
        ext = file_path.split('.')[-1].lower()
        extracted_text = ""

        if ext == 'pdf':
            # Convert PDF to list of PIL Images
            images = convert_from_path(file_path)
            for i, img in enumerate(images):
                # Convert PIL to OpenCV format (numpy)
                open_cv_image = np.array(img) 
                # RGB to BGR for OpenCV
                open_cv_image = open_cv_image[:, :, ::-1].copy() 
                
                text = self._process_single_image(open_cv_image)
                extracted_text += f"\n--- Page {i+1} ---\n{text}"
        else:
            # It is an image (png, jpg)
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Could not load image at {file_path}")
            extracted_text = self._process_single_image(img)

        return extracted_text

    def _process_single_image(self, img_cv2) -> str:
        """
        Applies Computer Vision preprocessing and runs Tesseract.
        """
        # 1. Grayscale (Essential for OCR)
        gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)

        # 2. Denoising (Crucial for the 'Salt & Pepper' noise we added in Phase 3.1)
        # MedianBlur is excellent for removing salt-and-pepper noise
        denoised = cv2.medianBlur(gray, 3)

        # 3. Thresholding (Binarization)
        # Otsu's thresholding automatically finds the best separation between text and background
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 4. (Optional) Deskewing could go here if rotation is severe
        # For now, Tesseract 4/5 handles slight rotations well.

        # 5. Run OCR
        # --psm 6: Assume a single uniform block of text. Good for prescriptions.
        config = "--psm 6" 
        text = pytesseract.image_to_string(thresh, lang=self.lang, config=config)

        return text.strip()
    