# Victron Battery Display System - Project Summary

## Overview

This is a Raspberry Pi Pico-powered battery monitoring display for Victron battery systems, using the Waveshare RP2350-Touch-LCD-1.28 display.

**Key Features:**
- Real-time battery monitoring with circular gauge
- 4-page display system with touch navigation
- Auto-displays charging page when charging detected
- 10-second auto-return to main battery page
- UART communication from Pico to display

---

## System Architecture

```
┌─────────────────────┐        UART         ┌──────────────────────┐
│  Raspberry Pi Pico  │    115200 baud      │   RP2350 Display     │
│                     ├────────────────────→ │   240×240 Touchscreen│
│  - Reads Victron    │    GPIO0/1 → 17/16  │                      │
│  - VE.Direct        │                     │   - Battery Gauge     │
│  - Processes data   │                     │   - System Info       │
│  - Sends to display │                     │   - Charging Page     │
└─────────────────────┘                     └──────────────────────┘
```

---

## Display Pages

### 1. Battery Monitor (Default Page)
- **Circular gauge**: Shows State of Charge (0-100%)
- **Background image**: Custom background
- **Auto-returns**: All other pages return here after 10 seconds

### 2. System Information
**Displayed Data:**
- State of Charge (%) - Large display
- Battery Voltage (V)
- Current (A) - Color-coded:
  - Green: Charging (positive current)
  - Red: Discharging (negative current)
  - White: Idle (0A)
- Battery Temperature (°C)

### 3. Status Page
**Displayed Data:**
- WiFi Status - Color-coded:
  - Green: Connected/OK/Active
  - Red: Disconnected/Failed/Error
  - White: Unknown
- Demo Mode - Color-coded:
  - Green: Active/ON/Enabled
  - White: Inactive/OFF/Disabled/Unknown

### 4. Charging Page (Auto-appears)
- **Green charging bolt icon**
- **Charging metrics:**
  - Current charging rate (+A)
  - Battery voltage
  - Current SOC percentage
- **Auto-display**: Appears when Pico sends `CHARGING:1`
- **Dismissible**: Touch to cycle pages, or auto-return after 10s

### 5. About Page
- **Application name**: "Victron Battery Display System"
- **Version**: v1.0
- **Developer**: Paul Williams

---

## Navigation

### Touch Controls
- **Touch anywhere on screen**: Cycle through pages
  ```
  Battery → System Info → Status → About → Battery → ...
  ```
- **Charging page**: Only appears when charging active
- **Auto-return timeout**: 10 seconds back to Battery page
- **Debounce**: 500ms between touch events

### No Bottom Button
The previous bottom button mode indicator has been removed. Full-screen touch is now used for all navigation.

---

## UART Communication Protocol

### Commands from Pico to Display

#### Battery State of Charge
```
BATTERY:<soc>\n
```
- **soc**: 0-100 (integer)
- **Example**: `BATTERY:75\n`

#### Battery System Data
```
BATSYS:<voltage>,<current>,<temp>\n
```
- **voltage**: Volts (float, e.g., 48.5)
- **current**: Amps (float, positive=charging, negative=discharging)
- **temp**: Temperature in °C (float)
- **Example**: `BATSYS:48.5,12.3,25.5\n`

#### Charging State
```
CHARGING:<state>\n
```
- **state**: 0=not charging, 1=charging
- **Example**: `CHARGING:1\n`

#### WiFi Status
```
WIFI:<status>\n
```
- **status**: WiFi connection status (string)
- **Example**: `WIFI:Connected\n`
- **Updates**: Status page

#### Demo Mode Status
```
DEMO:<state>\n
```
- **state**: Demo mode status (string)
- **Example**: `DEMO:Active\n`
- **Sent**: Once at startup
- **Updates**: Status page

#### Brightness Control
```
BRIGHT:<level>\n
```
- **level**: 0-100 (integer)
- **Example**: `BRIGHT:75\n`

---

## Hardware Connections

### UART Wiring
```
Pico                    RP2350 Display
────────────────────    ──────────────────
GPIO0 (UART0 TX)   →    GPIO17 (UART0 RX)
GPIO1 (UART0 RX)   ←    GPIO16 (UART0 TX)
GND                ─    GND
```

**Specifications:**
- Baud rate: 115200
- Data bits: 8
- Stop bits: 1
- Parity: None
- Protocol: Newline-terminated ASCII

---

## Pico Integration

### Reading Victron Data
Your Pico should read data from the Victron battery system using the VE.Direct protocol (19200 baud UART). See the [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect) project for reference implementation.

### Example Pico Code
```python
from machine import UART, Pin
import time

# UART to display
display_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Send battery data
def update_display(soc, voltage, current, temp, charging):
    display_uart.write(f"BATTERY:{int(soc)}\n".encode())
    display_uart.write(f"BATSYS:{voltage:.2f},{current:.2f},{temp:.1f}\n".encode())
    display_uart.write(f"CHARGING:{1 if charging else 0}\n".encode())

# Main loop - update every second
while True:
    # Get data from Victron system
    soc = 75  # Read from Victron
    voltage = 48.5
    current = 12.3  # Positive when charging
    temp = 25.5
    charging = (current > 0)

    # Send to display
    update_display(soc, voltage, current, temp, charging)
    time.sleep(1)
```

See `PICO_INTEGRATION.md` for complete integration guide.

---

## File Structure

### Core Files
- **main.py** - Main application with 4-page display system
- **LCD_1inch28.py** - Hardware driver (LCD, Touch, IMU)
- **circular_gauge.py** - Circular gauge module for battery SOC
- **battery_monitor.py** - Battery page with gauge + background
- **image_display.py** - Image background utilities
- **image_data.py** - Background image data
- **bitmap_fonts.py** - 16×24 pixel bitmap fonts
- **bitmap_fonts_32.py** - 24×32 pixel bitmap fonts
- **bitmap_fonts_48.py** - 32×48 pixel bitmap fonts

### Documentation
- **README.md** - Project overview
- **PICO_INTEGRATION.md** - Complete Pico integration guide
- **PROJECT_SUMMARY.md** - This file
- **CLAUDE.md** - Development documentation
- **BITMAP_FONTS_README.md** - Custom font creation guide
- **COLOR_NOTES.md** - Color system technical notes

### Tools
- **convert_image.py** - PC tool to convert images to RGB565 format

---

## Upload to Display

```bash
# Upload all files to RP2350 display
mpremote cp main.py :main.py
mpremote cp LCD_1inch28.py :LCD_1inch28.py
mpremote cp circular_gauge.py :circular_gauge.py
mpremote cp battery_monitor.py :battery_monitor.py
mpremote cp image_display.py :image_display.py
mpremote cp image_data.py :image_data.py
mpremote cp bitmap_fonts.py :bitmap_fonts.py
mpremote cp bitmap_fonts_32.py :bitmap_fonts_32.py
mpremote cp bitmap_fonts_48.py :bitmap_fonts_48.py

# Restart display
mpremote reset
```

---

## Testing

### Manual Testing via REPL
```bash
# Connect to display
mpremote

# Test commands
>>> uart.write(b'BATTERY:75\n')
>>> uart.write(b'BATSYS:48.5,12.3,25.5\n')
>>> uart.write(b'CHARGING:1\n')
```

### Expected Behavior
1. Display starts on Battery page (circular gauge)
2. Touch screen → cycles to System Info page
3. Touch screen → cycles to About page
4. Touch screen → returns to Battery page
5. After 10s of no touch → auto-returns to Battery page
6. When `CHARGING:1` received → auto-switches to Charging page

---

## Key Changes from Original Project

### Removed Features
- ESP32-S3 WiFi bridge (now uses direct Pico UART)
- Home Assistant integration (now Victron-focused)
- Weather, Bedroom, Clock, Hive display modes
- Bottom mode button indicator
- Cycle mode (auto-rotation)

### Added Features
- **4-page battery system**:
  1. Battery Monitor (circular gauge)
  2. System Information (detailed metrics)
  3. Charging (auto-appears when charging)
  4. About (app info and credits)
- **Full-screen touch navigation**
- **10-second auto-return timer** to Battery page
- **Charging auto-detection** and page display
- **Color-coded current display** (green/red for charge/discharge)
- **Direct Pico UART integration**
- **Victron VE.Direct support** (via Pico)

### Modified Behavior
- Touch now cycles through pages (not just bottom button)
- Display always returns to Battery page after 10s
- Charging page appears automatically when charging detected
- All pages use consistent black background

---

## Display Specifications

- **Screen**: 240×240 pixels, round LCD (GC9A01 driver)
- **Touch**: CST816T capacitive touch controller
- **Microcontroller**: RP2350B (264KB RAM, 4MB Flash)
- **Firmware**: MicroPython
- **Color Format**: BRG565 (non-standard, requires conversion)
- **Brightness**: PWM-controlled backlight (0-100%)

---

## Future Enhancements

Potential improvements:
- Battery health (SOH) display
- Charge/discharge history graphs
- Cell voltage monitoring (min/max/delta)
- Alert/alarm indicators
- Configurable thresholds
- Data logging to SD card
- Multiple battery bank support

---

## Credits

**Original Project**: HA-Waveshare-Display (Home Assistant integration)
**Adapted for Victron**: Paul Williams
**Display Hardware**: Waveshare RP2350-Touch-LCD-1.28
**VE.Direct Reference**: [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect)

---

## License

This project is open source. See individual file headers for specific license information.

## Support

For issues or questions:
1. Check `PICO_INTEGRATION.md` for integration details
2. Review troubleshooting section
3. Monitor serial console output with `mpremote`
4. Verify UART connections and baud rates
