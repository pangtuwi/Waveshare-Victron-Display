# Victron Battery Display System

A MicroPython project for the Waveshare RP2350-Touch-LCD-1.28 display that shows real-time Victron battery system data received from a Raspberry Pi Pico via UART.

![Waveshare RP2350-Touch-LCD-1.28](https://www.waveshare.com/img/devkit/RP2350-Touch-LCD-1.28/RP2350-Touch-LCD-1.28-1.jpg)

## Features

### 5-Page Display System
- **Battery Monitor** - Circular gauge showing State of Charge (0-100%) with background image
- **System Information** - Detailed metrics: SOC, Voltage, Current, Temperature
- **Status** - WiFi connection and Demo mode status
- **Charging** - Auto-displays when charging with green charging bolt icon
- **About** - Application information and credits

### Interaction
- **Full-Screen Touch Navigation** - Touch anywhere to cycle through pages
- **Auto-Return** - Returns to Battery page after 10 seconds
- **Smart Charging Detection** - Charging page appears automatically
- **Color-Coded Current** - Green for charging, Red for discharging

### Display Features
- **Custom Bitmap Fonts** - Crisp 16×24, 24×32, and 32×48 pixel fonts for large numbers
- **Circular Gauge** - Segmented arc display for battery SOC
- **Background Images** - Customizable 240×240 pixel backgrounds
- **Real-Time Updates** - 1-second update rate from Pico

## Hardware

**Waveshare RP2350-Touch-LCD-1.28 Display**
- 240×240 pixel round LCD display (GC9A01 driver)
- CST816T capacitive touch controller
- QMI8658 6-axis IMU (accelerometer + gyroscope)
- RP2350B microcontroller running MicroPython

**Raspberry Pi Pico**
- Reads Victron battery data via VE.Direct protocol (19200 baud)
- Processes and sends formatted data to display (115200 baud)
- Connects via UART (GPIO0/1 to Display GPIO17/16)

## Architecture

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

## Quick Start

### 1. Install MicroPython Firmware on RP2350

1. Hold the BOOTSEL button on the RP2350
2. Connect USB cable to your computer
3. Copy `WAVESHARE_RP2350B.uf2` to the mounted drive
4. Device will reboot with MicroPython installed

### 2. Upload Project Files to RP2350

Using `mpremote`:

```bash
mpremote cp main.py :main.py
mpremote cp LCD_1inch28.py :LCD_1inch28.py
mpremote cp circular_gauge.py :circular_gauge.py
mpremote cp battery_monitor.py :battery_monitor.py
mpremote cp image_display.py :image_display.py
mpremote cp image_data.py :image_data.py
mpremote cp bitmap_fonts.py :bitmap_fonts.py
mpremote cp bitmap_fonts_32.py :bitmap_fonts_32.py
mpremote cp bitmap_fonts_48.py :bitmap_fonts_48.py
```

The code will auto-run on power-up since it's named `main.py`.

### 3. Connect Hardware

Connect the Pico to the RP2350 display via UART:
```
Pico                    RP2350 Display
────────────────────    ──────────────────
GPIO0 (UART0 TX)   →    GPIO17 (UART0 RX)
GPIO1 (UART0 RX)   ←    GPIO16 (UART0 TX)
GND                ─    GND
```

### 4. Program Your Raspberry Pi Pico

See `PICO_INTEGRATION.md` for complete integration guide with Victron VE.Direct protocol.

**Basic Example:**
```python
from machine import UART, Pin
import time

# UART to display
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Update display with battery data
def update_display(soc, voltage, current, temp, charging):
    uart.write(f"BATTERY:{int(soc)}\n".encode())
    uart.write(f"BATSYS:{voltage:.2f},{current:.2f},{temp:.1f}\n".encode())
    uart.write(f"CHARGING:{1 if charging else 0}\n".encode())

# Main loop
while True:
    # Read from Victron system (VE.Direct protocol)
    soc = 75  # State of charge 0-100%
    voltage = 48.5  # Voltage in V
    current = 12.3  # Current in A (+ = charging, - = discharging)
    temp = 25.5  # Temperature in °C
    charging = (current > 0)

    # Send to display
    update_display(soc, voltage, current, temp, charging)
    time.sleep(1)
```

## UART Command Protocol

Commands are line-delimited ASCII strings sent from Pico to RP2350:

### Battery Data Commands

**Battery State of Charge**
```
BATTERY:<soc>\n
```
- **soc**: State of Charge (0-100)
- **Example**: `BATTERY:75\n`

**Battery System Data**
```
BATSYS:<voltage>,<current>,<temp>\n
```
- **voltage**: Battery voltage in volts (e.g., 48.5)
- **current**: Current in amps (positive=charging, negative=discharging)
- **temp**: Battery temperature in °C
- **Example**: `BATSYS:48.5,12.3,25.5\n`

**Charging State**
```
CHARGING:<state>\n
```
- **state**: 0=not charging, 1=charging
- **Example**: `CHARGING:1\n`
- **Auto-displays**: Charging page when state changes to 1

**WiFi Status**
```
WIFI:<status>\n
```
- **status**: WiFi connection status (string)
- **Example**: `WIFI:Connected\n`
- **Updates**: Status page

**Demo Mode Status**
```
DEMO:<state>\n
```
- **state**: Demo mode status (string)
- **Example**: `DEMO:Active\n`
- **Sent**: Once at startup
- **Updates**: Status page

**Brightness Control**
```
BRIGHT:<level>\n
```
- **level**: Brightness 0-100
- **Example**: `BRIGHT:75\n`

## Display Pages

### 1. Battery Monitor (Default)
- Circular gauge showing SOC (0-100%)
- Background image
- Auto-returns to this page after 10 seconds of inactivity
- Updates via `BATTERY:<soc>` command

### 2. System Information
- **SOC** - State of Charge percentage
- **Voltage** - Battery voltage in volts (2 decimal places)
- **Current** - Current in amps (2 decimal places, color-coded: Green=charging, Red=discharging, White=idle)
- **Temperature** - Battery temperature in °C (1 decimal place)
- Updates via `BATSYS:<voltage>,<current>,<temp>` command
- All values displayed in consistent font size

### 3. Status
- **WiFi Status** - Color-coded (Green=connected, Red=disconnected, White=unknown)
- **Demo Mode** - Color-coded (Green=active, White=inactive/unknown)
- Updates via `WIFI:<status>` and `DEMO:<state>` commands

### 4. Charging (Auto-appears)
- Charging current in amps (1 decimal place, green)
- Battery voltage in volts (1 decimal place)
- Current SOC percentage
- Battery temperature in °C (1 decimal place)
- Automatically displayed when `CHARGING:1` received
- Remains visible while actively charging (no auto-return)
- Returns to Battery page 10s after charging stops

### 5. About
- Application name: "Victron Battery Display System"
- Version: v1.0
- Developer: Paul Williams

## Page Navigation

- **Touch anywhere on screen** → Next page (Battery → System Info → Status → About → Battery → ...)
- **10 seconds idle** → Auto-return to Battery page
- **Charging detected** → Auto-show Charging page
- **500ms debounce** → Prevents accidental double-touches

## Project Structure

```
.
├── main.py                      # Main application with 4-page display system
├── LCD_1inch28.py               # Hardware driver library (LCD, Touch, IMU)
├── circular_gauge.py            # Circular gauge/progress display module
├── battery_monitor.py           # Battery SOC display with circular gauge
├── image_display.py             # Image display utilities
├── image_data.py                # Storage for converted images
├── bitmap_fonts.py              # 16×24 pixel bitmap font
├── bitmap_fonts_32.py           # 24×32 pixel bitmap font
├── bitmap_fonts_48.py           # 32×48 pixel bitmap font
├── convert_image.py             # PC tool to convert JPG/PNG to RGB565
├── jtj.py                       # Standalone SOC display (for testing)
├── screentest.py                # Display feature test suite
├── PICO_INTEGRATION.md          # Complete Pico integration guide
├── PROJECT_SUMMARY.md           # Full project documentation
├── QUICK_REFERENCE.md           # Command reference card
├── BITMAP_FONTS_README.md       # Custom bitmap font creation guide
├── COLOR_NOTES.md               # Color system technical documentation
├── CLAUDE.md                    # Development documentation
└── README.md                    # This file
```

## Development

### Monitor Serial Output

```bash
mpremote  # Opens REPL, shows print() output
```

### Run Code Manually

```bash
mpremote run main.py
```

### Testing Commands

Send test commands via UART in REPL:

```python
# Test SOC update
uart.write(b'BATTERY:75\n')

# Test system data
uart.write(b'BATSYS:48.5,12.3,25.5\n')

# Test charging state
uart.write(b'CHARGING:1\n')

# Test WiFi status
uart.write(b'WIFI:Connected\n')

# Test demo mode
uart.write(b'DEMO:Active\n')

# Test brightness
uart.write(b'BRIGHT:50\n')
```

## Circular Gauge Module

The `circular_gauge.py` module provides a flexible `CircularGauge` class for creating segmented arc displays perfect for visualizing percentage values (0-100%).

### Features

- **Configurable segments**: 4-20 segments
- **Flexible angles**: Position arcs anywhere (top, bottom, full circle)
- **Adjustable appearance**: Thickness, gaps, colors
- **Direction control**: Counter-clockwise (default) or clockwise
- **Performance optimized**: Suitable for 1-second updates

### Example Usage

**Bottom arc gauge (used for battery display):**
```python
from circular_gauge import CircularGauge

gauge = CircularGauge(
    lcd=lcd,
    center_x=120, center_y=120,
    radius=115, thickness=10,
    segments=20,
    start_angle=215,  # Bottom-left
    end_angle=320,    # Bottom-right
    gap_degrees=2,
    clockwise=True,
    color=0xFFFF,     # White
    background_color=0xE67AE6  # Magenta
)
gauge.update(75)  # Set to 75% and draw
lcd.show()
```

### Methods

- `set_value(percentage)` - Set value (0-100)
- `draw()` - Draw gauge to buffer
- `update(percentage)` - Set and draw in one call

## Bitmap Fonts

Custom bitmap fonts for crisp, large number displays:

- **bitmap_fonts.py**: 16×24 pixel font (digits 0-9, colon)
- **bitmap_fonts_32.py**: 24×32 pixel font (digits 0-9, colon)
- **bitmap_fonts_48.py**: 32×48 pixel font (digits 0-9, colon)

### Example Usage

```python
import bitmap_fonts

# Draw large time
time_str = "12:34"
time_width = bitmap_fonts.get_text_width(time_str, spacing=4)
time_x = (240 - time_width) // 2  # Center on screen
bitmap_fonts.draw_text(lcd, time_str, time_x, 100, lcd.white, spacing=4)
```

See `BITMAP_FONTS_README.md` for creating custom fonts.

## Customization

### Adding New Display Pages

1. Add page name to `cycle_mode()` modes list in `main.py`
2. Add display logic in `update_display_for_mode()`
3. Add UART command handler if needed for new data
4. Update page cycling order

### Adding New Data Sources

1. Add global variables in `main.py`
2. Create UART command handler in `process_command()`
3. Update display page to show new data
4. Add Pico code to send new data

### Creating Custom Background Images

1. Create a 240×240 pixel image (JPG or PNG)
2. Convert using the provided script:
   ```bash
   python convert_image.py your_image.jpg battery_bg > output.py
   ```
3. Copy the output to `image_data.py` on the display
4. Update `battery_monitor.py` to use the new image

## Troubleshooting

**Display not updating:**
1. Check UART connections (TX→RX, RX→TX, GND→GND)
2. Verify baud rate is 115200 on both devices
3. Ensure commands are newline-terminated (`\n`)
4. Monitor display console with `mpremote`

**Touch not working:**
1. Touch anywhere on screen, not just edges
2. Wait 500ms between touches (debounce delay)
3. Check touch controller initialization in console

**Charging page not appearing:**
1. Verify `CHARGING:1` command is being sent
2. Check Pico charging detection logic
3. Monitor console for "Charging started" message

**Wrong data displayed:**
1. Verify command format matches protocol exactly
2. Check data types (SOC=integer, voltage/current=float)
3. Test with manual commands via REPL

## Documentation

- **PICO_INTEGRATION.md** - Complete guide for Raspberry Pi Pico integration with VE.Direct
- **PROJECT_SUMMARY.md** - Full project overview and technical details
- **QUICK_REFERENCE.md** - Command reference card for quick lookup
- **BITMAP_FONTS_README.md** - Guide for creating custom bitmap fonts
- **COLOR_NOTES.md** - Technical color system documentation

## Implemented Features

✅ **Complete**:
1. 4-page display system (Battery, SystemInfo, Charging, About)
2. Full-screen touch navigation with page cycling
3. 10-second auto-return to Battery page
4. Charging page auto-detection and display
5. Custom bitmap fonts for large, crisp displays (16×24, 24×32, 32×48)
6. Circular gauge module for battery SOC visualization
7. Color-coded current display (green=charging, red=discharging)
8. Battery monitor with background image
9. Image display system with gamma correction
10. UART communication protocol for Pico integration
11. Real-time battery system monitoring (1-second updates)
12. Comprehensive documentation and integration guides

## Future Enhancements

Potential improvements:
- Battery health (SOH) display
- Charge/discharge history graphs
- Cell voltage monitoring (min/max/delta)
- Alert/alarm indicators
- Configurable thresholds
- Data logging capability
- Multiple battery bank support

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Credits

**Original Project**: HA-Waveshare-Display (Home Assistant integration)
**Adapted for Victron**: Paul Williams
**Display Hardware**: Waveshare RP2350-Touch-LCD-1.28
**VE.Direct Reference**: [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect)

## License

This project is open source. Please check individual file headers for specific license information.

## Resources

- [Victron VE.Direct Protocol](https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.33.pdf)
- [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect)
- [Waveshare RP2350 Display Wiki](https://www.waveshare.com/wiki/RP2350-Touch-LCD-1.28)
- [MicroPython Documentation](https://docs.micropython.org/)
