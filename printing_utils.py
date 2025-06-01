import os
import win32print
import subprocess
import traceback
import img2pdf
from PIL import Image, ImageDraw, ImageFont

def get_printer_media_size(printer_name):
    """Get the media size for a specific printer"""
    try:
        printer_handle = win32print.OpenPrinter(printer_name)
        try:
            settings = win32print.GetPrinter(printer_handle, 3)
            if not settings:
                raise Exception("Could not get printer settings")
                
            # Get media size in mm
            media_width_mm = settings.get('dmPaperWidth', 101.6)  # Default to 4 inches if not found
            media_height_mm = settings.get('dmPaperLength', 152.4)  # Default to 6 inches if not found
            
            return media_width_mm, media_height_mm
            
        finally:
            win32print.ClosePrinter(printer_handle)
            
    except Exception as e:
        print(f"Error getting printer media size: {str(e)}")
        # Return default 4x6 inch size in mm
        return 101.6, 152.4

def resize_image_for_printing(image_path, printer_name):
    """Resize image to fit both strips on the printer's media size"""
    try:
        # Get printer media size
        media_width_mm, media_height_mm = get_printer_media_size(printer_name)
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
        if os.path.exists(qr_path):
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
            
            # Calculate center coordinates for each strip
            left_strip_center_x = strip_width // 2
            right_strip_center_x = strip_width + (strip_width // 2)
            text_center_y = target_height - text_height // 2 - 50  # Center the text vertically in its area
            
            # Draw text on left strip (centered)
            draw.text((left_strip_center_x, text_center_y), text, fill='black', font=font, anchor="mm")
            
            # Position QR code above text on left strip (centered)
            left_qr_x = (strip_width - qr_img.width) // 2
            qr_y = text_center_y - text_height // 2 - qr_img.height - 20  # 20 pixels above text
            background.paste(qr_img, (left_qr_x, qr_y))
            
            # Draw text on right strip (centered)
            draw.text((right_strip_center_x, text_center_y), text, fill='black', font=font, anchor="mm")
            
            # Position QR code above text on right strip (centered)
            right_qr_x = strip_width + (strip_width - qr_img.width) // 2
            background.paste(qr_img, (right_qr_x, qr_y))
        
        # Save the resized image
        resized_path = os.path.splitext(image_path)[0] + '_resized.jpg'
        background.save(resized_path, 'JPEG', quality=95)
        
        print(f"Resized image saved to: {resized_path}")
        return resized_path
        
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        print(traceback.format_exc())
        return None

def convert_to_pdf(image_path):
    """Convert an image to PDF with explicit 4x6 inch size"""
    try:
        # Create PDF filename
        pdf_path = os.path.splitext(image_path)[0] + '.pdf'
        
        # Convert image to PDF with explicit 4x6 inch size
        with open(pdf_path, "wb") as f:
            # Create a layout function that forces 4x6 inch size
            def layout_fun(img_width, img_height, img_rotation):
                # Convert inches to points (1 inch = 72 points)
                page_width = 4.09 * 72  # 4 inches
                page_height = 6.02 * 72  # 6 inches
                return (page_width, page_height, page_width, page_height)
            
            f.write(img2pdf.convert(image_path, layout_fun=layout_fun))
            
        print(f"Converted {image_path} to {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Error converting to PDF: {str(e)}")
        print(traceback.format_exc())
        return None

def print_with_gsprint(pdf_path, printer_name=None):
    """Print a PDF file using gsprint with enhanced color settings"""
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
        ]
        
        # Add printer specification if provided
        if printer_name:
            cmd.extend(["-printer", printer_name])
            print(f"Targeting specific printer: {printer_name}")
        
        cmd.append(pdf_path)
        
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

def print_photo_strip(image_path, printer_name):
    """
    Complete photo strip printing workflow:
    1. Resize image for printer's media size
    2. Convert to PDF with proper layout
    3. Print using gsprint with color settings
    """
    try:
        print(f"Starting photo strip printing workflow for: {image_path}")
        print(f"Using printer: {printer_name}")
        
        # Step 1: Resize image using printer's media size
        resized_path = resize_image_for_printing(image_path, printer_name)
        if not resized_path:
            raise Exception("Failed to resize image for printing")
        
        # Step 2: Convert to PDF with proper layout
        pdf_path = convert_to_pdf(resized_path)
        if not pdf_path:
            raise Exception("Failed to convert image to PDF")
        
        # Step 3: Print using gsprint with enhanced settings
        success = print_with_gsprint(pdf_path, printer_name)
        if not success:
            raise Exception("Failed to print using gsprint")
        
        print(f"Photo strip printing completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in photo strip printing workflow: {str(e)}")
        print(traceback.format_exc())
        return False 