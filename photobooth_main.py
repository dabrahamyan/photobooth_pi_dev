import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from PIL import Image, ImageEnhance
from datetime import datetime
from picamera2 import Picamera2
import time
from escpos.printer import Usb
from gpiozero import Button
from signal import pause
import threading

# IMAGE SETTINGS
BRIGHTNESS = 1.5   # 1.0 = normal, 1.3–1.7 works well for thermal printers
CONTRAST   = 1.6

# Initialize camera at startup
picam = Picamera2()
config = picam.create_still_configuration(main={"size": (1640, 1232)})
picam.configure(config)
picam.start()

# Initialize Printer
try:
    printer = Usb(0x1FC9, 0x2016)
    print("Printer initialized successfully")
except Exception as e:
    print(f"WARNING: Printer not found: {e}")
    printer = None

# make print lock
printing_lock = threading.Lock()

def capture_photo():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photos/photo_{timestamp}.jpg"
        picam.capture_file(filename)
        return filename
    except Exception as e:
        print(f"Camera error: {e}")
        return None
    
def get_printer():
    # Tries to connect to printer and returns None if its not available
    try:
        return Usb(0x1FC9, 0x2016)
    except:
        return None

def take_photo_and_print():
    # check if already printing
    if printing_lock.locked():
        print("Still Printing previous photo, wait..")
        return

    with printing_lock:
        print("Button pressed! Taking photo...")

        time.sleep(2)
        # Capture photo
        photo_file = capture_photo()

        # Open template and photo w/ error handling
        try:
            template = Image.open("junkyard_template.png")
        except FileNotFoundError:
            print("Template not found! Using blank background")
            template = Image.new('RGB', (576, 800), color='white')
        
        pic = Image.open(photo_file)

        # Resize template
        width = 576
        height = int(width * template.height / template.width)
        template = template.resize((width, height))

        # Resize photo
        pic = pic.resize((550, 480))

        # Paste
        template.paste(pic, (10, 145))

        # Grayscale first
        template = template.convert("L")

        # Brighten for printing
        template = ImageEnhance.Brightness(template).enhance(BRIGHTNESS)
        template = ImageEnhance.Contrast(template).enhance(CONTRAST)

        # Convert to pure black & white
        template = template.convert("1")

        # Try to find printer if we don't have one
        global printer
        if printer is None:
            print("Trying to reconnect to printer...")
            printer = get_printer()

        if printer is None:
            print("Printer still not available - photo saved but not printed")
            return

        # Print
        try:
            printer.image(template)
            printer.cut()
            print("Photo printed! Ready for next person.")
        except Exception as e:
            print(f"Print failed - check paper/printer: {e}")

# Set up button
button = Button(24)
button.when_pressed = take_photo_and_print

print("Photobooth ready! Press button to take photo.")
pause()
