import win32print
import sys
import os
from PIL import Image
import traceback
import img2pdf
import subprocess
from PIL import ImageDraw, ImageFont

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
            
        # Construct the command with color mode parameters
        cmd = [
            gsprint_path,
            "-ghostscript", gswin64_path,
            "-color",  # Enable color printing
            "-dUseCIEColor=true",  # Use CIE color space
            "-dProcessColorModel=/DeviceRGB",  # Use RGB color model
            pdf_path
        ]
        
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
            
            # Calculate position to place image at the top
            x = (target_width - img.width) // 2  # Center horizontally
            y = 0  # Place at the top
            
            # Paste the resized image onto the white background
            background.paste(img, (x, y))
            
            # Load and resize QR code
            qr_path = os.path.join(os.path.dirname(os.path.dirname(image_path)), "qr-code.png")
            if not os.path.exists(qr_path):
                raise FileNotFoundError(f"QR code not found at {qr_path}")
                
            qr_img = Image.open(qr_path)
            if qr_img.mode != 'RGB':
                qr_img = qr_img.convert('RGB')
            
            # Calculate QR code size (about 1/3 of strip width)
            strip_width = target_width // 2
            qr_size = strip_width // 3
            
            # Resize QR code maintaining aspect ratio
            qr_img.thumbnail((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            # Add text at the bottom
            draw = ImageDraw.Draw(background)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 72)  # Adjust size as needed
            except:
                font = ImageFont.load_default()
            
            # Text to add
            text = "Law and Disorder\nBig Stick 2025"
            
            # Calculate text position for both strips
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate strip widths
            strip_width = target_width // 2
            
            # Draw text and QR code on left strip
            left_text_x = (strip_width - text_width) // 2
            text_y = target_height - text_height - 50  # 50 pixels from bottom
            draw.text((left_text_x, text_y), text, fill='black', font=font)
            
            # Position QR code above text on left strip
            left_qr_x = (strip_width - qr_img.width) // 2
            qr_y = text_y - qr_img.height - 20  # 20 pixels above text
            background.paste(qr_img, (left_qr_x, qr_y))
            
            # Draw text and QR code on right strip
            right_text_x = strip_width + (strip_width - text_width) // 2
            draw.text((right_text_x, text_y), text, fill='black', font=font)
            
            # Position QR code above text on right strip
            right_qr_x = strip_width + (strip_width - qr_img.width) // 2
            background.paste(qr_img, (right_qr_x, qr_y))
            
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