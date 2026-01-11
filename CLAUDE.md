# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Victron Battery Display System

A MicroPython project for the Waveshare RP2350-Touch-LCD-1.28 display that shows Victron battery system data received from a Raspberry Pi Pico via UART communication.

**Hardware**: Waveshare RP2350-Touch-LCD-1.28
- 240×240 pixel round LCD display (GC9A01 driver)
- CST816T capacitive touch controller
- QMI8658 6-axis IMU (accelerometer + gyroscope)
- RP2350B microcontroller running MicroPython

**Current Version**: v1.0

## Project Purpose

This display system receives Victron battery data from a Raspberry Pi Pico and displays it across 4 pages:
1. **Battery Monitor** - Circular gauge showing SOC (State of Charge)
2. **System Information** - Detailed battery metrics (SOC, voltage, current, temperature)
3. **Charging** - Auto-displays when battery is charging
4. **About** - Application information

## Project Structure

### Core Files
- `main.py` - Main application with 4-page battery display system
- `LCD_1inch28.py` - Hardware driver library (LCD, Touch, IMU)
- `circular_gauge.py` - Circular gauge/progress display module with segmented arcs
- `battery_monitor.py` - Battery SOC display module using circular gauge with background image
- `bitmap_fonts.py` - 16×24 pixel bitmap font for digits and colon
- `bitmap_fonts_32.py` - 24×32 pixel bitmap font for larger displays
- `bitmap_fonts_48.py` - 32×48 pixel bitmap font for extra large displays

### Image Display System
- `convert_image.py` - PC tool to convert JPG/PNG to RGB565 with BRG format and gamma correction
- `image_data.py` - Storage for converted image byte arrays (chunked format for memory efficiency)
- `image_display.py` - Display utilities for backgrounds with text/graphics overlays
- `COLOR_NOTES.md` - Complete color system documentation and hardware limitations

### Test Files
- `jtj.py` - Standalone SOC display with simulated data (for testing)
- `screentest.py` - Comprehensive test suite for display features and CircularGauge
- `color_calibration.py` - Color accuracy test suite with gamma correction
- `old_color_tests/` - Diagnostic test scripts from color system development

### Documentation
- `README.md` - Project overview and quick start guide
- `PICO_INTEGRATION.md` - Complete Raspberry Pi Pico integration guide
- `PROJECT_SUMMARY.md` - Full project documentation
- `QUICK_REFERENCE.md` - Command reference card
- `BITMAP_FONTS_README.md` - Guide for creating custom bitmap fonts
- `COLOR_NOTES.md` - Color system technical documentation

### Legacy Files (From Original Project)
- `old_main.py` - Backup of main.py before Victron adaptation
- `ESP32-s3.YAML` - ESPHome configuration (legacy Home Assistant integration)
- `home_assistant_automation.yaml` - Example Home Assistant automations (legacy)
- `DISPLAY_INTEGRATION.md` - Battery monitor integration guide (legacy)

## Hardware Communication

### UART Connection
The project uses direct UART communication:
1. **Raspberry Pi Pico** reads Victron battery data (VE.Direct protocol at 19200 baud)
2. **Pico** processes data and sends formatted commands to display (115200 baud)
3. **RP2350 Display** receives commands via UART (GPIO16/17) and updates display

### Wiring
```
Pico                    RP2350 Display
────────────────────    ──────────────────
GPIO0 (UART0 TX)   →    GPIO17 (UART0 RX)
GPIO1 (UART0 RX)   ←    GPIO16 (UART0 TX)
GND                ─    GND
```

### UART Command Protocol
Commands are line-delimited ASCII strings sent from Pico to RP2350:

**Battery Data Commands**:
- `BATTERY:<soc>` - Update battery State of Charge (0-100%)
  - Example: `BATTERY:75\n`
- `BATSYS:<voltage>,<current>,<temp>` - Update battery system data
  - voltage: Battery voltage in volts (e.g., 48.5)
  - current: Current in amps (positive=charging, negative=discharging)
  - temp: Battery temperature in °C
  - Example: `BATSYS:48.5,12.3,25.5\n`
- `CHARGING:<state>` - Update charging state (0=not charging, 1=charging)
  - Example: `CHARGING:1\n`
  - Auto-displays Charging page when state changes to 1

**Configuration Commands**:
- `BRIGHT:<0-100>` - Set brightness percentage (0-100)
  - Example: `BRIGHT:75\n`
- `MODE:<mode_name>` - Set display mode (Battery/SystemInfo/Charging/About)
  - Example: `MODE:SystemInfo\n`
  - Note: Touch navigation is preferred; use only for testing

## Display Pages

### 1. Battery Monitor (Default Page)
- **Circular gauge** showing State of Charge (0-100%)
- **Background image** (customizable)
- **Auto-return**: All other pages return here after 10 seconds of inactivity
- Updated via `BATTERY:<soc>` command

### 2. System Information
- **State of Charge (%)** - Large display using 24×32 bitmap font
- **Voltage (V)** - Battery voltage
- **Current (A)** - Color-coded:
  - Green: Charging (positive current)
  - Red: Discharging (negative current)
  - White: Idle (0A)
- **Temperature (°C)** - Battery temperature
- Updated via `BATSYS:<voltage>,<current>,<temp>` command

### 3. Charging Page (Auto-appears)
- **Green charging bolt icon**
- **Charging metrics**:
  - Current charging rate (+A)
  - Battery voltage (V)
  - Current SOC (%)
- **Auto-display**: Appears when `CHARGING:1` received
- **Auto-dismiss**: Returns to Battery page after 10s or when charging stops

### 4. About Page
- **Application name**: "Victron Battery Display System"
- **Version**: v1.0
- **Developer**: Paul Williams

## Page Navigation

### Touch Controls
- **Touch anywhere on screen**: Cycle through pages
  ```
  Battery → System Info → About → Battery → ...
  ```
- **Charging page**: Only appears when charging is active
- **Auto-return**: All pages return to Battery page after 10 seconds
- **Debounce**: 500ms between touch events

### Navigation Behavior
- No bottom button (full-screen touch navigation)
- Touch to cycle: Battery → SystemInfo → About → Battery
- Charging page auto-appears and is not in normal cycle
- 10-second timeout returns to Battery page from any other page

## Development Commands

### Uploading Firmware
1. Hold BOOTSEL button on RP2350
2. Connect USB cable
3. Copy `WAVESHARE_RP2350B.uf2` to mounted drive
4. Device will reboot with MicroPython installed

### Uploading Code to Device
Use `mpremote` to copy all required files:
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

### Running the Application
Code auto-runs on boot when saved as `main.py`. To test manually:
```bash
mpremote run main.py
```

### Monitoring UART Communication
```bash
mpremote  # Opens REPL, shows print() output
```

### Testing Commands
Send test commands via REPL:
```python
# Test SOC update
uart.write(b'BATTERY:75\n')

# Test system data
uart.write(b'BATSYS:48.5,12.3,25.5\n')

# Test charging state
uart.write(b'CHARGING:1\n')

# Test brightness
uart.write(b'BRIGHT:50\n')
```

## Important Implementation Notes

### Display Buffer and Memory
- Frame buffer requires 115,200 bytes (240×240×2 bytes for RGB565)
- Call `lcd.show()` to push buffer to display (blocks briefly during SPI transfer)
- Use `Windows_show(x1, y1, x2, y2)` for partial updates (more efficient)

### Color Format
The driver uses BRG format (not RGB) due to MicroPython framebuf:
- `lcd.red = 0x07E0` (actually displays green)
- `lcd.green = 0x001f` (actually displays blue)
- `lcd.blue = 0xf800` (actually displays red)
- BRG565 format: Blue(15-11), Red(10-5), Green(4-0)
- Conversion: `((b & 0xF8) << 8) | ((r & 0xFC) << 3) | (g >> 3)`

**Gamma Correction Required:**
For intermediate color values, gamma correction (gamma=2.2) is required:
```python
def apply_gamma_correction(value, gamma=2.2):
    normalized = value / 255.0
    corrected = pow(normalized, 1.0 / gamma)
    return int(corrected * 255.0)
```

**Hardware Limitations:**
- ⚠️ Grayscale (equal R=G=B values) is fundamentally broken at intermediate values
- Root cause: Display has mismatched per-channel hardware gamma curves
- Only works at: 0 (black), 64, 255 (white) - other values show green/purple artifacts
- **Cannot be fixed in software** - use colored designs instead of grayscale
- See COLOR_NOTES.md for complete details and testing results

### UART Communication
- Baudrate: 115200
- RP2350: TX=GPIO16, RX=GPIO17
- Pico: TX=GPIO0, RX=GPIO1 (or any UART-capable pins)
- Commands must be newline-terminated (`\n`)
- Always decode bytes: `cmd_line.decode().strip()`
- Wrap command processing in try/except to prevent crashes

### Touch Handling
- Touch coordinates: (0-239, 0-239) for 240×240 display
- Mode: point mode (mode=1)
- Poll `touch.Flag` for new touch events (interrupt-driven)
- Access coordinates via `touch.X_point`, `touch.Y_point`
- 500ms debounce using `time.ticks_ms()` and `time.ticks_diff()`
- Full-screen touch cycles through pages (no button area)

### Display Text Rendering
- `lcd.text(str, x, y, color)` - Standard 8×8 font
- `lcd.write_text(str, x, y, size, color)` - Scalable font (size multiplier)
- `bitmap_fonts.draw_text(lcd, text, x, y, color, spacing)` - 16×24 bitmap font
- `bitmap_fonts_32.draw_text_32(lcd, text, x, y, color, spacing)` - 24×32 bitmap font
- `bitmap_fonts_48.draw_text_48(lcd, text, x, y, color, spacing)` - 32×48 bitmap font
- Bitmap fonts provide crisp, professional-looking large numbers

## Circular Gauge Module (circular_gauge.py)

**CircularGauge class** - Progressive fill circular gauge/progress indicator:
- Displays values as segmented arcs around the display perimeter
- Configurable parameters:
  - **Segments**: 4-20 segments (validated and clamped)
  - **Angles**: Start/end angles in degrees (supports wraparound >360°)
  - **Thickness**: Arc thickness in pixels
  - **Gap**: Gap between segments in degrees
  - **Colors**: Foreground (filled) and background (unfilled) segments
  - **Direction**: Counter-clockwise (default) or clockwise drawing

**Angle System**:
- 0° = Right (3 o'clock)
- 90° = Top (12 o'clock)
- 180° = Left (9 o'clock)
- 270° = Bottom (6 o'clock)

**Example - Bottom arc gauge (used for battery)**:
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

**Methods**:
- `set_value(percentage)` - Set gauge value (0-100)
- `draw()` - Draw gauge to LCD buffer
- `update(percentage)` - Set value and draw in one call

**Helper function**:
- `rgb_to_brg565(r, g, b)` - Convert RGB888 to BRG565 format for correct color display

## Raspberry Pi Pico Integration

### Reading Victron Data
Your Pico should read data from the Victron battery system using the VE.Direct protocol (19200 baud UART). See:
- [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect)
- [Victron VE.Direct Protocol Whitepaper](https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.33.pdf)

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

# Main loop
while True:
    # Read from Victron system (VE.Direct protocol)
    soc = 75  # State of charge 0-100%
    voltage = 48.5  # Battery voltage in V
    current = 12.3  # Current in A (positive=charging, negative=discharging)
    temp = 25.5  # Temperature in °C
    charging = (current > 0)

    # Send to display
    update_display(soc, voltage, current, temp, charging)
    time.sleep(1)  # Update every second
```

See `PICO_INTEGRATION.md` for complete integration guide with VE.Direct parsing.

## Extending the Project

### Adding New Display Pages
1. Add page name to `cycle_mode()` modes list in main.py
2. Add `elif mode == "NewPage":` section in `update_display_for_mode()`
3. Implement display layout using `lcd.text()`, `lcd.write_text()`, or bitmap fonts
4. Add UART command handler if new data is needed

### Adding New Data Fields
1. Add global variables for data storage in main.py
2. Add to `process_command()` global declaration
3. Implement command handler (e.g., `elif cmd_line.startswith(b'NEWCMD:'):`)
4. Parse data and update variables
5. Update display page to show new data

### Creating Custom Bitmap Fonts
See BITMAP_FONTS_README.md for:
- Manual binary creation
- Image-to-bitmap conversion script
- Online font generator tools
- Different font sizes (8×12, 16×24, 24×32, 32×48)

### Customizing Background Image
1. Create a 240×240 pixel image (JPG or PNG)
2. Convert using: `python convert_image.py your_image.jpg bg_name > output.py`
3. Copy the output to `image_data.py` on the display
4. Update `battery_monitor.py` to use the new image index

## Current Features

✅ **Implemented**:
1. 4-page display system (Battery, SystemInfo, Charging, About)
2. Full-screen touch navigation with page cycling
3. 10-second auto-return to Battery page
4. Charging page auto-detection and display
5. Custom bitmap fonts for large, crisp displays
6. Circular gauge for battery SOC visualization
7. Color-coded current display (green=charging, red=discharging)
8. Battery monitor with background image
9. Image display system with gamma correction
10. UART communication protocol for Pico integration
11. Real-time battery system monitoring

## Driver Library (LCD_1inch28.py)

**LCD_1inch28 class**:
- Inherits from `framebuf.FrameBuffer` (RGB565 format)
- 240×240 pixel buffer (115,200 bytes)
- SPI communication at 100 MHz
- Methods: `show()`, `Windows_show()`, `write_text()`, `set_bl_pwm()`
- Predefined colors: red, green, blue, white, black, brown (note: RGB/BRG format swap)

**Touch_CST816T class**:
- I2C communication (address 0x15)
- Point mode (mode=1) for coordinate detection
- Interrupt-driven touch detection with Flag polling
- Touch coordinates: X_point, Y_point (0-239)

**QMI8658 class** (6-DOF IMU):
- I2C address 0x6B
- Accelerometer range: ±8g at 1000Hz
- Gyroscope range: ±512dps at 1000Hz
- Returns 6-axis data: [acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z]
- Not currently used in battery display modes
