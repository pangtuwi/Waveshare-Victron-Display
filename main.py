from machine import UART, Pin, RTC
from LCD_1inch28 import LCD_1inch28, Touch_CST816T
import time
import json
import bitmap_fonts
import bitmap_fonts_32
import bitmap_fonts_48
from battery_monitor import BatteryMonitor

# Initialize UART for communication with Raspberry Pi Pico
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# Initialize RTC
rtc = RTC()

# Initialize display
lcd = LCD_1inch28()
lcd.set_bl_pwm(65535)  # Set brightness to maximum

# Initialize touch controller
touch = Touch_CST816T(mode=1, LCD=lcd)  # Mode 1 = point mode

# Initialize battery monitor
print("Initializing battery monitor...")
battery_monitor = BatteryMonitor(lcd, image_index=0)
battery_monitor.render()  # Show initial state (0%)
print("Battery monitor ready")

# Display welcome message
lcd.fill(lcd.white)
lcd.text("Victron Battery", 60, 100, lcd.black)
lcd.text("Display", 85, 120, lcd.black)
lcd.text("Ready!", 90, 140, lcd.black)
lcd.show()
print("Welcome message displayed")

# Wait for 2 seconds to show welcome message
time.sleep(2)

# Display settings
current_brightness = 100
current_mode = "Battery"  # Start with Battery page
display_color = lcd.black

# Battery system data
battery_soc = 0  # State of Charge (0-100%)
battery_voltage = 0.0  # Voltage in V
battery_current = 0.0  # Current in A (positive=charging, negative=discharging)
battery_temp = 0.0  # Temperature in °C
is_charging = False  # Charging state

# System status data
wifi_status = -1  # WiFi connection status: -1=Unknown, 0=Disconnected, 1=Connected, 2=Skipped (demo mode)
demo_mode = 0  # Demo mode status: 0=Inactive, 1=Active

# Page navigation settings
AUTO_RETURN_TIMEOUT_MS = 10000  # 10 seconds to auto-return to Battery page
last_page_change_time = time.ticks_ms()
MODE_CHANGE_COOLDOWN_MS = 1000  # Prevent rapid mode switching (1 second cooldown)
last_mode_change_time = 0

def process_command(cmd_line):
    """Process incoming commands from Raspberry Pi Pico via UART"""
    global current_brightness, current_mode, display_color
    global battery_soc, battery_voltage, battery_current, battery_temp, is_charging
    global wifi_status, demo_mode
    global battery_monitor, last_page_change_time, last_mode_change_time

    try:
        print(f"Received command: {cmd_line}")

        if cmd_line.startswith(b'BRIGHT:'):
            # Adjust brightness
            brightness = int(cmd_line[7:].decode().strip())
            current_brightness = brightness
            lcd.set_bl_pwm(int(brightness * 65535 / 100))
            print(f"Brightness set to: {brightness}%")

        elif cmd_line.startswith(b'MODE:'):
            # Change display mode (for compatibility)
            mode = cmd_line[5:].decode().strip()

            # Check cooldown to prevent rapid mode switching
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_mode_change_time) < MODE_CHANGE_COOLDOWN_MS:
                print(f"Mode change ignored (cooldown active): {mode}")
                return

            if mode != current_mode:
                print(f"Mode changed via UART: {current_mode} → {mode}")
                current_mode = mode
                update_display_for_mode(mode)
                last_page_change_time = time.ticks_ms()
                last_mode_change_time = time.ticks_ms()
            else:
                print(f"Mode unchanged: {mode}")

        elif cmd_line.startswith(b'CMD:CLEAR'):
            # Clear display
            lcd.fill(lcd.white)
            lcd.show()
            print("Display cleared")

        elif cmd_line.startswith(b'SETTIME:'):
            # Set RTC time from Pico
            # Format: SETTIME:YYYY,MM,DD,HH,MM,SS,WEEKDAY,YEARDAY
            time_str = cmd_line[8:].decode().strip()
            time_parts = time_str.split(',')
            if len(time_parts) == 8:
                year = int(time_parts[0])
                month = int(time_parts[1])
                day = int(time_parts[2])
                hour = int(time_parts[3])
                minute = int(time_parts[4])
                second = int(time_parts[5])
                weekday = int(time_parts[6])
                yearday = int(time_parts[7])
                rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
                print(f"Time set to: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")

        elif cmd_line.startswith(b'BATTERY:'):
            # Update battery SOC
            # Format: BATTERY:soc
            soc_str = cmd_line[8:].decode().strip()
            try:
                soc = int(soc_str)
                battery_soc = soc
                print(f"Battery SOC: {soc}%")

                # Only update battery monitor (which renders) if on Battery page
                if current_mode == "Battery":
                    if battery_monitor.update_soc(soc):
                        # Battery monitor rendered successfully
                        pass
                    else:
                        print(f"Battery SOC update failed: {soc}")
            except ValueError:
                print(f"Invalid battery SOC format: {soc_str}")

        elif cmd_line.startswith(b'BATSYS:'):
            # Update battery system data
            # Format: BATSYS:voltage,current,temp
            data_str = cmd_line[7:].decode().strip()
            data_parts = data_str.split(',')
            if len(data_parts) == 3:
                try:
                    battery_voltage = float(data_parts[0])
                    battery_current = float(data_parts[1])
                    battery_temp = float(data_parts[2])
                    print(f"Battery system: {battery_voltage}V, {battery_current}A, {battery_temp}°C")
                    # Refresh display if on SystemInfo or Charging page (both show this data)
                    if current_mode == "SystemInfo" or current_mode == "Charging":
                        update_display_for_mode(current_mode)
                except ValueError:
                    print(f"Invalid battery system data format: {data_str}")

        elif cmd_line.startswith(b'CHARGING:'):
            # Update charging state
            # Format: CHARGING:state (0=not charging, 1=charging)
            state_str = cmd_line[9:].decode().strip()
            try:
                charging_state = int(state_str)
                was_charging = is_charging
                is_charging = (charging_state == 1)

                # Auto-switch to Charging page when charging starts
                if is_charging and not was_charging:
                    print("Charging started - auto-switching to Charging page")
                    current_mode = "Charging"
                    update_display_for_mode(current_mode)
                    last_page_change_time = time.ticks_ms()
                    last_mode_change_time = time.ticks_ms()
                # Log when charging stops (but don't reset timer - let auto-return handle it)
                elif not is_charging and was_charging:
                    print("Charging stopped - page will auto-return to Battery in 10s")

                # Refresh display if on Charging page (without resetting timer)
                if current_mode == "Charging":
                    update_display_for_mode(current_mode)

            except ValueError:
                print(f"Invalid charging state format: {state_str}")

        elif cmd_line.startswith(b'WIFI:'):
            # Update WiFi status
            # Format: WIFI:status (0=Disconnected, 1=Connected, 2=Skipped/Demo)
            status_str = cmd_line[5:].decode().strip()
            try:
                wifi_status = int(status_str)
                status_text = ["Disconnected", "Connected", "Skipped"][wifi_status] if 0 <= wifi_status <= 2 else "Unknown"
                print(f"WiFi status: {wifi_status} ({status_text})")
            except (ValueError, IndexError):
                print(f"Invalid WiFi status format: {status_str}")
            # Refresh display if on Status page
            if current_mode == "Status":
                update_display_for_mode(current_mode)

        elif cmd_line.startswith(b'DEMO:'):
            # Update demo mode status
            # Format: DEMO:state (0=Inactive, 1=Active)
            state_str = cmd_line[5:].decode().strip()
            try:
                demo_mode = int(state_str)
                mode_text = "Active" if demo_mode == 1 else "Inactive"
                print(f"Demo mode: {demo_mode} ({mode_text})")
            except ValueError:
                print(f"Invalid demo mode format: {state_str}")
            # Refresh display if on Status page
            if current_mode == "Status":
                update_display_for_mode(current_mode)

    except Exception as e:
        print(f"Error processing command: {e}")

def cycle_mode():
    """Cycle to the next display page"""
    global current_mode, last_page_change_time, last_mode_change_time

    # Normal page cycling: Battery → SystemInfo → Status → About → Battery
    # (Charging page is only shown when charging is active)
    modes = ["Battery", "SystemInfo", "Status", "About"]

    old_mode = current_mode
    try:
        current_index = modes.index(current_mode)
        next_index = (current_index + 1) % len(modes)
        current_mode = modes[next_index]
    except ValueError:
        # If current mode is not in list (e.g., Charging), go to Battery
        current_mode = "Battery"

    print(f"Page changed via touch: {old_mode} → {current_mode}")
    update_display_for_mode(current_mode)
    last_page_change_time = time.ticks_ms()
    last_mode_change_time = time.ticks_ms()

def update_display_for_mode(mode):
    """Update display based on selected page"""

    lcd.fill(lcd.black)  # Start with black background for all pages

    if mode == "Battery":
        # Battery monitor page - circular gauge with background image
        battery_monitor.render()

    elif mode == "SystemInfo":
        # System Information page - detailed battery metrics
        # Title
        lcd.text("SYSTEM INFO", 70, 15, lcd.white)

        # Draw horizontal line separator
        lcd.hline(10, 35, 220, lcd.white)

        # SOC
        lcd.text("SOC:", 20, 60, lcd.white)
        soc_text = f"{battery_soc}%"
        lcd.write_text(soc_text, 140, 57, 2, lcd.white)

        # Voltage
        lcd.text("Voltage:", 20, 95, lcd.white)
        voltage_text = f"{battery_voltage:.1f}V"
        lcd.write_text(voltage_text, 140, 92, 2, lcd.white)

        # Current
        lcd.text("Current:", 20, 130, lcd.white)
        # Show charging/discharging indicator
        if battery_current > 0:
            current_color = 0x07E0  # Green (charging)
            current_text = f"+{battery_current:.1f}A"
        elif battery_current < 0:
            current_color = 0xF800  # Red (discharging)
            current_text = f"{battery_current:.1f}A"
        else:
            current_color = lcd.white
            current_text = "0.0A"
        lcd.write_text(current_text, 140, 127, 2, current_color)

        # Temperature
        lcd.text("Temperature:", 20, 165, lcd.white)
        temp_text = f"{battery_temp:.1f}"
        lcd.write_text(temp_text, 140, 162, 2, lcd.white)
        lcd.text("o", 200, 163, lcd.white)
        lcd.text("C", 208, 168, lcd.white)

    elif mode == "Charging":
        # Charging page - displayed when battery is charging
        # Title
        lcd.text("CHARGING", 80, 20, lcd.white)

        # Draw horizontal line separator
        lcd.hline(10, 40, 220, lcd.white)

        # Charging metrics
        lcd.text("Current:", 20, 70, lcd.white)
        if battery_current > 0:
            charge_text = f"+{battery_current:.1f}A"
        else:
            charge_text = "0.0A"
        lcd.write_text(charge_text, 130, 67, 2, 0x07E0)  # Green

        lcd.text("Voltage:", 20, 105, lcd.white)
        voltage_text = f"{battery_voltage:.1f}V"
        lcd.write_text(voltage_text, 130, 102, 2, lcd.white)

        lcd.text("SOC:", 20, 140, lcd.white)
        soc_text = f"{battery_soc}%"
        lcd.write_text(soc_text, 130, 137, 2, lcd.white)

        lcd.text("Temperature:", 20, 175, lcd.white)
        temp_text = f"{battery_temp:.1f}"
        lcd.write_text(temp_text, 130, 172, 2, lcd.white)
        lcd.text("o", 190, 173, lcd.white)
        lcd.text("C", 198, 178, lcd.white)

    elif mode == "Status":
        # Status page - system status information
        # Title
        lcd.text("SYSTEM STATUS", 65, 20, lcd.white)

        # Draw horizontal line separator
        lcd.hline(10, 40, 220, lcd.white)

        # WiFi Status
        lcd.text("WiFi Status:", 20, 70, lcd.white)
        # Display WiFi status based on numeric value
        if wifi_status == 1:
            wifi_text = "Connected"
            wifi_color = 0x07E0  # Green
        elif wifi_status == 0:
            wifi_text = "Disconnected"
            wifi_color = 0xF800  # Red
        elif wifi_status == 2:
            wifi_text = "Skipped"
            wifi_color = lcd.white  # White
        else:
            wifi_text = "Unknown"
            wifi_color = lcd.white  # White
        lcd.write_text(wifi_text, 20, 87, 2, wifi_color)

        # Demo Mode - only display if active
        if demo_mode == 1:
            lcd.write_text("Demo Mode", 20, 140, 2, 0x07E0)  # Green

    elif mode == "About":
        # About page - application and author information
        # Application title (centered, large)
        lcd.text("Victron Battery", 55, 70, lcd.white)
        lcd.text("Display System", 55, 90, lcd.white)

        # Version/build info
        lcd.text("v1.0", 105, 120, lcd.white)

        # Horizontal separator
        lcd.hline(40, 145, 160, lcd.white)

        # Author information
        lcd.text("Developed by", 75, 160, lcd.white)
        lcd.text("Paul Williams", 70, 180, lcd.white)

    lcd.show()

def check_auto_return_to_battery():
    """Check if we should auto-return to Battery page after timeout"""
    global current_mode, last_page_change_time, last_mode_change_time

    # Don't auto-return if already on Battery page
    if current_mode == "Battery":
        return

    # Don't auto-return if on Charging page and battery is actively charging
    if current_mode == "Charging" and is_charging:
        return

    # Check if timeout has elapsed
    elapsed = time.ticks_diff(time.ticks_ms(), last_page_change_time)
    if elapsed > AUTO_RETURN_TIMEOUT_MS:
        old_mode = current_mode
        print(f"Auto-return triggered: {old_mode} → Battery (after {elapsed}ms)")
        current_mode = "Battery"
        update_display_for_mode(current_mode)
        last_page_change_time = time.ticks_ms()
        last_mode_change_time = time.ticks_ms()
        print(f"Auto-return complete, timer reset")

# Display initial Battery page after welcome message
update_display_for_mode(current_mode)
print(f"Started on {current_mode} page")

# Main loop
last_battery_check = time.ticks_ms()
last_touch_time = 0

while True:
    # Check for incoming commands from Raspberry Pi Pico
    if uart.any():
        cmd_line = uart.readline()
        if cmd_line:
            # print(f"Raw UART data received: {cmd_line}")
            process_command(cmd_line)

    # Check for touch events - full screen touch for page navigation
    if touch.Flag == 1:
        current_time = time.ticks_ms()
        # Only process touch if at least 500ms has passed since last touch (debounce)
        if time.ticks_diff(current_time, last_touch_time) > 500:
            touch.Flag = 0  # Reset flag
            x = touch.X_point
            y = touch.Y_point

            # Full screen touch - cycle to next page
            print(f"Screen touched at ({x}, {y}) - cycling to next page")
            cycle_mode()
            last_touch_time = current_time
        else:
            # Reset flag even if we ignore the touch
            touch.Flag = 0

    # Check for auto-return to Battery page
    check_auto_return_to_battery()

    # Check battery data staleness (every 30 seconds)
    if time.ticks_diff(time.ticks_ms(), last_battery_check) > 30000:
        if battery_monitor.is_stale():
            status = battery_monitor.get_status()
            print(f"WARNING: Battery data stale (age: {status['age_ms']}ms)")
        last_battery_check = time.ticks_ms()

    time.sleep(0.1)
