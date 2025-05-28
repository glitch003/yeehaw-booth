import os
import cups
from PIL import Image
from urllib.parse import quote

class DNPPrinter:
    def __init__(self):
        self.conn = cups.Connection()
        # List all available printers and their URIs
        printers = self.conn.getPrinters()
        print("Available printers:")
        for name, printer in printers.items():
            print(f"Name: {name}")
            print(f"URI: {printer.get('device-uri', 'No URI')}")
            print("---")
        
        # Try to find DNP printer
        self.printer_uri = None
        for name, printer in printers.items():
            if "Dai_Nippon" in name:
                self.printer_uri = printer.get('device-uri')
                print(f"Found DNP printer: {name} with URI: {self.printer_uri}")
                break
        
        if not self.printer_uri:
            print("DNP printer not found in system printers. Using default URI.")
            self.printer_uri = "usb://Dai%20Nippon%20Printing/DS-RX1?location=100000"
        
    def print_strip(self, image_path):
        """
        Print a photo strip using the DNP DS-RX1 printer.
        The image should be a 4x6 photo that will be cut into two 2x6 strips.
        
        Args:
            image_path (str): Path to the image file to print
        """
        try:
            # Ensure the image is in the correct format and size
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as temporary file in the correct format with absolute path
            temp_dir = os.path.dirname(os.path.abspath(image_path))
            temp_filename = os.path.basename(image_path).replace('.jpg', '_print.jpg')
            temp_path = os.path.join(temp_dir, temp_filename)
            temp_path = os.path.abspath(temp_path)
            
            print(f"Saving temporary file to: {temp_path}")
            img.save(temp_path, 'JPEG', quality=95)
            
            # Verify the file exists and is readable
            if not os.path.exists(temp_path):
                raise FileNotFoundError(f"Temporary file was not created: {temp_path}")
            
            if not os.access(temp_path, os.R_OK):
                raise PermissionError(f"Cannot read temporary file: {temp_path}")
            
            print(f"Attempting to print using URI: {self.printer_uri}")
            print(f"Printing file: {temp_path}")
            
            # Print using CUPS with direct URI
            job_id = self.conn.printFile(
                self.printer_uri,
                temp_path,  # Use the raw path instead of encoded path
                "Photo Strip",  # Job name
                {
                    'fit-to-page': 'true',
                }
            )
            
            print(f"Print job submitted with ID: {job_id}")
            return True
            
        except Exception as e:
            print(f"Error printing: {str(e)}")
            return False 