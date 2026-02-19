from PIL import Image
from datetime import datetime
from picamera2 import Picamera2
import time
from escpos.printer import Usb
from gpiozero import Button
from signal import pause
import threading

# IMAGE SETTINGS
thresh = 110

# Initialize camera ONCE at startup
picam = Picamera2()
config = picam.create_still_configuration(main={"size": (1640, 1232)})
picam.configure(config)
picam.start()

# Initialize Printer ONCE
printer = Usb(0x1FC9, 0x2016)

# make print lock
printing_lock = threading.Lock()

def capture_photo():
    """Capture a photo using the already-running camera"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photos/photo_{timestamp}.jpg"
    
    # Just capture, don't start/stop camera
    picam.capture_file(filename)
    
    return filename

def take_photo_and_print():
    #check if already printing
    if printing_lock.locked():
        print("Still Printing previous photo, wait..")
        return

    with printing_lock:
        print("Button pressed! Taking photo...")
    
        # Capture photo
        photo_file = capture_photo()
    
        # Open template and photo
        template = Image.open("junkyard_template.png")
        pic = Image.open(photo_file)
    
        # Resize template
        width = 576
        height = int(width * template.height / template.width)
        template = template.resize((width, height))
    
        # Resize photo
        pic = pic.resize((480, 480))
    
        # Paste
        template.paste(pic, (50, 145))
    
        # Convert to B&W
        template = template.convert('1')
    
        # Print
        try:
            printer.image(template)
            printer.cut()
    
            print("Photo printed! Ready for next person.")
        except Exception as e:
            print(f"Print failed - check paper/printer: {e}")


# Set up button
button = Button(24) #, pull_up=True, bounce_time=1.0)
button.when_pressed = take_photo_and_print

print("Photobooth ready! Press button to take photo.")
pause()
