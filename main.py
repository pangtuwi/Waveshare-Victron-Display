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
wifi_status = "Unknown"  # WiFi connection status
demo_mode = "Unknown"  # Demo mode status

# Page navigation settings
AUTO_RETURN_TIMEOUT_MS = 10000  # 10 seconds to auto-return to Battery page
last_page_change_time = time.ticks_ms()

def process_command(cmd_line):
    """Process incoming commands from Raspberry Pi Pico via UART"""
    global current_brightness, current_mode, display_color
    global battery_soc, battery_voltage, battery_current, battery_temp, is_charging
    global wifi_status, demo_mode
    global battery_monitor, last_page_change_time

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
            current_mode = mode
            print(f"Mode changed to: {mode}")
            update_display_for_mode(mode)
            last_page_change_time = time.ticks_ms()

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
                if battery_monitor.update_soc(soc):
                    print(f"Battery SOC: {soc}%")
                    # Refresh display if on Battery page
                    if current_mode == "Battery":
                        update_display_for_mode(current_mode)
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
                    # Refresh display if on SystemInfo page
                    if current_mode == "SystemInfo":
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
                    print("Charging started - switching to Charging page")
                    current_mode = "Charging"
                    update_display_for_mode(current_mode)
                    last_page_change_time = time.ticks_ms()
                # Return to Battery page when charging stops (after timeout)
                elif not is_charging and was_charging:
                    print("Charging stopped")
                    if current_mode == "Charging":
                        # Stay on Charging page but allow timeout to return to Battery
                        last_page_change_time = time.ticks_ms()

                # Refresh display if on Charging page
                if current_mode == "Charging":
                    update_display_for_mode(current_mode)

            except ValueError:
                print(f"Invalid charging state format: {state_str}")

        elif cmd_line.startswith(b'WIFI:'):
            # Update WiFi status
            # Format: WIFI:status
            status_str = cmd_line[5:].decode().strip()
            wifi_status = status_str
            print(f"WiFi status: {wifi_status}")
            # Refresh display if on Status page
            if current_mode == "Status":
                update_display_for_mode(current_mode)

        elif cmd_line.startswith(b'DEMO:'):
            # Update demo mode status
            # Format: DEMO:state
            state_str = cmd_line[5:].decode().strip()
            demo_mode = state_str
            print(f"Demo mode: {demo_mode}")
            # Refresh display if on Status page
            if current_mode == "Status":
                update_display_for_mode(current_mode)

    except Exception as e:
        print(f"Error processing command: {e}")

def cycle_mode():
    """Cycle to the next display page"""
    global current_mode, last_page_change_time

    # Normal page cycling: Battery → SystemInfo → Status → About → Battery
    # (Charging page is only shown when charging is active)
    modes = ["Battery", "SystemInfo", "Status", "About"]

    try:
        current_index = modes.index(current_mode)
        next_index = (current_index + 1) % len(modes)
        current_mode = modes[next_index]
    except ValueError:
        # If current mode is not in list (e.g., Charging), go to Battery
        current_mode = "Battery"

    print(f"Page changed to: {current_mode}")
    update_display_for_mode(current_mode)
    last_page_change_time = time.ticks_ms()

def update_display_for_mode(mode):
    """Update display based on selected page"""

    lcd.fill(lcd.black)  # Start with black background for all pages

    if mode == "Battery":
        # Battery monitor page - circular gauge with background image
        battery_monitor.render()

    elif mode == "SystemInfo":
        # System Information page - detailed battery metrics
        # Title
        lcd.text("SYSTEM INFO", 70, 20, lcd.white)

        # Draw horizontal line separator
        lcd.hline(10, 40, 220, lcd.white)

        # SOC
        lcd.text("State of Charge:", 20, 60, lcd.white)
        soc_text = f"{battery_soc}%"
        soc_width = bitmap_fonts_32.get_text_width_32(soc_text, spacing=2)
        soc_x = (240 - soc_width) // 2
        bitmap_fonts_32.draw_text_32(lcd, soc_text, soc_x, 75, lcd.white, spacing=2)

        # Voltage
        lcd.text("Voltage:", 20, 120, lcd.white)
        voltage_text = f"{battery_voltage:.2f}V"
        lcd.write_text(voltage_text, 140, 117, 2, lcd.white)

        # Current
        lcd.text("Current:", 20, 150, lcd.white)
        # Show charging/discharging indicator
        if battery_current > 0:
            current_color = 0x07E0  # Green (charging)
            current_text = f"+{battery_current:.2f}A"
        elif battery_current < 0:
            current_color = 0xF800  # Red (discharging)
            current_text = f"{battery_current:.2f}A"
        else:
            current_color = lcd.white
            current_text = "0.00A"
        lcd.write_text(current_text, 140, 147, 2, current_color)

        # Temperature
        lcd.text("Temperature:", 20, 180, lcd.white)
        temp_text = f"{battery_temp:.1f}"
        lcd.write_text(temp_text, 140, 177, 2, lcd.white)
        lcd.text("o", 200, 178, lcd.white)
        lcd.text("C", 208, 183, lcd.white)

    elif mode == "Charging":
        # Charging page - displayed when battery is charging
        # Title with animation indicator
        lcd.text("CHARGING", 80, 30, lcd.white)

        # Draw animated charging bolt icon (simple triangular bolt)
        # Center coordinates
        cx, cy = 120, 100

        # Draw charging bolt as filled triangles
        # Upper triangle (pointing down)
        for y in range(15):
            lcd.hline(cx - y//2, cy - 15 + y, y + 1, 0x07E0)  # Green
        # Lower triangle (pointing up)
        for y in range(15):
            lcd.hline(cx - (14-y)//2, cy + y, (14-y) + 1, 0x07E0)  # Green

        # Charging metrics
        lcd.text("Current:", 20, 140, lcd.white)
        if battery_current > 0:
            charge_text = f"+{battery_current:.2f}A"
        else:
            charge_text = "0.00A"
        lcd.write_text(charge_text, 130, 137, 2, 0x07E0)  # Green

        lcd.text("Voltage:", 20, 170, lcd.white)
        voltage_text = f"{battery_voltage:.2f}V"
        lcd.write_text(voltage_text, 130, 167, 2, lcd.white)

        lcd.text("SOC:", 20, 200, lcd.white)
        soc_text = f"{battery_soc}%"
        lcd.write_text(soc_text, 130, 197, 2, lcd.white)

    elif mode == "Status":
        # Status page - system status information
        # Title
        lcd.text("SYSTEM STATUS", 65, 20, lcd.white)

        # Draw horizontal line separator
        lcd.hline(10, 40, 220, lcd.white)

        # WiFi Status
        lcd.text("WiFi Status:", 20, 70, lcd.white)
        # Color-code WiFi status
        if "Connected" in wifi_status or "OK" in wifi_status or "Active" in wifi_status:
            wifi_color = 0x07E0  # Green for connected
        elif "Disconnected" in wifi_status or "Failed" in wifi_status or "Error" in wifi_status:
            wifi_color = 0xF800  # Red for disconnected
        else:
            wifi_color = lcd.white  # White for unknown
        lcd.write_text(wifi_status, 20, 87, 2, wifi_color)

        # Demo Mode Status
        lcd.text("Demo Mode:", 20, 140, lcd.white)
        # Color-code demo mode
        if "Active" in demo_mode or "ON" in demo_mode or "Enabled" in demo_mode:
            demo_color = 0x07E0  # Green for active
        elif "Inactive" in demo_mode or "OFF" in demo_mode or "Disabled" in demo_mode:
            demo_color = lcd.white  # White for inactive
        else:
            demo_color = lcd.white  # White for unknown
        lcd.write_text(demo_mode, 20, 157, 2, demo_color)

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
        lcd.write_text("Paul Williams", 50, 177, 2, lcd.white)

    lcd.show()

def check_auto_return_to_battery():
    """Check if we should auto-return to Battery page after timeout"""
    global current_mode, last_page_change_time

    # Don't auto-return if already on Battery page
    if current_mode == "Battery":
        return

    # Check if timeout has elapsed
    elapsed = time.ticks_diff(time.ticks_ms(), last_page_change_time)
    if elapsed > AUTO_RETURN_TIMEOUT_MS:
        print(f"Auto-returning to Battery page after {elapsed}ms")
        current_mode = "Battery"
        update_display_for_mode(current_mode)
        last_page_change_time = time.ticks_ms()

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
            print(f"Raw UART data received: {cmd_line}")
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
