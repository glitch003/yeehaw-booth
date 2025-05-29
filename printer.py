import os
import win32print
import win32api
from PIL import Image

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
            
            # Get printer handle
            printer_handle = win32print.OpenPrinter(self.printer_name)
            try:
                # Start a print job
                job = win32print.StartDocPrinter(printer_handle, 1, ("Photo Strip", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer_handle)
                    # Read the file in binary mode
                    with open(temp_path, 'rb') as f:
                        data = f.read()
                    # Write the data to the printer
                    win32print.WritePrinter(printer_handle, data)
                    win32print.EndPagePrinter(printer_handle)
                finally:
                    win32print.EndDocPrinter(printer_handle)
            finally:
                win32print.ClosePrinter(printer_handle)
                
            print(f"Print job submitted to: {self.printer_name}")
            return True
        except Exception as e:
            print(f"Error printing: {str(e)}")
            # Print more detailed error information
            import traceback
            print("Detailed error:")
            print(traceback.format_exc())
            return False 