# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Waveshare RP2350 Touch LCD Home Assistant Display

A MicroPython project for the Waveshare RP2350-Touch-LCD-1.28 display that integrates with Home Assistant via UART communication through an ESP32 bridge.

**Hardware**: Waveshare RP2350-Touch-LCD-1.28
- 240x240 pixel round LCD display
- CST816T capacitive touch controller
- QMI8658 6-axis IMU (accelerometer + gyroscope)
- RP2350B microcontroller

**Current Version**: Development

## Project Structure

- `main.py` - Main application code for Home Assistant integration
- `LCD_1inch28.py` - Hardware driver library (LCD, Touch, IMU) - renamed from RP2350-TOUCH-LCD-1.28.py
- `circular_gauge.py` - Circular gauge/progress display module with segmented arcs
- `bitmap_fonts.py` - 16x24 pixel bitmap font for digits and colon
- `bitmap_fonts_32.py` - 24x32 pixel bitmap font for larger displays
- `bitmap_fonts_48.py` - 32x48 pixel bitmap font for extra large displays
- `screentest.py` - Comprehensive test suite for display features and CircularGauge
- `ESP32-s3.YAML` - ESPHome configuration for ESP32-S3 WiFi/UART bridge
- `home_assistant_automation.yaml` - Example Home Assistant automations
- `BITMAP_FONTS_README.md` - Guide for creating custom bitmap fonts
- `WAVESHARE_RP2350B.uf2` - MicroPython firmware for RP2350B

## Key Architecture

### Hardware Communication
The project uses a three-tier communication architecture:
1. **Home Assistant** sends commands via ESPHome services
2. **ESP32-S3** acts as WiFi bridge, forwards commands over UART (115200 baud, GPIO43/44)
3. **RP2350** receives UART commands (GPIO16/17) and controls the display

### UART Command Protocol
Commands are line-delimited ASCII strings sent from ESP32 to RP2350:

**Display Commands**:
- `MSG:<text>` - Display text message
- `DISP:<data>` - Custom display text
- `CMD:CLEAR` - Clear display

**Configuration Commands**:
- `BRIGHT:<0-100>` - Set brightness percentage (0-100)
- `MODE:<mode_name>` - Set display mode (Clock/Bedroom/Weather/Cycle)
- `COLOR:<r>,<g>,<b>` - Set text color (RGB values 0-255)
- `SETTIME:<YYYY>,<MM>,<DD>,<HH>,<MM>,<SS>,<WEEKDAY>,<YEARDAY>` - Set RTC time

**Data Update Commands**:
- `WEATHER:<condition>,<temperature>,<humidity>` - Update weather data
- `HIVE:<current_temp>,<target_temp>,<heating_status>,<hotwater_status>` - Update Hive thermostat data
- `BEDROOM:<temperature>,<humidity>` - Update bedroom temperature sensor data

**Sensor Responses** (RP2350 to ESP32):
- `SENSOR:{json_data}` - Sends sensor data every 10 seconds

### Display Modes

- **Clock**:
  - Black background with white text
  - Shows date with day name (e.g., "Mon 1/12/2025")
  - Large time display using 16x24 bitmap font
  - 12-hour format with AM/PM indicator
  - Auto-updates every minute

- **Bedroom**:
  - Dark grey background (RGB 64,64,64) with white text
  - Title: "BEDROOM"
  - Large temperature display using 24x32 bitmap font
  - Humidity display using 16x24 bitmap font
  - Data from Home Assistant bedroom temperature sensor

- **Weather**:
  - Black background with white text
  - Weather condition at top
  - Very large temperature using 32x48 bitmap font
  - Humidity display using 16x24 bitmap font
  - No decimal places on temperature

- **Cycle**:
  - Automatically cycles through Clock → Weather → Bedroom every 10 seconds
  - Uses same layouts as individual modes

### Mode Selection
- Touch button at bottom of screen (y: 210-240)
- Button displays current mode name
- Touch to cycle: Clock → Bedroom → Weather → Cycle → Clock
- 500ms debounce to prevent double-presses

### Bitmap Fonts
Custom bitmap fonts for crisp, large number displays:
- **bitmap_fonts.py**: 16x24 pixel font (digits 0-9, colon)
- **bitmap_fonts_32.py**: 24x32 pixel font (digits 0-9, colon)
- **bitmap_fonts_48.py**: 32x48 pixel font (digits 0-9, colon)
- Functions: `draw_char()`, `draw_text()`, `get_text_width()` (and _32, _48 variants)
- See BITMAP_FONTS_README.md for creating custom fonts

### Circular Gauge Module (circular_gauge.py)

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
- Counter-clockwise increases angle (default)
- Clockwise decreases angle (set `clockwise=True`)

**Example - Top arc gauge**:
```python
from circular_gauge import CircularGauge

gauge = CircularGauge(
    lcd=lcd,
    center_x=120, center_y=120,
    radius=110, thickness=12,
    segments=16,
    start_angle=135,  # Top-left
    end_angle=405,    # Top-right (270° arc)
    gap_degrees=2,
    color=0xFFFF,     # White
    background_color=0x2104  # Dark grey for unfilled
)
gauge.update(75)  # Set to 75% and draw
lcd.show()
```

**Example - Bottom arc (speedometer style)**:
```python
gauge = CircularGauge(
    lcd=lcd,
    center_x=120, center_y=150,
    radius=100, thickness=15,
    segments=12,
    start_angle=225,  # Bottom-left
    end_angle=495,    # Bottom-right (270° arc)
    gap_degrees=2,
    color=rgb_to_brg565(0, 255, 0)  # Green
)
```

**Example - Clockwise gauge**:
```python
gauge = CircularGauge(
    lcd=lcd,
    center_x=120, center_y=120,
    radius=110, thickness=12,
    segments=8,
    start_angle=45,   # Top-right
    end_angle=315,    # Bottom-right (90° clockwise)
    gap_degrees=2,
    color=0xFFFF,
    clockwise=True    # Draw clockwise instead of counter-clockwise
)
```

**Methods**:
- `set_value(percentage)` - Set gauge value (0-100)
- `draw()` - Draw gauge to LCD buffer
- `update(percentage)` - Set value and draw in one call
- `draw_with_partial_refresh()` - Draw and use Windows_show() for efficiency
- `draw_incremental(old_value)` - Only redraw changed segments

**Helper function**:
- `rgb_to_brg565(r, g, b)` - Convert RGB888 to BRG565 format for correct color display

**Performance**:
- Single segment (~10px thick, 20° arc): ~5-10ms
- Full 12-segment gauge: ~60-120ms
- Suitable for real-time sensor data updates (1-2 second intervals)

**Use Cases**:
- Temperature gauges
- Humidity indicators
- Battery level displays
- Progress indicators
- Speed/RPM displays
- Any percentage-based visualization

### Driver Library (LCD_1inch28.py)

**LCD_1inch28 class**:
- Inherits from `framebuf.FrameBuffer` (RGB565 format)
- 240x240 pixel buffer (115,200 bytes)
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

## ESP32 Integration

### ESPHome Services
The ESP32-s3.YAML defines the following services:

- `esphome.esphome_web_b11440_send_weather` - Send weather data
  - Parameters: condition, temperature, humidity

- `esphome.esphome_web_b11440_send_hive` - Send Hive thermostat data
  - Parameters: current_temp, target_temp, heating_status, hotwater_status

- `esphome.esphome_web_b11440_send_bedroom` - Send bedroom temperature data
  - Parameters: temperature, humidity

- `esphome.esphome_web_b11440_send_notification` - Send notification
  - Parameters: title, message, color

### Time Synchronization
- Home Assistant time platform syncs to ESP32
- On boot: 20 second delay, then sends time to RP2350
- Retry after 60 seconds if first attempt fails
- Hourly sync on the hour (00 minutes)

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
mpremote cp bitmap_fonts.py :bitmap_fonts.py
mpremote cp bitmap_fonts_32.py :bitmap_fonts_32.py
mpremote cp bitmap_fonts_48.py :bitmap_fonts_48.py
```

For testing the CircularGauge module:
```bash
mpremote cp screentest.py :screentest.py
mpremote run screentest.py
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
- Manual RGB565 conversion: `((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)`

### UART Communication
- Baudrate: 115200
- RP2350: TX=GPIO16, RX=GPIO17
- ESP32-S3: TX=GPIO43, RX=GPIO44
- Commands must be newline-terminated
- Always decode bytes: `cmd_line.decode().strip()`
- Wrap command processing in try/except to prevent crashes

### Touch Handling
- Touch coordinates: (0-239, 0-239) for 240×240 display
- Mode: point mode (mode=1)
- Poll `touch.Flag` for new touch events (interrupt-driven)
- Access coordinates via `touch.X_point`, `touch.Y_point`
- 500ms debounce using `time.ticks_ms()` and `time.ticks_diff()`

### Display Text Rendering
- `lcd.text(str, x, y, color)` - Standard 8×8 font
- `lcd.write_text(str, x, y, size, color)` - Scalable font (size multiplier)
- `bitmap_fonts.draw_text(lcd, text, x, y, color, spacing)` - 16x24 bitmap font
- `bitmap_fonts_32.draw_text_32(lcd, text, x, y, color, spacing)` - 24x32 bitmap font
- `bitmap_fonts_48.draw_text_48(lcd, text, x, y, color, spacing)` - 32x48 bitmap font
- Bitmap fonts provide crisp, professional-looking large numbers

### RTC (Real-Time Clock)
- RTC synced from Home Assistant via ESP32 on boot
- Format: `(year, month, day, weekday, hour, minute, second, subsecond)`
- Access time: `time.localtime()` after RTC is set
- Clock mode auto-refreshes every 60 seconds

## Home Assistant Integration

### Required Entity IDs (Update in automations)
- Weather: `weather.forecast_home`
- Hive Thermostat: `climate.hive_thermostat`
- Hive Hot Water: `water_heater.hive_hot_water`
- Bedroom Temperature: `sensor.temp_sensor_1_bedroom_temperature`
- Bedroom Humidity: `sensor.temp_sensor_1_bedroom_humidity`

### Automation Triggers
- Weather: Every 5 minutes OR on state change
- Hive: Every 2 minutes OR on state change
- Bedroom: Every 2 minutes OR on state change
- Time: On boot (20s delay) + hourly

## Current Features

✅ **Implemented**:
1. Time synchronization from Home Assistant
2. Touch-based mode cycling
3. Custom bitmap fonts for large, crisp displays
4. Weather data display
5. Hive thermostat integration (legacy support)
6. Bedroom temperature sensor display with dark grey background
7. Auto-cycling Cycle mode
8. Mode button displays current mode name
9. Multiple background colors (black for Clock/Weather, dark grey for Bedroom)
10. Large temperature displays with humidity

## Extending the Project

### Adding New Display Modes
1. Add mode name to `cycle_mode()` modes list
2. Add `elif mode == "NewMode":` section in `update_display_for_mode()`
3. Implement display layout using `lcd.text()`, `lcd.write_text()`, or bitmap fonts
4. Update ESP32-s3.YAML select options
5. Create Home Assistant automation/service if needed

### Adding New Data Sources
1. Add global variables for data storage
2. Add to `process_command()` global declaration
3. Implement command handler (e.g., `elif cmd_line.startswith(b'NEWCMD:'):`)
4. Parse data and update variables
5. Add ESPHome service in ESP32-s3.YAML
6. Create Home Assistant automation
7. Update display mode to show new data

### Creating Custom Bitmap Fonts
See BITMAP_FONTS_README.md for:
- Manual binary creation
- Image-to-bitmap conversion script
- Online font generator tools
- Different font sizes (8x12, 16x24, 24x32, 32x48)
- Weather icon fonts

### Improving Performance
- Use partial display updates (`Windows_show`) instead of full refreshes
- Reduce polling frequency in main loop
- Implement display sleep mode after inactivity
- Use bitmap fonts for frequently updated large numbers
