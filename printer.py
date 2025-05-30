import os
import win32print
import win32api
from PIL import Image
import img2pdf
import subprocess
import traceback

class DNPPrinter:
    def __init__(self):
        # List all available printers
        printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        print("Available printers:")
        for name in printers:
            print(f"Name: {name}")
        
        # Try to find DNP printer
        self.printer_name = None
        for name in printers:
            if "Dai_Nippon" in name or "DNP" in name or "DS-RX1" in name:
                self.printer_name = name
                print(f"Found DNP printer: {name}")
                break
        
        if not self.printer_name:
            print("DNP printer not found in system printers. Using default printer.")
            self.printer_name = win32print.GetDefaultPrinter()
            print(f"Default printer: {self.printer_name}")

    def convert_to_pdf(self, image_path):
        """Convert an image to PDF"""
        try:
            # Create PDF filename
            pdf_path = os.path.splitext(image_path)[0] + '.pdf'
            
            # Convert image to PDF
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(image_path))
                
            print(f"Converted {image_path} to {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Error converting to PDF: {str(e)}")
            print(traceback.format_exc())
            return None

    def print_with_gsprint(self, pdf_path):
        """Print a PDF file using gsprint"""
        try:
            # Get the path to gsprint.exe
            gsprint_path = r"C:\Program Files\Ghostgum\gsview\gsprint.exe"
            gswin64_path = r"C:\Program Files\gs\gs10.05.1\bin\gswin64.exe"
            
            if not os.path.exists(gsprint_path):
                print(f"Error: gsprint.exe not found at {gsprint_path}")
                return False
                
            if not os.path.exists(gswin64_path):
                print(f"Error: gswin64.exe not found at {gswin64_path}")
                return False
                
            # Construct the command
            cmd = [gsprint_path, "-ghostscript", gswin64_path, pdf_path]
            
            # Execute the command
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Print job submitted successfully!")
                return True
            else:
                print(f"Error printing: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error during printing: {str(e)}")
            print(traceback.format_exc())
            return False

    def print_strip(self, image_path):
        """
        Print a photo strip using the DNP DS-RX1 printer (or default printer).
        The image should be a 4x6 photo that will be cut into two 2x6 strips.
        Args:
            image_path (str): Path to the image file to print
        """
        try:
            # Ensure the image is in the correct format and size
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            temp_dir = os.path.dirname(os.path.abspath(image_path))
            temp_filename = os.path.basename(image_path).replace('.jpg', '_print.jpg')
            temp_path = os.path.join(temp_dir, temp_filename)
            temp_path = os.path.abspath(temp_path)
            print(f"Saving temporary file to: {temp_path}")
            img.save(temp_path, 'JPEG', quality=95)
            
            if not os.path.exists(temp_path):
                raise FileNotFoundError(f"Temporary file was not created: {temp_path}")
            if not os.access(temp_path, os.R_OK):
                raise PermissionError(f"Cannot read temporary file: {temp_path}")
                
            print(f"Attempting to print using printer: {self.printer_name}")
            print(f"Printing file: {temp_path}")
            
            # Convert to PDF
            pdf_path = self.convert_to_pdf(temp_path)
            if not pdf_path:
                raise Exception("Failed to convert image to PDF")
            
            # Print using gsprint
            success = self.print_with_gsprint(pdf_path)
            if not success:
                raise Exception("Failed to print using gsprint")
                
            print(f"Print job submitted to: {self.printer_name}")
            return True
        except Exception as e:
            print(f"Error printing: {str(e)}")
            print("Detailed error:")
            print(traceback.format_exc())
            return False 