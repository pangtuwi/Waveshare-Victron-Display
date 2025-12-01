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
- `RP2350-TOUCH-LCD-1.28.py` - Hardware driver library (LCD, Touch, IMU)
- `WAVESHARE_RP2350B.uf2` - MicroPython firmware for RP2350B

## Key Architecture

### Hardware Communication
The project uses a three-tier communication architecture:
1. **Home Assistant** sends commands via MQTT/API
2. **ESP32** acts as WiFi bridge, forwards commands over UART (115200 baud)
3. **RP2350** receives UART commands and controls the display

### UART Command Protocol
Commands are line-delimited ASCII strings sent from ESP32 to RP2350:

**Display Commands**:
- `MSG:<text>` - Display text message
- `DISP:<data>` - Custom display text
- `CMD:CLEAR` - Clear display
- `CMD:TIME` - Show time (placeholder implementation)

**Configuration Commands**:
- `BRIGHT:<0-100>` - Set brightness percentage
- `MODE:<mode_name>` - Set display mode (Clock/Sensors/Weather/Custom)
- `COLOR:<r>,<g>,<b>` - Set text color (RGB values)

**Sensor Responses** (RP2350 to ESP32):
- `SENSOR:{json_data}` - Sends sensor data every 10 seconds

### Display Modes
- **Clock**: Shows time (requires RTC or network sync)
- **Sensors**: Displays temperature and humidity from IMU or external sensors
- **Weather**: Shows weather info (data source not yet implemented)
- **Custom**: User-defined display content

### Driver Library (RP2350-TOUCH-LCD-1.28.py)

**LCD_1inch28 class**:
- Inherits from `framebuf.FrameBuffer` (RGB565 format)
- 240x240 pixel buffer (115,200 bytes)
- SPI communication at 100 MHz
- Methods: `show()`, `Windows_show()`, `write_text()`, `set_bl_pwm()`
- Predefined colors: red, green, blue, white, black, brown (note: RGB/BRG format swap)

**Touch_CST816T class**:
- I2C communication (address 0x15)
- Three modes: gestures (0), point (1), mixed (2)
- Gesture types: UP, DOWN, LEFT, RIGHT, Long Press, Double Click
- Interrupt-driven touch detection

**QMI8658 class** (6-DOF IMU):
- I2C address 0x6B
- Accelerometer range: ±8g at 1000Hz
- Gyroscope range: ±512dps at 1000Hz
- Returns 6-axis data: [acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z]

## Development Commands

### Uploading Firmware
1. Hold BOOTSEL button on RP2350
2. Connect USB cable
3. Copy `WAVESHARE_RP2350B.uf2` to mounted drive
4. Device will reboot with MicroPython installed

### Uploading Code to Device
Use `mpremote` or `ampy` to copy Python files:
```bash
mpremote cp main.py :
mpremote cp RP2350-TOUCH-LCD-1.28.py :LCD_1inch28.py
```

### Running the Application
Code auto-runs on boot if saved as `main.py`. To test manually:
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
- Use `lcd.color(r, g, b)` method for correct RGB conversion

### UART Communication
- Baudrate: 115200
- TX: Pin 0, RX: Pin 1
- Commands must be newline-terminated
- Always decode bytes: `cmd_line.decode().strip()`
- Wrap command processing in try/except to prevent crashes

### Touch Handling
- Touch coordinates: (0-239, 0-239) for 240×240 display
- Set mode before use: `Touch.Set_Mode(mode)`
- Poll `Touch.Flag` for new touch events (interrupt-driven)
- Access coordinates via `Touch.X_point`, `Touch.Y_point`

### Display Text Rendering
- `lcd.text(str, x, y, color)` - Standard 8×8 font
- `lcd.write_text(str, x, y, size, color)` - Scalable font (size multiplier)
- Text rendering is slow for large fonts; minimize redraws

## Current Limitations

1. **Time Display**: No RTC or network time sync implemented
2. **Sensor Data**: IMU data available but not integrated into display modes
3. **ESP32 Bridge**: Communication protocol defined but ESP32 code not included
4. **Home Assistant Integration**: UART protocol defined but HA configuration not included
5. **Error Handling**: Limited error feedback to Home Assistant
6. **Display Updates**: No automatic refresh; requires command from HA

## Extending the Project

### Adding New Display Modes
1. Add mode name to `update_display_for_mode()` function
2. Implement display layout using `lcd.text()` or `lcd.write_text()`
3. Update Home Assistant to send `MODE:<new_mode>` command

### Adding Sensor Integration
1. Read IMU data using `qmi8658.Read_XYZ()` in main loop
2. Package data in `send_sensor_data()` function
3. Configure Home Assistant to parse `SENSOR:` response

### Improving Performance
- Use partial display updates (`Windows_show`) instead of full refreshes
- Reduce UART polling frequency if commands are infrequent
- Implement display sleep mode after inactivity
