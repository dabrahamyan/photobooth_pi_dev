from PIL import Image
from PIL import ImageWin
from escpos.printer import Usb


# IMAGE SETTINGS
thresh = 110

# open photos you'll use
template = Image.open("junkyard_template.png")
pic = Image.open("yo.jpg")

# Resize template to printer width (576 pixels for 80mm)
width = 576
height = int(width * template.height / template.width)
template = template.resize((width, height))

# Resize people picture to be exact height and width
pic = pic.resize((474, 483))

# paste people pic into template
template.paste(pic, (55, 146))

# Pure B&W
template = template.convert('1') # make black and white

# # dithering
# img = img.convert('L') # make greyscale
# img = img.convert('1', dither=Image.FLOYDSTEINBERG)


# threshold image
# img = img.convert('L') #convert to grayscale
# img = img.point(lambda x: 0 if x < thresh else 255, '1') # then to B&W with threshold

# Connect to printer via USB
p = Usb(0x1FC9, 0x2016) #printer ID i found during craft night

# Print the image
p.image(template)
p.cut()

print("Photo printed")
