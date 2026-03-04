#!/usr/bin/env python3
import time
import subprocess
from smbus import SMBus
from PIL import Image, ImageDraw, ImageFont

I2C_BUS = 1
I2C_ADDR = 0x3C
WIDTH = 128
HEIGHT = 64
PAGES = 8
COL_OFFSET = 2
REFRESH_SEC = 2

bus = SMBus(I2C_BUS)

def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
    except:
        return ""

def cmd(c):
    bus.write_byte_data(I2C_ADDR, 0x00, c)

def data_block(bs):
    for b in bs:
        bus.write_byte_data(I2C_ADDR, 0x40, b)

def init_sh1106():
    seq = [
        0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,
        0xAD,0x8B,0xA1,0xC8,0xDA,0x12,
        0x81,0x7F,0xD9,0xF1,0xDB,0x40,
        0xA4,0xA6,0xAF
    ]
    for c in seq:
        cmd(c)

def set_page(page):
    cmd(0xB0 + page)
    col = COL_OFFSET
    cmd(0x00 + (col & 0x0F))
    cmd(0x10 + ((col >> 4) & 0x0F))

def display_image(img):
    px = img.load()
    for page in range(PAGES):
        set_page(page)
        base_y = page * 8
        line = bytearray(WIDTH)
        for x in range(WIDTH):
            b = 0
            for bit in range(8):
                if px[x, base_y + bit]:
                    b |= (1 << bit)
            line[x] = b
        data_block(bytes(line))

def active_dev():
    return sh("ip route | awk '$1==\"default\" {for(i=1;i<=NF;i++) if($i==\"dev\") {print $(i+1); exit}}'")

def ip4(dev):
    return sh(f"ip -4 addr show dev {dev} | awk '/inet /{{print $2; exit}}' | cut -d/ -f1")

def read_bytes(dev):
    try:
        with open(f"/sys/class/net/{dev}/statistics/rx_bytes") as f:
            rx = int(f.read().strip())
        with open(f"/sys/class/net/{dev}/statistics/tx_bytes") as f:
            tx = int(f.read().strip())
        return rx, tx
    except:
        return None, None

def fmt(bps):
    mbps = (bps * 8) / 1_000_000
    return f"{mbps:.1f}"

def clients():
    try:
        with open("/proc/net/arp") as f:
            return len(f.read().splitlines()) - 1
    except:
        return 0

CHART_Y = 46
CHART_H = HEIGHT - CHART_Y  # 18px tall
CHART_W = WIDTH              # 128 samples = 128 columns

def draw_chart(draw, history):
    if len(history) < 2:
        return
    peak = max(history)
    if peak <= 0:
        return
    pts = []
    x_start = CHART_W - len(history)
    for i, val in enumerate(history):
        x = x_start + i
        y = CHART_Y + CHART_H - 1 - int((val / peak) * (CHART_H - 1))
        pts.append((x, y))
    draw.line(pts, fill=1)

def main():
    init_sh1106()
    font = ImageFont.truetype("/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf", 10)
    last_rx = last_tx = None
    last_time = time.time()
    last_dev = None
    speed_history = []

    while True:
        dev = active_dev()
        ip = ip4(dev) if dev else ""
        now = time.time()
        dt = max(1, now - last_time)
        rx, tx = read_bytes(dev) if dev else (None, None)

        if dev != last_dev:
            last_rx = last_tx = None
            speed_history.clear()

        if rx is None or last_rx is None:
            combined_bps = 0
            down = up = "0"
        else:
            rx_bps = max(0, rx - last_rx) / dt
            tx_bps = max(0, tx - last_tx) / dt
            combined_bps = rx_bps + tx_bps
            down = fmt(rx_bps)
            up = fmt(tx_bps)

        speed_history.append(combined_bps)
        if len(speed_history) > CHART_W:
            speed_history.pop(0)

        img = Image.new("1", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(img)

        if not dev:
            wan_label = "---"
        elif dev.startswith("eth") or dev.startswith("end"):
            wan_label = "ETH"
        else:
            wan_label = "WIFI"
        draw.text((0,0),  f"{wan_label}: {ip or 'no link'}", 1, font=font)
        draw.text((0,16), f"Clients: {clients()}", 1, font=font)
        speed_text = f"\u2191{up} / \u2193{down} Mbps"
        tw = draw.textlength(speed_text, font=font)
        draw.text(((WIDTH - tw) // 2, 32), speed_text, 1, font=font)

        draw_chart(draw, speed_history)

        display_image(img)

        last_dev = dev
        last_rx, last_tx = rx, tx
        last_time = now
        time.sleep(REFRESH_SEC)

if __name__ == "__main__":
    main()
