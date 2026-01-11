# Raspberry Pi Pico Integration Guide

This guide explains how to integrate your Raspberry Pi Pico with the Waveshare RP2350 Display for the Victron Battery Display System.

## Hardware Connection

### UART Wiring
Connect the Raspberry Pi Pico to the Waveshare RP2350 display via UART:

```
Pico                    RP2350 Display
────────────────────    ──────────────────
GPIO0 (UART0 TX)   →    GPIO17 (UART0 RX)
GPIO1 (UART0 RX)   ←    GPIO16 (UART0 TX)
GND                ─    GND
```

### Specifications
- **Baud Rate**: 115200
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Protocol**: Line-delimited ASCII commands (newline terminated)

## UART Command Protocol

The RP2350 display accepts the following commands from your Pico:

### Battery State of Charge
```
BATTERY:<soc>\n
```
- **soc**: State of Charge (0-100)
- **Example**: `BATTERY:75\n`
- **Updates**: Battery page circular gauge

### Battery System Data
```
BATSYS:<voltage>,<current>,<temp>\n
```
- **voltage**: Battery voltage in volts (e.g., 48.5)
- **current**: Current in amps (positive=charging, negative=discharging)
- **temp**: Battery temperature in °C
- **Example**: `BATSYS:48.5,12.3,25.5\n`
- **Updates**: System Information page

### Charging State
```
CHARGING:<state>\n
```
- **state**: 0=not charging, 1=charging
- **Example**: `CHARGING:1\n`
- **Auto-displays**: Charging page when state changes to 1

### Brightness Control
```
BRIGHT:<level>\n
```
- **level**: Brightness 0-100
- **Example**: `BRIGHT:75\n`

### Display Mode (Manual Override)
```
MODE:<page>\n
```
- **page**: Battery, SystemInfo, Charging, About
- **Example**: `MODE:SystemInfo\n`
- **Note**: Touch navigation is preferred; use only for testing

## Display Pages

### 1. Battery Monitor (Default)
- Circular gauge showing SOC (0-100%)
- Background image
- Auto-returns to this page after 10 seconds of inactivity

### 2. System Information
- State of Charge (%) - Large display
- Voltage (V)
- Current (A) - Green when charging, Red when discharging
- Temperature (°C)

### 3. Charging (Auto-appears)
- Green charging bolt icon
- Charging current (+A)
- Battery voltage
- Current SOC
- Automatically displayed when `CHARGING:1` received
- Returns to Battery page when charging stops or after 10s timeout

### 4. About
- Application name: "Victron Battery Display System"
- Version: v1.0
- Developer: Paul Williams

## Page Navigation

### Touch Navigation
- **Touch anywhere on screen**: Cycles through pages
  - Battery → System Info → About → Battery → ...
- **Charging page**: Only appears when charging is active
- **Auto-return**: All pages auto-return to Battery page after 10 seconds

### Navigation Flow
```
[Battery] ──touch──> [System Info] ──touch──> [About] ──touch──> [Battery]
    ↑
    └─────────────── 10 second timeout ──────────────────────────────┘

[Charging] appears automatically when CHARGING:1 received
[Charging] ──touch or timeout──> [Battery]
```

## Example Pico Code (MicroPython)

### Basic UART Setup
```python
from machine import UART, Pin
import time

# Initialize UART0
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

def send_command(command):
    """Send command to display"""
    uart.write(command.encode('utf-8'))
    print(f"Sent: {command.strip()}")

# Send SOC
send_command("BATTERY:75\n")

# Send system data
send_command("BATSYS:48.5,12.3,25.5\n")

# Set charging state
send_command("CHARGING:1\n")
```

### Complete Integration Example
```python
from machine import UART, Pin
import time

# Initialize UART
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

def send_battery_data(soc, voltage, current, temp, charging):
    """Send complete battery data to display"""
    # Send SOC
    uart.write(f"BATTERY:{int(soc)}\n".encode())

    # Send system information
    uart.write(f"BATSYS:{voltage:.2f},{current:.2f},{temp:.1f}\n".encode())

    # Send charging state
    charging_state = 1 if charging else 0
    uart.write(f"CHARGING:{charging_state}\n".encode())

    print(f"Sent: SOC={soc}%, V={voltage}V, I={current}A, T={temp}°C, Charging={charging}")

# Main loop - update every 1 second
while True:
    # Get data from your Victron system (example values)
    soc = 75  # Read from Victron
    voltage = 48.5  # Read from Victron
    current = 12.3  # Positive when charging, negative when discharging
    temp = 25.5  # Battery temperature
    charging = (current > 0)  # Charging if current is positive

    # Send to display
    send_battery_data(soc, voltage, current, temp, charging)

    time.sleep(1)  # Update every second
```

### Integration with Victron VE.Direct

Based on the [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect) project:

```python
from machine import UART, Pin
import time

# UART for Victron VE.Direct (adjust pins as needed)
victron_uart = UART(1, baudrate=19200, tx=Pin(4), rx=Pin(5))

# UART for Display
display_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Victron data storage
victron_data = {
    'V': 0,      # Voltage (mV)
    'I': 0,      # Current (mA)
    'SOC': 0,    # State of charge (0.1%)
    'T': 0,      # Temperature (°C)
    'CS': 0,     # Charger state
}

def parse_vedirect_line(line):
    """Parse VE.Direct protocol line"""
    if '\t' in line:
        key, value = line.split('\t', 1)
        if key in victron_data:
            try:
                victron_data[key] = int(value)
            except ValueError:
                pass

def send_to_display():
    """Send Victron data to display"""
    # Convert Victron units to display units
    voltage = victron_data['V'] / 1000.0  # mV to V
    current = victron_data['I'] / 1000.0  # mA to A
    soc = victron_data['SOC'] / 10.0      # 0.1% to %
    temp = victron_data['T']               # Already in °C

    # Charger state: 0=Off, 2=Fault, 3=Bulk, 4=Absorption, 5=Float
    charging = victron_data['CS'] in [3, 4, 5]

    # Send to display
    display_uart.write(f"BATTERY:{int(soc)}\n".encode())
    display_uart.write(f"BATSYS:{voltage:.2f},{current:.2f},{temp:.1f}\n".encode())
    display_uart.write(f"CHARGING:{1 if charging else 0}\n".encode())

# Main loop
line_buffer = ""
last_update = time.ticks_ms()

while True:
    # Read from Victron
    if victron_uart.any():
        data = victron_uart.read()
        if data:
            line_buffer += data.decode('utf-8', 'ignore')

            while '\n' in line_buffer:
                line, line_buffer = line_buffer.split('\n', 1)
                parse_vedirect_line(line.strip())

    # Update display every 1 second
    if time.ticks_diff(time.ticks_ms(), last_update) > 1000:
        send_to_display()
        last_update = time.ticks_ms()

    time.sleep_ms(10)
```

## Testing Commands

You can test the display manually via the RP2350's REPL console:

### Connect to REPL
```bash
mpremote
```

### Manual Test Commands
```python
# Test SOC update
uart.write(b'BATTERY:75\n')

# Test system data
uart.write(b'BATSYS:48.5,12.3,25.5\n')

# Test charging state
uart.write(b'CHARGING:1\n')

# Test brightness
uart.write(b'BRIGHT:50\n')

# Manual page change
uart.write(b'MODE:SystemInfo\n')
```

## Upload Files to Display

Upload the updated code to your RP2350 display:

```bash
cd /path/to/Waveshare-Victron-Display

# Upload all required files
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

The code will auto-run on boot since it's named `main.py`.

## Troubleshooting

### Display not updating
1. Check UART connections (TX→RX, RX→TX, GND→GND)
2. Verify baud rate is 115200 on both devices
3. Ensure commands are newline-terminated (`\n`)
4. Check Pico is sending data: add `print()` statements
5. Monitor display console: `mpremote` to see received commands

### Wrong data displayed
1. Verify command format matches protocol exactly
2. Check data types (SOC must be integer, voltage/current must be float)
3. Ensure commas separate values in `BATSYS` command
4. Test with known values manually via REPL

### Touch not working
1. Touch anywhere on screen, not just edges
2. Wait 500ms between touches (debounce delay)
3. Check touch controller initialization in console output

### Charging page not appearing
1. Verify `CHARGING:1` command is being sent
2. Check charging detection logic on Pico side
3. Monitor console for "Charging started" message

### Display shows stale data warning
1. Pico must send updates at least every 15 seconds
2. Check UART connection is stable
3. Verify Pico code main loop is running

## Data Update Recommendations

### Update Frequencies
- **SOC**: Every 1-5 seconds
- **System Data**: Every 1-5 seconds
- **Charging State**: On change, or every 10 seconds
- **Brightness**: On change only

### Bandwidth Considerations
At 1-second update intervals:
- SOC: ~15 bytes/sec
- System data: ~30 bytes/sec
- Charging: ~15 bytes/sec
- **Total**: ~60 bytes/sec (well within 115200 baud capacity)

## Advanced Features

### Custom Background Image
To change the background image on the Battery page:

1. Create a 240×240 pixel image (JPG or PNG)
2. Convert using the provided script:
   ```bash
   python convert_image.py your_image.jpg battery_bg > output.py
   ```
3. Copy the output to `image_data.py` on the display
4. Update `battery_monitor.py` to use the new image index

### Adjusting Auto-Return Timeout
Edit `main.py` and change:
```python
AUTO_RETURN_TIMEOUT_MS = 10000  # Change to desired milliseconds
```

### Adding More Pages
You can add additional pages by:
1. Adding new mode name to `cycle_mode()` function
2. Adding page layout in `update_display_for_mode()`
3. Creating UART command handler if needed

## Reference

### Display Specifications
- **Screen**: 240×240 pixels, round LCD
- **Touch**: CST816T capacitive touch (point mode)
- **Microcontroller**: RP2350B
- **Flash**: 4MB
- **RAM**: 264KB
- **Firmware**: MicroPython

### Color Format
The display uses non-standard BRG565 format:
- Use predefined colors: `lcd.white`, `lcd.black`, `lcd.red`, `lcd.green`, `lcd.blue`
- For custom colors, use: `rgb_to_brg565(r, g, b)` function

### Useful Resources
- [Victron VE.Direct Protocol](https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.33.pdf)
- [Raspberry-Pi-Victron-Connect](https://github.com/pangtuwi/Raspberry-Pi-Victron-Connect)
- [Waveshare RP2350 Display Wiki](https://www.waveshare.com/wiki/RP2350-Touch-LCD-1.28)
- [MicroPython UART Documentation](https://docs.micropython.org/en/latest/library/machine.UART.html)
