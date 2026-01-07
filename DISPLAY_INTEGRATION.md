# Display Integration Instructions

This file contains instructions for integrating the battery monitor into your HA-Waveshare-Display repository.

## Files to Copy

1. Copy `battery_monitor.py` from this directory to your HA-Waveshare-Display repository root

## Modifications to Display main.py

The following changes need to be made to the `main.py` file in your HA-Waveshare-Display repository:

### 1. Add Import (at the top with other imports)

```python
from battery_monitor import BatteryMonitor
```

### 2. Initialize Battery Monitor (after LCD initialization)

Find where the LCD is initialized (likely something like `lcd = LCD_1inch28()`) and add after it:

```python
# Initialize battery monitor
print("Initializing battery monitor...")
battery_monitor = BatteryMonitor(lcd, image_index=0)
battery_monitor.render()  # Show initial state (0%)
print("Battery monitor ready")
```

### 3. Add UART Command Handler

Find the `process_command()` function or wherever UART commands are parsed. Add this handler alongside existing command handlers (like `MSG:`, `BRIGHT:`, etc.):

```python
elif line.startswith('BATTERY:'):
    soc_str = line[8:].strip()
    try:
        soc = int(soc_str)
        if battery_monitor.update_soc(soc):
            print(f"Battery SOC: {soc}%")
        else:
            print(f"Battery SOC update failed: {soc}")
    except ValueError:
        print(f"Invalid battery SOC format: {soc_str}")
```

### 4. Optional: Add Staleness Monitoring

In the main loop, you can optionally add periodic staleness checks:

```python
# Periodically check for stale data (every 30 seconds or so)
if battery_monitor.is_stale():
    status = battery_monitor.get_status()
    print(f"WARNING: Battery data stale (age: {status['age_ms']}ms)")
```

## Example Integration

Here's a complete example of what the relevant sections might look like:

```python
from machine import UART, Pin
import time
from LCD_1inch28 import LCD_1inch28
from battery_monitor import BatteryMonitor

# Initialize hardware
lcd = LCD_1inch28()
lcd.set_bl_pwm(65535)  # Full brightness

# Initialize battery monitor
print("Initializing battery monitor...")
battery_monitor = BatteryMonitor(lcd, image_index=0)
battery_monitor.render()  # Show initial state
print("Battery monitor ready")

# Initialize UART
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
uart.init(timeout=100)

def process_command(line):
    """Process incoming UART command"""
    try:
        if line.startswith('MSG:'):
            message = line[4:]
            # Handle message display
        elif line.startswith('BRIGHT:'):
            brightness = int(line[7:])
            lcd.set_bl_pwm(brightness)
        elif line.startswith('BATTERY:'):
            soc_str = line[8:].strip()
            try:
                soc = int(soc_str)
                if battery_monitor.update_soc(soc):
                    print(f"Battery SOC: {soc}%")
                else:
                    print(f"Battery SOC update failed: {soc}")
            except ValueError:
                print(f"Invalid battery SOC format: {soc_str}")
        else:
            print(f"Unknown command: {line}")
    except Exception as e:
        print(f"Error processing command: {e}")

# Main loop
while True:
    if uart.any():
        data = uart.readline()
        if data:
            line = data.decode('utf-8').strip()
            process_command(line)

    time.sleep(0.1)
```

## Testing the Display

Once integrated, you can test the display by manually sending UART commands:

```python
# From another device or the REPL
from machine import UART, Pin
import time

uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# Test sequence
for soc in [0, 25, 50, 75, 100]:
    uart.write(f"BATTERY:{soc}\n".encode('utf-8'))
    time.sleep(2)
```

## Troubleshooting

**Gauge not displaying:**
- Check that the image file loaded successfully (look for "Loaded image" message)
- Verify CircularGauge module is available
- Check for exceptions in the console

**No response to UART commands:**
- Verify UART is initialized on correct pins (GP16/GP17 for UART0)
- Check baud rate matches (115200)
- Ensure command format is correct: `BATTERY:XX\n`
- Use REPL to check `uart.any()` returns True when data sent

**Gauge shows wrong value:**
- Check SOC parsing in command handler
- Verify `update_soc()` returns True
- Print debug info: `print(f"Received SOC: {soc}, Current: {battery_monitor.current_soc}")`
