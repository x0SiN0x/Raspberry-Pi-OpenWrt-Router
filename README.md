# <img src="https://raw.githubusercontent.com/openwrt/branding/master/logo/openwrt_logo_blue.svg" height="28" alt="OpenWrt"> Raspberry Pi 5 Portable Router

> A Raspberry Pi 5 running OpenWrt, configured as a portable WiFi WAN router with a 1.3" OLED status display and a physical power button.

<p align="center">
  <img src="https://img.shields.io/badge/device-Raspberry_Pi_5-c51a4a?style=flat-square&logo=raspberrypi&logoColor=white" alt="Raspberry Pi 5">
  <img src="https://img.shields.io/badge/OS-OpenWrt_24.10-00a3e0?style=flat-square&logo=openwrt&logoColor=white" alt="OpenWrt">
  <img src="https://img.shields.io/badge/display-SH1106_OLED-333?style=flat-square" alt="SH1106 OLED">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
</p>

---

## Features

- **Automatic uplink detection** — switches between WiFi WAN, USB Ethernet, and tethering
- **Live OLED status** — shows WAN type, IP, client count, throughput, and a scrolling sparkline chart
- **Physical power button** — short press to reboot, long press to shut down, with OLED feedback
- **Managed by OpenWrt init** — procd service with auto-respawn, no systemd

---

## Hardware

| Component | Details |
|-----------|---------|
| **Board** | Raspberry Pi 5 (4GB or 8GB) |
| **OLED Display** | 1.3" SH1106, I2C, 128x64, address `0x3C` |
| **Power Button** | Momentary switch: GPIO17 (Pin 11) → GND (Pin 14) |
| **WAN Uplink** | Built-in WiFi, USB Ethernet dongle, or USB tethering |

### Wiring

```
OLED Display (I2C)          Power Button
┌──────────┐                ┌──────────┐
│ VCC  → Pin 1 (3.3V)      │ Leg 1 → Pin 11 (GPIO17)
│ GND  → Pin 6  (GND)      │ Leg 2 → Pin 14 (GND)
│ SDA  → Pin 3  (GPIO2)    └──────────┘
│ SCL  → Pin 5  (GPIO3)
└──────────┘
```

---

## Installing OpenWrt

### Prerequisites

- Raspberry Pi 5 with up-to-date EEPROM (boot Raspberry Pi OS first and run `sudo rpi-eeprom-update -a` if needed)
- microSD card (8GB+)
- SD card flashing tool ([balenaEtcher](https://etcher.balena.io/), [Raspberry Pi Imager](https://www.raspberrypi.com/software/), or `dd`)

### Steps

1. **Download the OpenWrt image** from the [OpenWrt Firmware Selector](https://firmware-selector.openwrt.org/?version=24.10.0&target=bcm27xx%2Fbcm2712&id=rpi-5). Select the **factory (ext4)** image for a fresh install.

2. **Flash to SD card:**
   ```bash
   # Using dd (replace /dev/sdX with your SD card device)
   gunzip openwrt-bcm27xx-bcm2712-rpi-5-ext4-factory.img.gz
   sudo dd if=openwrt-bcm27xx-bcm2712-rpi-5-ext4-factory.img of=/dev/sdX bs=4M status=progress
   sync
   ```
   Or use balenaEtcher / Raspberry Pi Imager for a GUI approach.

3. **Boot the Pi** — insert the SD card and power on. OpenWrt will boot to a default configuration.

4. **Connect to OpenWrt** — plug an Ethernet cable into the Pi's Ethernet port and navigate to `http://192.168.1.1` in your browser. The default login is `root` with no password.

5. **Set a root password** — go to **System → Administration** and set a password immediately.

6. **(Optional) Configure boot options** — mount the boot partition and edit `config.txt`:
   ```bash
   mount /dev/mmcblk0p1 /boot
   vi /boot/config.txt
   ```
   Useful additions:
   ```ini
   # Enable the onboard power button
   dtparam=pwr_led_trigger=default-on

   # Enable active cooling (fan spins up at 50°C)
   dtparam=fan_temp0=50000
   dtparam=fan_temp0_hyst=5000
   ```

For more details, see the [OpenWrt Raspberry Pi 5 installation guide](https://openwrt.org/toh/raspberry_pi_foundation/raspberry_pi).

---

## Adding a USB Network Adapter

The Pi 5 has one Ethernet port. To use it as a proper router (WAN + LAN), you need a second network interface via USB. Once the adapter is recognized, configure it through the OpenWrt web UI at **Network → Interfaces**.

### USB Ethernet Adapters

Most USB Ethernet dongles use Realtek or ASIX chipsets. Install the matching driver:

```bash
opkg update

# Realtek RTL8152/RTL8153 (most common USB 3.0 gigabit adapters)
opkg install kmod-usb-net-rtl8152

# ASIX AX88179 (another common USB 3.0 gigabit chipset)
opkg install kmod-usb-net-asix-ax88179

# Generic CDC Ethernet (for adapters that present as CDC devices)
opkg install kmod-usb-net-cdc-ether
```

After installing, plug in the adapter and verify it appears:
```bash
ip link show
# Look for a new eth1 or enXXX device
```

### USB WiFi Adapters

USB WiFi support on OpenWrt depends heavily on the chipset. **MediaTek chipsets have the best support** — avoid Realtek-based USB WiFi adapters as their out-of-kernel drivers are problematic.

```bash
opkg update

# MediaTek MT7921U (recommended — WiFi 6, well-supported)
opkg install kmod-mt7921u

# MediaTek MT7612U (WiFi 5, mature driver)
opkg install kmod-mt76x2u

# MediaTek MT7610U (WiFi 5, budget option)
opkg install kmod-mt76x0u

# Ralink RT5370 (WiFi 4, very common in cheap dongles)
opkg install kmod-rt2800-usb
```

After installing, verify the adapter is detected:
```bash
ip link show
# Look for wlan1 or similar

# Check available wireless devices
iwinfo
```

Then configure via **Network → Wireless** in the OpenWrt web UI.

> **Tip:** If you're buying a USB WiFi adapter specifically for OpenWrt, look for one with a **MediaTek MT7921U** chipset. It supports WiFi 6, has in-kernel drivers, and works reliably.

---

## Installation

### 1. Install Required Packages

```bash
opkg update
opkg install \
  python3 python3-pillow python3-smbus \
  kmod-i2c-bcm2835 i2c-tools \
  kmod-gpio-button-hotplug \
  dejavu-fonts-ttf-DejaVuSans
```

| Package | Purpose |
|---------|---------|
| `python3` `python3-pillow` `python3-smbus` | Python runtime, image rendering, I2C communication |
| `kmod-i2c-bcm2835` `i2c-tools` | I2C kernel driver and diagnostic tools |
| `kmod-gpio-button-hotplug` | GPIO button detection for the power button |
| `dejavu-fonts-ttf-DejaVuSans` | TrueType font used by the OLED display |

### 2. Verify I2C

Confirm the OLED is detected at address `0x3C` on bus 1:

```bash
i2cdetect -y 1
```

Expected output shows `3c` in the grid:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
...
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
...
```

### 3. Deploy Files

Copy the project files to the Pi:

```bash
# From your local machine
scp oled_status.py oled_msg.py root@192.168.1.1:/root/
scp oled root@192.168.1.1:/etc/init.d/
scp power root@192.168.1.1:/etc/rc.button/
```

Set permissions on the Pi:

```bash
chmod +x /etc/init.d/oled
chmod +x /etc/rc.button/power
chmod +x /root/oled_msg.py
```

### 4. Enable and Start the OLED Service

```bash
/etc/init.d/oled enable   # auto-start on boot
/etc/init.d/oled start    # start now
```

### 5. Verify

The OLED should display the current network status. Test the power button:

```bash
# Check OLED service is running
/etc/init.d/oled status

# Watch power button logs
logread -f | grep powerbtn
# Then press the button briefly — should log "Short press -> reboot"
```

---

## File Reference

| File | Deploys to | Description |
|------|-----------|-------------|
| [`oled_status.py`](oled_status.py) | `/root/oled_status.py` | Main OLED display daemon — shows WAN status, clients, speed, and sparkline chart |
| [`oled_msg.py`](oled_msg.py) | `/root/oled_msg.py` | One-shot OLED message helper — displays centered text (used by power script) |
| [`oled`](oled) | `/etc/init.d/oled` | Procd init script — manages the OLED daemon with auto-respawn |
| [`power`](power) | `/etc/rc.button/power` | Power button handler — reboot/shutdown with OLED feedback |

---

## OLED Display Layout

The 128x64 pixel display shows four lines of information plus a throughput chart:

```
┌────────────────────────────────┐
│ WIFI: 192.168.1.105            │  ← WAN type + IP
│ Clients: 3                     │  ← Connected devices
│      ↑1.2 / ↓15.4 Mbps        │  ← Upload / Download speed
│ ▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇ │  ← Scrolling sparkline (combined throughput)
└────────────────────────────────┘
```

- **Sparkline** auto-scales to peak throughput and scrolls right-to-left
- History resets when the active WAN interface changes
- Display retains the last image when powered off (shows shutdown message)

---

## Power Button Behavior

| Action | Result |
|--------|--------|
| Short press (~1s) | OLED shows "Rebooting..." → clean reboot |
| Long press (~3s) | OLED shows "Shutting down..." → clean shutdown |

### Wake-from-Halt Limitation (Pi 5)

GPIO17 **cannot** wake the Pi 5 from halt. On the Pi 5, all 40-pin header GPIOs route through the RP1 southbridge, which is unpowered in halt state. The `WAKE_ON_GPIO` and `gpio-shutdown` overlay from Pi 1–4 have no effect on Pi 5.

**To restart after shutdown:**

1. Press the **onboard Pi 5 power button** (small tactile switch near USB-C)
2. **Power-cycle** — unplug and replug the USB-C power supply
3. *(Hardware mod)* Solder the button to the **J2 pads** on the Pi 5 board — these connect directly to the PMIC and can wake from halt

---

## Service Management

```bash
/etc/init.d/oled start     # Launch the display daemon
/etc/init.d/oled stop      # Stop the daemon
/etc/init.d/oled restart   # Restart (useful after editing the script)
/etc/init.d/oled enable    # Enable auto-start on boot
/etc/init.d/oled disable   # Disable auto-start
```

The OLED daemon is managed by procd with auto-respawn. If it crashes, procd restarts it automatically (up to 5 times within an hour). Errors are logged to syslog:

```bash
logread | grep oled
```

---

## Acknowledgments

This project was inspired by [Spencer's Desk — Anti-ISP Raspberry Pi Router](https://spencersdesk.com/projects/anti-isp-raspberry-pi-router). Thank you to Spencer for sharing the idea, the 3D printable case files (available on [Printables](https://www.printables.com/model/1386188-raspberry-pi-router)), and the write-up that kicked this project off.
