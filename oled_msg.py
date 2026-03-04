#!/usr/bin/env python3
"""Write a centered message to the SH1106 OLED and exit."""
import sys
from smbus import SMBus
from PIL import Image, ImageDraw, ImageFont

I2C_BUS = 1
I2C_ADDR = 0x3C
WIDTH = 128
HEIGHT = 64
COL_OFFSET = 2

bus = SMBus(I2C_BUS)

def cmd(c):
    bus.write_byte_data(I2C_ADDR, 0x00, c)

def data_block(bs):
    for b in bs:
        bus.write_byte_data(I2C_ADDR, 0x40, b)

def display_image(img):
    px = img.load()
    for page in range(8):
        cmd(0xB0 + page)
        col = COL_OFFSET
        cmd(0x00 + (col & 0x0F))
        cmd(0x10 + ((col >> 4) & 0x0F))
        base_y = page * 8
        line = bytearray(WIDTH)
        for x in range(WIDTH):
            b = 0
            for bit in range(8):
                if px[x, base_y + bit]:
                    b |= (1 << bit)
            line[x] = b
        data_block(bytes(line))

msg = " ".join(sys.argv[1:]) or "..."
img = Image.new("1", (WIDTH, HEIGHT), 0)
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf", 14)
except:
    font = ImageFont.load_default()
tw = draw.textlength(msg, font=font)
bbox = font.getbbox(msg)
th = bbox[3] - bbox[1]
draw.text(((WIDTH - tw) // 2, (HEIGHT - th) // 2), msg, 1, font=font)
display_image(img)
