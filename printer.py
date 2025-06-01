import os
import win32print
import win32api
from PIL import Image
import traceback
from printing_utils import print_photo_strip

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
            print(f"Attempting to print using printer: {self.printer_name}")
            print(f"Printing file: {image_path}")
            
            # Use the working printing utilities
            success = print_photo_strip(image_path, self.printer_name)
            
            if success:
                print(f"Print job completed successfully using: {self.printer_name}")
                return True
            else:
                raise Exception("Photo strip printing workflow failed")
                
        except Exception as e:
            print(f"Error printing: {str(e)}")
            print("Detailed error:")
            print(traceback.format_exc())
            return False 