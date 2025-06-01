import win32print
import sys
import os
from PIL import Image
import traceback
from printing_utils import print_photo_strip, get_printer_media_size

def get_printer_info(printer_name):
    """Get detailed information about a specific printer"""
    try:
        # Open the printer
        printer_handle = win32print.OpenPrinter(printer_name)
        try:
            # Get printer info
            info = win32print.GetPrinter(printer_handle, 2)
            print(f"\nPrinter Information for: {printer_name}")
            print("-" * 50)
            print(f"Status: {info['Status']}")
            print(f"Attributes: {info['Attributes']}")
            print(f"Priority: {info['Priority']}")
            print(f"Default Priority: {info['DefaultPriority']}")
            print(f"Start Time: {info['StartTime']}")
            print(f"Until Time: {info['UntilTime']}")
            print(f"Average PPM: {info['AveragePPM']}")
            
            # Get printer settings
            settings = win32print.GetPrinter(printer_handle, 3)
            if settings:
                print("\nCurrent Printer Settings:")
                print(f"  Paper Size: {settings.get('dmPaperSize', 'Unknown')}")
                print(f"  Paper Length: {settings.get('dmPaperLength', 'Unknown')}")
                print(f"  Paper Width: {settings.get('dmPaperWidth', 'Unknown')}")
                print(f"  Orientation: {settings.get('dmOrientation', 'Unknown')}")
                print(f"  Copies: {settings.get('dmCopies', 'Unknown')}")
                print(f"  Default Source: {settings.get('dmDefaultSource', 'Unknown')}")
                print(f"  Print Quality: {settings.get('dmPrintQuality', 'Unknown')}")
                print(f"  Color: {settings.get('dmColor', 'Unknown')}")
                print(f"  Duplex: {settings.get('dmDuplex', 'Unknown')}")
            
        finally:
            win32print.ClosePrinter(printer_handle)
    except Exception as e:
        print(f"Error getting printer info: {e}")

def list_printers():
    printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    print("\nAvailable Printers:")
    print("-" * 50)
    for i, name in enumerate(printers, 1):
        print(f"{i}. {name}")
    return printers

def main():
    printers = list_printers()
    dnp_printer = None
    for name in printers:
        if "Dai_Nippon" in name or "DNP" in name or "DS-RX1" in name:
            dnp_printer = name
            break
    
    image_path = r"C:\Users\glitc\Documents\yeehaw-booth\photos\strip_20250601_162010_print.jpg"
    
    if dnp_printer:
        print(f"\nFound DNP printer: {dnp_printer}")
        
        # Use the printing utilities
        print_photo_strip(image_path, dnp_printer)
    else:
        print("\nNo DNP printer found. Would you like to:")
        for i, name in enumerate(printers, 1):
            print(f"{i}. Get info for {name}")
        try:
            choice = int(input("\nEnter printer number (or 0 to exit): "))
            if 1 <= choice <= len(printers):                
                # Use the printing utilities
                print_photo_strip(image_path, printers[choice-1])
        except ValueError:
            print("Invalid input")

if __name__ == "__main__":
    main() 