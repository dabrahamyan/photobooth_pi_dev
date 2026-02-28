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
import requests
import qrcode

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

API_URL = "https://booth-api.lucas.tools/api/v1/upload"
API_KEY = "BC60806019AA489B94BDBF8DAB008829"
EVENT_ID = "market_2_20"

def upload_and_show_qr(photo_path: str):
    try:
        with open(photo_path, "rb") as f:
            res = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                files={"file": (photo_path, f, "image/jpeg")},
                data={"event_id": EVENT_ID},
                timeout=10,
            )
        res.raise_for_status()
        url = res.json()["url"]
    except Exception:
        return None

    qr = qrcode.make(url)

    return qr

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
    except Exception as e:
        print(f"Printer connection failed: {e}")
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

        # Try to upload photo and get QR code
        qr = upload_and_show_qr(photo_file)
        if qr:
            qr = qr.resize((220, 220))

        # Open template and photo w/ error handling
        try:
            if qr:
                template = Image.open("junkyard_template.png")
            else:
                template = Image.open("template_no_qr.png")
        except FileNotFoundError:
            print("Template not found! Using blank background")
            template = Image.new('RGB', (576, 800), color='white')
        
        pic = Image.open(photo_file)

        # Resize template
        width = 576
        height = int(width * template.height / template.width)
        template = template.resize((width, height))

        # Resize photo
        pic = pic.resize((550, 412))

        # Grayscale first
        template = template.convert("L")
        pic = pic.convert("L")

        # Paste stuff
        if qr:
            template.paste(pic, (10, 180))
            template.paste(qr, (185, 730))
        else:
            template.paste(pic, (10, 145))


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
            print("Bogos binted! Ready for next person.")
        except Exception as e:
            print(f"Print failed - check paper/printer: {e}")

button = Button(24)
while True:
    if button.is_pressed:
        take_photo_and_print()

        print("Photobooth ready! Press button to take photo.")



# Set up button
# button = Button(24)
# button.when_pressed = take_photo_and_print

# print("Photobooth ready! Press button to take photo.")
# pause()
