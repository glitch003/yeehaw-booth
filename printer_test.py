import win32print
import win32api
import sys
import os
from PIL import Image
import traceback
import img2pdf
import subprocess

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
            
            # Get specific capabilities
            print("\nPrinter Capabilities:")
            capabilities = {
                1: "DC_FIELDS",
                2: "DC_PAPERS",
                3: "DC_PAPERSIZE",
                4: "DC_MINEXTENT",
                5: "DC_MAXEXTENT",
                6: "DC_BINS",
                7: "DC_DUPLEX",
                8: "DC_SIZE",
                9: "DC_EXTRA",
                10: "DC_VERSION",
                11: "DC_DRIVER",
                12: "DC_BINNAMES",
                13: "DC_ENUMRESOLUTIONS",
                14: "DC_FILEDEPENDENCIES",
                15: "DC_TRUETYPE",
                16: "DC_PAPERNAMES",
                17: "DC_ORIENTATION",
                18: "DC_COPIES",
                19: "DC_BINADJUST",
                20: "DC_EMF_COMPLIANT",
                21: "DC_DATATYPE_PRODUCED",
                22: "DC_COLLATE",
                23: "DC_MANUFACTURER",
                24: "DC_MODEL",
                25: "DC_PERSONALITY",
                26: "DC_PRINTRATE",
                27: "DC_PRINTRATEUNIT",
                28: "DC_PRINTERMEM",
                29: "DC_MEDIAREADY",
                30: "DC_STAPLE",
                31: "DC_PRINTRATEPPM",
                32: "DC_COLORDEVICE",
                33: "DC_NUP",
                34: "DC_MEDIATYPENAMES",
                35: "DC_MEDIATYPES"
            }
            
            for cap_code, cap_name in capabilities.items():
                try:
                    value = win32print.DeviceCapabilities(printer_name, None, cap_code)
                    if value is not None and value != 0:
                        if isinstance(value, list):
                            print(f"\n{cap_name} ({cap_code}):")
                            for i, v in enumerate(value):
                                print(f"  {i+1}. {v}")
                        else:
                            print(f"{cap_name} ({cap_code}): {value}")
                except Exception as e:
                    continue
                    
        finally:
            win32print.ClosePrinter(printer_handle)
    except Exception as e:
        print(f"Error getting printer info: {e}")

def get_media_capabilities(printer_name):
    print(f"\nQuerying media/paper capabilities for: {printer_name}\n{'-'*60}")
    caps_to_check = {
        16: "DC_PAPERNAMES",
        2: "DC_PAPERS",
        3: "DC_PAPERSIZE",
        34: "DC_MEDIATYPENAMES",
        35: "DC_MEDIATYPES"
    }
    for cap_code, cap_name in caps_to_check.items():
        try:
            value = win32print.DeviceCapabilities(printer_name, None, cap_code)
            print(f"{cap_name} ({cap_code}): {repr(value)}")
        except Exception as e:
            print(f"{cap_name} ({cap_code}): ERROR - {e}")

def print_4x6_image(printer_name, image_path):
    print(f"\nAttempting to print {image_path} on {printer_name} with 4x6 settings")
    print("-" * 60)
    
    try:
        print("Step 1: Opening printer...")
        printer_handle = win32print.OpenPrinter(printer_name)
        print("Printer opened successfully")
        
        try:
            print("\nStep 2: Getting current printer settings (level 2)...")
            printer_info = win32print.GetPrinter(printer_handle, 2)
            print(f"Printer info (level 2) keys: {list(printer_info.keys())}")
            print("Attempting to access pDevMode...")
            devmode = printer_info["pDevMode"]
            print("Current settings retrieved")

            print("Current devmode settings:")
            print(f"  Paper Width: {devmode.PaperWidth/10}mm")
            print(f"  Paper Length: {devmode.PaperLength/10}mm") 
            print(f"  Orientation: {devmode.Orientation}")
            print(f"  Color: {devmode.Color}")
            print(f"  Print Quality: {devmode.PrintQuality} DPI")
            print(f"  Paper Size: {devmode.PaperSize}")
            print(f"  Scale: {devmode.Scale}%")
            print(f"  Copies: {devmode.Copies}")
            
            print("\nStep 3: Setting paper size to 4x6...")
            devmode.PaperWidth = 1016  # 4 inches in 1/10 mm
            devmode.PaperLength = 1524  # 6 inches in 1/10 mm
            print(f"Set paper width to {devmode.PaperWidth/10}mm")
            print(f"Set paper length to {devmode.PaperLength/10}mm")
            
            print("\nStep 4: Setting other print parameters...")
            devmode.Orientation = 1  # 1 = Portrait
            devmode.Color = 2  # 2 = Color
            devmode.PrintQuality = 600  # 600 DPI
            print("Print parameters set")
            
            print("\nStep 5: Updating printer settings...")
            win32print.SetPrinter(printer_handle, 2, {"pDevMode": devmode}, 0)
            print("Printer settings updated")
            
            print("\nStep 6: Verifying image file...")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            print("Image file exists")
            
            print("\nStep 7: Opening and verifying image...")
            img = Image.open(image_path)
            print(f"Image size: {img.size}")
            print(f"Image mode: {img.mode}")
            
            print("\nStep 8: Starting print job...")
            job = win32print.StartDocPrinter(printer_handle, 1, ("Photo Strip", None, "RAW"))
            print("Print job started")
            
            try:
                print("\nStep 9: Starting page...")
                win32print.StartPagePrinter(printer_handle)
                print("Page started")
                
                print("\nStep 10: Reading image data...")
                with open(image_path, 'rb') as f:
                    data = f.read()
                print(f"Read {len(data)} bytes of image data")
                
                print("\nStep 11: Writing to printer...")
                win32print.WritePrinter(printer_handle, data)
                print("Data written to printer")
                
                print("\nStep 12: Ending page...")
                win32print.EndPagePrinter(printer_handle)
                print("Page ended")
                
                print("\nPrint job submitted successfully!")
            except Exception as e:
                print(f"\nError during print job: {str(e)}")
                print("\nDetailed error:")
                print(traceback.format_exc())
            finally:
                print("\nStep 13: Ending print job...")
                win32print.EndDocPrinter(printer_handle)
                print("Print job ended")
                
        except Exception as e:
            print(f"\nError during printer setup: {str(e)}")
            print("\nDetailed error:")
            print(traceback.format_exc())
        finally:
            print("\nStep 14: Closing printer...")
            win32print.ClosePrinter(printer_handle)
            print("Printer closed")
            
    except Exception as e:
        print(f"\nError during printing: {str(e)}")
        print("\nDetailed error:")
        print(traceback.format_exc())

def list_printers():
    printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    print("\nAvailable Printers:")
    print("-" * 50)
    for i, name in enumerate(printers, 1):
        print(f"{i}. {name}")
    return printers

def print_with_gsprint(pdf_path):
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

def resize_image_for_printing(image_path, printer_name):
    """Resize image to fit both strips on the printer's media size"""
    try:
        # Get printer handle and media size
        printer_handle = win32print.OpenPrinter(printer_name)
        try:
            # Get printer settings
            settings = win32print.GetPrinter(printer_handle, 3)
            if not settings:
                raise Exception("Could not get printer settings")
                
            # Get media size in mm
            media_width_mm = settings.get('dmPaperWidth', 101.6)  # Default to 4 inches if not found
            media_height_mm = settings.get('dmPaperLength', 152.4)  # Default to 6 inches if not found
            
            print(f"Printer media size: {media_width_mm/10}mm x {media_height_mm/10}mm")
            
            # Open the image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            print(f"Original image size: {img.size}")
            
            # Calculate target size in pixels at 600 DPI
            # We want the image to be about 60% of the media size
            scale_factor = 0.6
            target_width = int((media_width_mm / 25.4) * 600 * scale_factor)
            target_height = int((media_height_mm / 25.4) * 600 * scale_factor)
            
            print(f"Target size in pixels: {target_width}x{target_height}")
            
            # Resize image maintaining aspect ratio
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            print(f"Resized image size: {img.size}")
            
            # Create a new white background image at the target size
            background = Image.new('RGB', (target_width, target_height), 'white')
            
            # Calculate position to center the image
            x = (target_width - img.width) // 2
            y = (target_height - img.height) // 2
            
            # Paste the resized image onto the white background
            background.paste(img, (x, y))
            
            # Save the resized image
            resized_path = os.path.splitext(image_path)[0] + '_resized.jpg'
            background.save(resized_path, 'JPEG', quality=95)
            
            print(f"Resized image saved to: {resized_path}")
            return resized_path
            
        finally:
            win32print.ClosePrinter(printer_handle)
            
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        print(traceback.format_exc())
        return None

def convert_to_pdf(image_path):
    """Convert an image to PDF"""
    try:
        # Create PDF filename
        pdf_path = os.path.splitext(image_path)[0] + '.pdf'
        
        # Convert image to PDF with explicit 4x6 inch size
        with open(pdf_path, "wb") as f:
            # Create a layout function that forces 4x6 inch size
            def layout_fun(img_width, img_height, img_rotation):
                # Convert inches to points (1 inch = 72 points)
                page_width = 4.09 * 72  # 4 inches
                page_height = 6.15 * 72  # 6 inches
                return (page_width, page_height, page_width, page_height)
            
            f.write(img2pdf.convert(image_path, layout_fun=layout_fun))
            
        print(f"Converted {image_path} to {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Error converting to PDF: {str(e)}")
        print(traceback.format_exc())
        return None

def main():
    printers = list_printers()
    dnp_printer = None
    for name in printers:
        if "Dai_Nippon" in name or "DNP" in name or "DS-RX1" in name:
            dnp_printer = name
            break
    
    if dnp_printer:
        print(f"\nFound DNP printer: {dnp_printer}")
        image_path = r"C:\Users\glitc\Documents\yeehaw-booth\photos\strip_20250530_135230_print.jpg"
        
        # Resize image using printer's media size
        resized_path = resize_image_for_printing(image_path, dnp_printer)
        if not resized_path:
            print("Failed to resize image")
            return
            
        # Convert to PDF
        pdf_path = convert_to_pdf(resized_path)
        if not pdf_path:
            print("Failed to convert to PDF")
            return
            
        # Print using gsprint
        print_with_gsprint(pdf_path)
    else:
        print("\nNo DNP printer found. Would you like to:")
        for i, name in enumerate(printers, 1):
            print(f"{i}. Get info for {name}")
        try:
            choice = int(input("\nEnter printer number (or 0 to exit): "))
            if 1 <= choice <= len(printers):
                image_path = r"C:\Users\glitc\Documents\yeehaw-booth\photos\strip_20250530_135230_print.jpg"
                
                # Resize image using printer's media size
                resized_path = resize_image_for_printing(image_path, printers[choice-1])
                if not resized_path:
                    print("Failed to resize image")
                    return
                    
                # Convert to PDF
                pdf_path = convert_to_pdf(resized_path)
                if not pdf_path:
                    print("Failed to convert to PDF")
                    return
                    
                # Print using gsprint
                print_with_gsprint(pdf_path)
        except ValueError:
            print("Invalid input")

if __name__ == "__main__":
    main() 