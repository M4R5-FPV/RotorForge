"""Root-layer sections for the single two-plate clamp, using default dimensions."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
im = Image.new('RGB', (1600, 650), 'white')
d = ImageDraw.Draw(im)
ink, line, carbon, arms, amber = '#262a2f', '#d4d6d8', '#565b63', '#a3a8ae', '#e6b25a'

def text(x, y, value, size=25, bold=False, fill=ink):
    d.text((x, y), value, font=ImageFont.truetype(BOLD if bold else FONT, size), fill=fill)

for origin, upper in ((20, False), (820, True)):
    d.rounded_rectangle((origin, 8, origin+760, 640), radius=18, outline=line, width=2)
    text(origin+28, 30, 'ARMS ABOVE BOTTOM' if upper else 'ARMS BELOW BOTTOM', 31, True)
    text(origin+28, 82, 'One upper clamp' if upper else 'One lower clamp', 26, fill='#08798a')
    x0, x1, y0, scale = origin+45, origin+360, 455, 16

    def layer(z, height, label, colour, inset=0):
        top, bottom = y0-(z+height)*scale, y0-z*scale
        d.rectangle((x0+inset, top, x1-inset, bottom), fill=colour, outline=ink, width=2)
        mid = (top+bottom)/2
        d.line((x1-inset, mid, origin+390, mid), fill=ink, width=2)
        text(origin+403, mid-16, label, 25)

    stack_base = 9 if upper else 2
    d.rectangle((origin+130, y0-(stack_base+9)*scale,
                 origin+275, y0-stack_base*scale), fill=amber, outline=ink, width=2)
    text(origin+403, y0-(stack_base+6)*scale, 'FC / ESC stack', 25)
    d.line((origin+275, y0-(stack_base+5)*scale,
            origin+390, y0-(stack_base+5)*scale), fill=ink, width=2)
    layer(0, 2, 'Bottom plate', carbon)
    layer(2 if upper else -5, 5, 'Arms / optional key', arms, 23)
    layer(7 if upper else -7, 2, 'Upper clamp' if upper else 'Lower clamp', carbon, 10)
    text(origin+28, 590, 'FC mounts on upper clamp' if upper else 'FC mounts on bottom plate', 25, True)

im.save(HERE/'SingleClamp0871.png')
