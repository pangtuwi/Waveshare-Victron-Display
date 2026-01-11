# Victron Battery Display - Quick Reference Card

## Pages

| Page | Shows | Access |
|------|-------|--------|
| **Battery** | Circular gauge (SOC) | Default, auto-return after 10s |
| **System Info** | SOC, Voltage, Current, Temp | Touch screen to cycle |
| **Charging** | Charging metrics + bolt icon | Auto-appears when charging |
| **About** | App name, Paul Williams | Touch screen to cycle |

## Navigation

- **Touch anywhere** → Next page
- **10 seconds idle** → Return to Battery page
- **Charging detected** → Auto-show Charging page

## UART Commands (from Pico)

```python
# Battery State of Charge (0-100%)
uart.write(b"BATTERY:75\n")

# System data: voltage(V), current(A), temp(°C)
uart.write(b"BATSYS:48.5,12.3,25.5\n")

# Charging state (0=no, 1=yes)
uart.write(b"CHARGING:1\n")

# Brightness (0-100%)
uart.write(b"BRIGHT:75\n")
```

## Hardware Connection

```
Pico GPIO0 (TX) → Display GPIO17 (RX)
Pico GPIO1 (RX) → Display GPIO16 (TX)
GND → GND
```

**Baud**: 115200

## Upload Files

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

## Pico Example Code

```python
from machine import UART, Pin
import time

# Initialize UART to display
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Update function
def update_display(soc, voltage, current, temp, charging):
    uart.write(f"BATTERY:{int(soc)}\n".encode())
    uart.write(f"BATSYS:{voltage:.2f},{current:.2f},{temp:.1f}\n".encode())
    uart.write(f"CHARGING:{1 if charging else 0}\n".encode())

# Main loop
while True:
    # Read from Victron system
    soc = 75  # State of charge %
    voltage = 48.5  # Volts
    current = 12.3  # Amps (+ = charging, - = discharging)
    temp = 25.5  # °C
    charging = (current > 0)

    # Send to display
    update_display(soc, voltage, current, temp, charging)
    time.sleep(1)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Display not updating | Check UART wiring (TX→RX crossover), verify 115200 baud |
| Touch not working | Touch anywhere, wait 500ms between touches |
| Wrong data | Check command format, ensure newline termination |
| Charging page not appearing | Send `CHARGING:1\n`, check Pico charging detection |

## Testing Commands (REPL)

```python
# Connect to display
mpremote

# Test commands
>>> uart.write(b'BATTERY:75\n')
>>> uart.write(b'BATSYS:48.5,12.3,25.5\n')
>>> uart.write(b'CHARGING:1\n')
```

## Files Documentation

- **PICO_INTEGRATION.md** - Complete integration guide
- **PROJECT_SUMMARY.md** - Full project overview
- **README.md** - Original project documentation
- **QUICK_REFERENCE.md** - This file
