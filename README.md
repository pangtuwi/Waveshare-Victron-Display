# HA-Waveshare-Display

A MicroPython project for the Waveshare RP2350-Touch-LCD-1.28 display that integrates with Home Assistant via UART communication through an ESP32-S3 ESPHome bridge.

![Waveshare RP2350-Touch-LCD-1.28](https://www.waveshare.com/img/devkit/RP2350-Touch-LCD-1.28/RP2350-Touch-LCD-1.28-1.jpg)

## Hardware

**Waveshare RP2350-Touch-LCD-1.28**
- 240×240 pixel round LCD display (GC9A01 driver)
- CST816T capacitive touch controller
- QMI8658 6-axis IMU (accelerometer + gyroscope)
- RP2350B microcontroller

**ESP32-S3 Bridge**
- Provides WiFi connectivity
- ESPHome firmware for Home Assistant integration
- UART bridge at 115200 baud

## Features

### Display Modes
- **Clock**: Large bitmap font time display with date and AM/PM indicator
- **Sensors**: Hive thermostat data with current/target temperature and heating/hot water status
- **Weather**: Weather condition, large temperature display, and humidity
- **Cycle**: Auto-rotates through Clock → Weather → Sensors every 10 seconds

### Interaction
- **Touch Control**: Touch button at bottom cycles through modes
- **Mode Indicator**: Button displays current mode name
- **Debounced Input**: 500ms debounce prevents accidental double-presses

### Display Features
- **Custom Bitmap Fonts**: Crisp 16x24 and 24x32 pixel fonts for large numbers
- **Black Backgrounds**: High contrast for better readability
- **Color-Coded Status**: Red for ON, Gray for OFF (heating/hot water)
- **Auto-Updates**: Clock refreshes every minute, data updates from Home Assistant

### Integration
- **Time Sync**: Automatic RTC sync from Home Assistant on boot and hourly
- **Weather Data**: Updates every 5 minutes or on state change
- **Hive Thermostat**: Updates every 2 minutes or on state change
- **Brightness Control**: 0-100% via Home Assistant
- **ESPHome Services**: Direct service calls from Home Assistant

## Project Structure

```
.
├── main.py                      # Main application with HA integration
├── LCD_1inch28.py               # Hardware driver library
├── bitmap_fonts.py              # 16x24 pixel bitmap font
├── bitmap_fonts_32.py           # 24x32 pixel bitmap font
├── ESP32-s3.YAML                # ESPHome configuration for ESP32
├── home_assistant_automation.yaml # HA automation examples
├── BITMAP_FONTS_README.md       # Guide for custom bitmap fonts
├── WAVESHARE_RP2350B.uf2        # MicroPython firmware
├── CLAUDE.md                     # Development documentation
└── README.md                     # This file
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
mpremote cp bitmap_fonts.py :bitmap_fonts.py
mpremote cp bitmap_fonts_32.py :bitmap_fonts_32.py
```

The code will auto-run on power-up since it's named `main.py`.

### 3. Configure ESP32-S3 with ESPHome

1. Install ESPHome on your ESP32-S3
2. Use `ESP32-s3.YAML` as your configuration
3. Update WiFi credentials in secrets
4. Flash to ESP32-S3

### 4. Connect Hardware

Connect the RP2350 to ESP32-S3 via UART:
- RP2350 TX (GPIO16) → ESP32-S3 RX (GPIO44)
- RP2350 RX (GPIO17) → ESP32-S3 TX (GPIO43)
- GND → GND

### 5. Add Home Assistant Automations

1. Copy automations from `home_assistant_automation.yaml`
2. Update entity IDs to match your setup:
   - `weather.forecast_home` - Your weather entity
   - `climate.hive_thermostat` - Your Hive thermostat
   - `water_heater.hive_hot_water` - Your Hive hot water
3. Add to your Home Assistant `automations.yaml`

## UART Command Protocol

Commands are line-delimited ASCII strings sent from ESP32 to RP2350:

### Display Commands

- `MSG:<text>` - Display text message
- `DISP:<data>` - Custom display text
- `CMD:CLEAR` - Clear display

### Configuration Commands

- `BRIGHT:<0-100>` - Set brightness percentage (0-100)
- `MODE:<mode_name>` - Set display mode (Clock/Sensors/Weather/Cycle)
- `COLOR:<r>,<g>,<b>` - Set text color (RGB values 0-255)
- `SETTIME:<YYYY>,<MM>,<DD>,<HH>,<MM>,<SS>,<WEEKDAY>,<YEARDAY>` - Set RTC time

### Data Update Commands

- `WEATHER:<condition>,<temperature>,<humidity>` - Update weather data
- `HIVE:<current_temp>,<target_temp>,<heating_status>,<hotwater_status>` - Update Hive data

### Sensor Responses (RP2350 to ESP32)

- `SENSOR:{json_data}` - Sends sensor data every 10 seconds

## Display Modes

### Clock Mode
- Black background with white text
- Day name and date (e.g., "Mon 1/12/2025")
- Large time using 16x24 bitmap font
- 12-hour format with AM/PM
- Auto-updates every minute

### Sensors Mode (Hive Thermostat)
- Black background with white text
- Current temperature (large 16x24 bitmap font)
- Target temperature (yellow, medium size)
- Heating status (ON=red, OFF=gray)
- Hot water status (ON=red, OFF=gray)

### Weather Mode
- Black background with white text
- Weather condition at top
- Very large temperature (24x32 bitmap font, no decimals)
- Humidity display (16x24 bitmap font)

### Cycle Mode
- Auto-cycles through Clock → Weather → Sensors
- Changes display every 10 seconds
- Uses same layouts as individual modes

## Architecture

```
┌──────────────────┐
│ Home Assistant   │
│ (ESPHome API)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  ESP32-S3 Bridge │
│  (WiFi → UART)   │
│    ESPHome       │
└────────┬─────────┘
         │ UART 115200
         │ GPIO43/44
         ▼
┌──────────────────┐
│   RP2350 Display │
│    MicroPython   │
│  GPIO16/17 UART  │
└──────────────────┘
```

## ESPHome Services

The ESP32 bridge provides these services to Home Assistant:

- `esphome.esphome_web_b11440_send_weather` - Send weather data
  - Parameters: `condition`, `temperature`, `humidity`

- `esphome.esphome_web_b11440_send_hive` - Send Hive thermostat data
  - Parameters: `current_temp`, `target_temp`, `heating_status`, `hotwater_status`

- `esphome.esphome_web_b11440_send_notification` - Send notification
  - Parameters: `title`, `message`, `color`

### Controls in Home Assistant
- **Display Message** (text input) - Send custom message
- **Display Brightness** (number, 0-100) - Adjust brightness
- **Display Mode** (select) - Choose Clock/Sensors/Weather/Cycle

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
uart.write(b'MSG:Hello World\n')
uart.write(b'BRIGHT:50\n')
uart.write(b'MODE:Weather\n')
uart.write(b'WEATHER:Sunny,22 C,45%\n')
uart.write(b'HIVE:20.5 C,21.0 C,ON,OFF\n')
```

## Bitmap Fonts

Custom bitmap fonts provide crisp, large displays for numbers:

- **bitmap_fonts.py**: 16x24 pixel font (digits 0-9, colon)
- **bitmap_fonts_32.py**: 24x32 pixel font (digits 0-9, colon)

### Creating Custom Fonts

See `BITMAP_FONTS_README.md` for:
- Manual binary creation
- Image-to-bitmap Python conversion script
- Online font generator tools
- Different font sizes (8x12, 16x24, 24x32, 32x48)
- Creating weather icon fonts

### Example Usage

```python
import bitmap_fonts

# Draw large time
time_str = "12:34"
time_width = bitmap_fonts.get_text_width(time_str, spacing=4)
time_x = (240 - time_width) // 2  # Center on screen
bitmap_fonts.draw_text(lcd, time_str, time_x, 100, lcd.white, spacing=4)
```

## Driver Library

The `LCD_1inch28.py` library provides:

### LCD_1inch28 Class
- Inherits from `framebuf.FrameBuffer` (RGB565 format)
- 240×240 pixel buffer (115,200 bytes)
- Methods: `show()`, `Windows_show()`, `write_text()`, `set_bl_pwm()`
- Predefined colors (note: uses BRG format internally due to framebuf)

### Touch_CST816T Class
- Point mode (mode=1) for coordinate detection
- Interrupt-driven touch detection via Flag polling
- Touch coordinates: X_point, Y_point (0-239)
- 500ms debounce implemented in main loop

### QMI8658 Class (6-DOF IMU)
- Accelerometer range: ±8g at 1000Hz
- Gyroscope range: ±512dps at 1000Hz
- Returns 6-axis data: [acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z]
- Currently not used in display modes

## Implemented Features

✅ **Complete**:
1. Time synchronization from Home Assistant (RTC)
2. Touch-based mode cycling with debouncing
3. Custom bitmap fonts for large, crisp number displays
4. Weather data display with auto-updates
5. Hive thermostat integration with status indicators
6. Auto-cycling Cycle mode (10-second intervals)
7. Mode button displays current mode name
8. Black backgrounds for optimal contrast
9. Color-coded status indicators
10. ESPHome integration with services
11. Home Assistant automation examples

## Configuration Examples

### Manual Service Calls (for testing)

**Weather Update:**
```yaml
service: esphome.esphome_web_b11440_send_weather
data:
  condition: "Sunny"
  temperature: "22 C"
  humidity: "45%"
```

**Hive Update:**
```yaml
service: esphome.esphome_web_b11440_send_hive
data:
  current_temp: "20.5 C"
  target_temp: "21.0 C"
  heating_status: "ON"
  hotwater_status: "OFF"
```

**Mode Change:**
```yaml
service: select.select_option
target:
  entity_id: select.display_mode
data:
  option: "Weather"
```

## Customization

### Adding New Display Modes

1. Add mode name to `cycle_mode()` modes list in `main.py`
2. Add display logic in `update_display_for_mode()`
3. Update ESP32-s3.YAML select options
4. Create Home Assistant automation if needed

### Adding New Data Sources

1. Add global variables in `main.py`
2. Create UART command handler in `process_command()`
3. Add ESPHome service in `ESP32-s3.YAML`
4. Create Home Assistant automation
5. Update display mode to show data

### Creating Custom Bitmap Fonts

Use the included Python script in `BITMAP_FONTS_README.md` to convert PNG images to bitmap format, or use online tools like The Dot Factory.

## Troubleshooting

**Time not syncing:**
- ESP32 waits 20 seconds on boot before sending time
- Retries after 60 seconds if first attempt fails
- Check ESP32 logs for time sync messages
- Ensure Home Assistant time platform is configured

**Touch not working:**
- Check 500ms debounce isn't preventing valid touches
- Touch area is bottom 30 pixels (y: 210-240)
- Verify touch controller initialization in logs

**Display not updating:**
- Check UART connection (GPIO16/17 on RP2350, GPIO43/44 on ESP32)
- Verify baud rate (115200)
- Check ESP32 logs for sent commands
- Monitor RP2350 serial output with `mpremote`

**Weather/Hive data showing "N/A":**
- Verify Home Assistant automations are running
- Check entity IDs match your setup
- Test with manual service calls
- Check ESP32 logs for UART output

## Future Enhancements

- [ ] Additional sensor displays (energy, security, etc.)
- [ ] Sleep mode with wake on touch
- [ ] Custom notification alerts
- [ ] Historical data graphs
- [ ] Additional bitmap font characters (letters, symbols)
- [ ] Weather icon fonts
- [ ] Multi-page displays with swipe gestures

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source. Please check individual file headers for specific license information.

## Resources

- [Waveshare RP2350-Touch-LCD-1.28 Wiki](https://www.waveshare.com/wiki/RP2350-Touch-LCD-1.28)
- [MicroPython Documentation](https://docs.micropython.org/)
- [ESPHome Documentation](https://esphome.io/)
- [Home Assistant](https://www.home-assistant.io/)

## Acknowledgments

- Hardware drivers based on Waveshare example code
- MicroPython community for excellent documentation and support
- ESPHome community for the fantastic Home Assistant integration platform
