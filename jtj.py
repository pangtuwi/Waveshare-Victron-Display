# State of Charge (SOC) Display for Waveshare RP2350
# Simulated version with slowly changing random SOC values
#
# This version does NOT require ADS1115 hardware - uses simulated voltage readings

from LCD_1inch28 import LCD_1inch28
from circular_gauge import CircularGauge, rgb_to_brg565
from image_data import get_image, get_image_names, get_image_count
from image_display import display_image_with_overlays
import time
import random

print("=== SOC Display Starting (Simulated Mode) ===")

# Initialize display
lcd = LCD_1inch28()
lcd.set_bl_pwm(65535)  # Maximum brightness

# Configuration
MAX_VOLTAGE = 5.0   # Maximum input voltage (5V = 100% SOC)

# Initialize simulated voltage state
simulated_voltage = 2.5  # Start at 50% SOC

# Load background image
img_name = get_image_names()[0]
img_data = get_image(img_name)

# Create circular gauge for SOC display
soc_gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=115,
    thickness=10,
    segments=20,
    start_angle=215,
    end_angle=320,
    gap_degrees=2,
    clockwise=True,
    color=lcd.white,
    background_color=rgb_to_brg565(180, 180, 180)
)

def read_voltage():
    """Generate simulated voltage with slow random walk."""
    global simulated_voltage

    # Random walk with larger variation
    # Change range: ±0.15V per reading (~±3% SOC change)
    change = (random.random() - 0.5) * 0.3  # -0.15 to +0.15V

    # Occasionally add a larger jump (10% chance)
    if random.random() < 0.1:
        change *= 3  # Make it ±0.45V (~±9% SOC change)

    simulated_voltage += change

    # Clamp to valid voltage range (0 to MAX_VOLTAGE)
    if simulated_voltage < 0:
        simulated_voltage = 0
    elif simulated_voltage > MAX_VOLTAGE:
        simulated_voltage = MAX_VOLTAGE

    return simulated_voltage

def voltage_to_soc(voltage):
    """Convert voltage to SOC percentage (0-100%)."""
    # Linear mapping: 0V = 0%, 5V = 100%
    soc = (voltage / MAX_VOLTAGE) * 100.0

    # Clamp to 0-100%
    if soc < 0:
        soc = 0
    elif soc > 100:
        soc = 100

    return int(soc)

print("SOC Display initialized")
print(f"Simulated mode: generating random slowly changing SOC values")
print(f"Voltage range: 0-{MAX_VOLTAGE}V (0-100% SOC)")

# Initial display
voltage = read_voltage()
soc = voltage_to_soc(voltage)
print(f"Initial: {voltage:.2f}V = {soc}% SOC")

display_image_with_overlays(
    lcd, img_data,
    gauge_items=[(soc_gauge, soc)]
)

# Main loop - update SOC every second
try:
    while True:
        # Read voltage and calculate SOC
        voltage = read_voltage()
        soc = voltage_to_soc(voltage)

        print(f"Voltage: {voltage:.2f}V, SOC: {soc}%")

        # Update display with new SOC value
        display_image_with_overlays(
            lcd, img_data,
            gauge_items=[(soc_gauge, soc)]
        )

        time.sleep(1)  # Update every 1 second

except KeyboardInterrupt:
    print("\nSOC Display ended")
