from machine import UART, Pin, RTC
from LCD_1inch28 import LCD_1inch28, Touch_CST816T
import time
import json
import bitmap_fonts
import bitmap_fonts_32
import bitmap_fonts_48

# Initialize UART
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# Initialize RTC
rtc = RTC()

# Initialize display
lcd = LCD_1inch28()
lcd.set_bl_pwm(65535)  # Set brightness to maximum

# Initialize touch controller
touch = Touch_CST816T(mode=1, LCD=lcd)  # Mode 1 = point mode

# Display welcome message
lcd.fill(lcd.white)
lcd.text("Home Assistant", 60, 100, lcd.black)
lcd.text("Display", 85, 120, lcd.black)
lcd.text("Ready!", 90, 140, lcd.black)
lcd.show()
print("Welcome message displayed")

# Wait for 2 seconds to show welcome message
time.sleep(2)

# Display settings
current_brightness = 100
current_mode = "Clock"
display_color = lcd.black

# Custom mode cycling
custom_sub_modes = ["Clock", "Weather", "Bedroom"]
current_custom_index = 0

# Weather data
weather_condition = "N/A"
weather_temp = "N/A"
weather_humidity = "N/A"

# Bedroom temperature data
bedroom_temp = "N/A"
bedroom_humidity = "N/A"

# Hive thermostat data
hive_current_temp = "N/A"
hive_target_temp = "N/A"
hive_heating_status = "OFF"
hive_hotwater_status = "OFF"

def process_command(cmd_line):
    """Process incoming commands from Home Assistant via ESP32"""
    global current_brightness, current_mode, display_color, weather_condition, weather_temp, weather_humidity
    global hive_current_temp, hive_target_temp, hive_heating_status, hive_hotwater_status
    global bedroom_temp, bedroom_humidity

    try:
        print(f"Received command: {cmd_line}")
        if cmd_line.startswith(b'MSG:'):
            # Display a text message
            message = cmd_line[4:].decode().strip()
            lcd.fill(lcd.white)
            lcd.text(message, 60, 120, display_color)
            lcd.show()
            print(f"Displayed: {message}")
            
        elif cmd_line.startswith(b'BRIGHT:'):
            # Adjust brightness
            brightness = int(cmd_line[7:].decode().strip())
            current_brightness = brightness
            lcd.set_bl_pwm(int(brightness * 65535 / 100))
            print(f"Brightness set to: {brightness}%")
            
        elif cmd_line.startswith(b'MODE:'):
            # Change display mode
            mode = cmd_line[5:].decode().strip()
            current_mode = mode
            print(f"Mode changed to: {mode}")
            update_display_for_mode(mode)
            
        elif cmd_line.startswith(b'CMD:CLEAR'):
            # Clear display
            lcd.fill(lcd.white)
            lcd.show()
            print("Display cleared")
            
        elif cmd_line.startswith(b'CMD:TIME'):
            # Show time (you'd get this from RTC or network)
            lcd.fill(lcd.white)
            lcd.text("12:34 PM", 80, 120, lcd.black)
            lcd.show()
            print("Time displayed")
            
        elif cmd_line.startswith(b'DISP:'):
            # Custom display command
            data = cmd_line[5:].decode().strip()
            lcd.fill(lcd.white)
            lcd.text(data, 60, 120, display_color)
            lcd.show()
            print(f"Custom display: {data}")
            
        elif cmd_line.startswith(b'COLOR:'):
            # Set text color (RGB)
            colors = cmd_line[6:].decode().strip().split(',')
            r, g, b = int(colors[0]), int(colors[1]), int(colors[2])
            # Convert RGB888 to RGB565 format (note: uses BRG format due to framebuf)
            display_color = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
            print(f"Color set to RGB({r},{g},{b})")

        elif cmd_line.startswith(b'SETTIME:'):
            # Set RTC time from ESP32
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
                # Refresh display if in clock mode
                if current_mode == "Clock":
                    update_display_for_mode(current_mode)

        elif cmd_line.startswith(b'WEATHER:'):
            # Update weather data
            # Format: WEATHER:condition,temperature,humidity
            weather_str = cmd_line[8:].decode().strip()
            weather_parts = weather_str.split(',')
            if len(weather_parts) == 3:
                weather_condition = weather_parts[0]
                weather_temp = weather_parts[1]
                weather_humidity = weather_parts[2]
                print(f"Weather updated: {weather_condition}, {weather_temp}, {weather_humidity}")
                # Refresh display if in weather mode
                if current_mode == "Weather":
                    update_display_for_mode(current_mode)

        elif cmd_line.startswith(b'HIVE:'):
            # Update Hive thermostat data
            # Format: HIVE:current_temp,target_temp,heating_status,hotwater_status
            hive_str = cmd_line[5:].decode().strip()
            hive_parts = hive_str.split(',')
            if len(hive_parts) == 4:
                hive_current_temp = hive_parts[0]
                hive_target_temp = hive_parts[1]
                hive_heating_status = hive_parts[2]
                hive_hotwater_status = hive_parts[3]
                print(f"Hive updated: Current={hive_current_temp}, Target={hive_target_temp}, Heating={hive_heating_status}, HotWater={hive_hotwater_status}")
                # Refresh display if in bedroom mode (kept for backwards compatibility)
                if current_mode == "Bedroom":
                    update_display_for_mode(current_mode)

        elif cmd_line.startswith(b'BEDROOM:'):
            # Update bedroom temperature data
            # Format: BEDROOM:temperature,humidity
            bedroom_str = cmd_line[8:].decode().strip()
            bedroom_parts = bedroom_str.split(',')
            if len(bedroom_parts) == 2:
                bedroom_temp = bedroom_parts[0]
                bedroom_humidity = bedroom_parts[1]
                print(f"Bedroom updated: Temp={bedroom_temp}, Humidity={bedroom_humidity}")
                # Refresh display if in bedroom mode
                if current_mode == "Bedroom":
                    update_display_for_mode(current_mode)

    except Exception as e:
        print(f"Error processing command: {e}")

def draw_mode_button(mode):
    """Draw a mode change button at the bottom of the screen"""
    # Button area: bottom 30 pixels (y: 210-240)
    button_color = lcd.blue if mode == "Clock" else lcd.red
    lcd.fill_rect(0, 210, 240, 30, button_color)

    # Center the mode name
    mode_x = 120 - (len(mode) * 4)  # Approximate centering
    lcd.text(mode, mode_x, 220, lcd.white)

def cycle_mode():
    """Cycle to the next display mode"""
    global current_mode
    modes = ["Clock", "Bedroom", "Weather", "Cycle"]
    current_index = modes.index(current_mode)
    next_index = (current_index + 1) % len(modes)
    current_mode = modes[next_index]
    print(f"Mode changed to: {current_mode}")
    update_display_for_mode(current_mode)

def update_display_for_mode(mode):
    """Update display based on selected mode"""

    if mode == "Clock":
        # Black background for clock mode
        lcd.fill(lcd.black)

        # Get current time
        current_time = time.localtime()
        hour = current_time[3]
        minute = current_time[4]

        # Get date info
        year = current_time[0]
        month = current_time[1]
        day = current_time[2]
        weekday = current_time[6]

        # Day names
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_name = days[weekday]

        # Format time as 12-hour with AM/PM
        am_pm = "AM" if hour < 12 else "PM"
        display_hour = hour if hour < 12 else hour - 12
        if display_hour == 0:
            display_hour = 12

        # Just the time without AM/PM for larger display
        time_str = "{:02d}:{:02d}".format(display_hour, minute)

        # Top: Day and date
        date_str = "{} {}/{}/{}".format(day_name, day, month, year)
        lcd.text(date_str, 55, 50, lcd.white)

        # Center: Very large time using bitmap font (16x24 per char)
        # Calculate centering for time string
        time_width = bitmap_fonts.get_text_width(time_str, spacing=4)
        time_x = (240 - time_width) // 2
        bitmap_fonts.draw_text(lcd, time_str, time_x, 100, lcd.white, spacing=4)

        # AM/PM indicator below time
        lcd.write_text(am_pm, 100, 155, 2, lcd.white)

    elif mode == "Bedroom":
        # Dark grey background for bedroom mode (RGB 64,64,64 in BRG format)
        dark_grey = 0x4208
        lcd.fill(dark_grey)

        # Title
        lcd.text("BEDROOM", 85, 30, lcd.white)

        # Temperature (large)
        lcd.text("Temperature", 75, 60, lcd.white)
        if bedroom_temp != "N/A":
            temp_display = bedroom_temp.replace("°C", "").replace(" C", "").strip()
            temp_width = bitmap_fonts_32.get_text_width_32(temp_display, spacing=2)
            temp_x = (240 - temp_width - 15) // 2
            bitmap_fonts_32.draw_text_32(lcd, temp_display, temp_x, 90, lcd.white, spacing=2)
            lcd.text("o", temp_x + temp_width + 2, 92, lcd.white)
            lcd.text("C", temp_x + temp_width + 10, 100, lcd.white)
        else:
            lcd.write_text("--.-C", 75, 90, 3, 0x7BEF)  # Gray

        # Humidity
        lcd.text("Humidity", 85, 150, lcd.white)
        if bedroom_humidity != "N/A":
            humidity_display = bedroom_humidity.replace("%", "").strip()
            humidity_width = bitmap_fonts.get_text_width(humidity_display, spacing=2)
            humidity_x = (240 - humidity_width - 20) // 2
            bitmap_fonts.draw_text(lcd, humidity_display, humidity_x, 165, lcd.white, spacing=2)
            lcd.text("%", humidity_x + humidity_width + 4, 175, lcd.white)
        else:
            lcd.write_text("--%", 95, 165, 2, 0x7BEF)  # Gray

    elif mode == "Weather":
        # Black background for weather mode
        lcd.fill(lcd.black)

        # Weather condition at top (centered)
        condition_x = 120 - (len(weather_condition) * 4)  # Approximate centering
        lcd.write_text(weather_condition, condition_x, 30, 2, lcd.white)

        # Very large temperature in center using 32px bitmap font
        temp_display = weather_temp.replace("°C", "").replace(" C", "").strip()
        temp_width = bitmap_fonts_48.get_text_width_48(temp_display, spacing=3)
        temp_x = (240 - temp_width) // 2
        bitmap_fonts_48.draw_text_48(lcd, temp_display, temp_x, 70, lcd.white, spacing=3)

        # Degree symbol and C
        lcd.text("o", temp_x + temp_width + 2, 72, lcd.white)
        lcd.text("C", temp_x + temp_width + 10, 78, lcd.white)

        # Humidity at bottom using 24px bitmap font
        lcd.text("Humidity", 80, 140, lcd.white)
        humidity_display = weather_humidity.replace("%", "").strip()
        humidity_width = bitmap_fonts.get_text_width(humidity_display, spacing=2)
        humidity_x = (240 - humidity_width - 20) // 2  # Account for % symbol
        bitmap_fonts.draw_text(lcd, humidity_display, humidity_x, 155, lcd.white, spacing=2)
        lcd.text("%", humidity_x + humidity_width + 4, 165, lcd.white)

    elif mode == "Cycle":
        # Cycle mode cycles through Clock, Weather, and Sensors
        # Display the current sub-mode
        sub_mode = custom_sub_modes[current_custom_index]

        if sub_mode == "Clock":
            # Black background for clock mode
            lcd.fill(lcd.black)

            # Get current time
            current_time = time.localtime()
            hour = current_time[3]
            minute = current_time[4]

            # Get date info
            year = current_time[0]
            month = current_time[1]
            day = current_time[2]
            weekday = current_time[6]

            # Day names
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = days[weekday]

            # Format time as 12-hour with AM/PM
            am_pm = "AM" if hour < 12 else "PM"
            display_hour = hour if hour < 12 else hour - 12
            if display_hour == 0:
                display_hour = 12

            # Just the time without AM/PM for larger display
            time_str = "{:02d}:{:02d}".format(display_hour, minute)

            # Top: Day and date
            date_str = "{} {}/{}/{}".format(day_name, day, month, year)
            lcd.text(date_str, 55, 50, lcd.white)

            # Center: Very large time using bitmap font (16x24 per char)
            # Calculate centering for time string
            time_width = bitmap_fonts.get_text_width(time_str, spacing=4)
            time_x = (240 - time_width) // 2
            bitmap_fonts.draw_text(lcd, time_str, time_x, 100, lcd.white, spacing=4)

            # AM/PM indicator below time
            lcd.write_text(am_pm, 100, 155, 2, lcd.white)

        elif sub_mode == "Weather":
            # Black background for weather mode
            lcd.fill(lcd.black)

            # Weather condition at top (centered)
            condition_x = 120 - (len(weather_condition) * 4)
            lcd.write_text(weather_condition, condition_x, 30, 2, lcd.white)

            # Very large temperature in center using 32px bitmap font
            temp_display = weather_temp.replace("°C", "").replace(" C", "").strip()
            temp_width = bitmap_fonts_32.get_text_width_32(temp_display, spacing=3)
            temp_x = (240 - temp_width) // 2
            bitmap_fonts_32.draw_text_32(lcd, temp_display, temp_x, 70, lcd.white, spacing=3)

            # Degree symbol and C
            lcd.text("o", temp_x + temp_width + 2, 72, lcd.white)
            lcd.text("C", temp_x + temp_width + 10, 78, lcd.white)

            # Humidity at bottom using 24px bitmap font
            lcd.text("Humidity", 80, 140, lcd.white)
            humidity_display = weather_humidity.replace("%", "").strip()
            humidity_width = bitmap_fonts.get_text_width(humidity_display, spacing=2)
            humidity_x = (240 - humidity_width - 20) // 2
            bitmap_fonts.draw_text(lcd, humidity_display, humidity_x, 155, lcd.white, spacing=2)
            lcd.text("%", humidity_x + humidity_width + 4, 165, lcd.white)

        elif sub_mode == "Bedroom":
            # Dark grey background for bedroom mode (RGB 64,64,64 in BRG format)
            dark_grey = 0x4208
            lcd.fill(dark_grey)

            # Title
            lcd.text("BEDROOM", 85, 30, lcd.white)

            # Temperature (large)
            lcd.text("Temperature", 75, 60, lcd.white)
            if bedroom_temp != "N/A":
                temp_display = bedroom_temp.replace("°C", "").replace(" C", "").strip()
                temp_width = bitmap_fonts_32.get_text_width_32(temp_display, spacing=2)
                temp_x = (240 - temp_width - 15) // 2
                bitmap_fonts_32.draw_text_32(lcd, temp_display, temp_x, 90, lcd.white, spacing=2)
                lcd.text("o", temp_x + temp_width + 2, 92, lcd.white)
                lcd.text("C", temp_x + temp_width + 10, 100, lcd.white)
            else:
                lcd.write_text("--.-C", 75, 90, 3, 0x7BEF)  # Gray

            # Humidity
            lcd.text("Humidity", 85, 150, lcd.white)
            if bedroom_humidity != "N/A":
                humidity_display = bedroom_humidity.replace("%", "").strip()
                humidity_width = bitmap_fonts.get_text_width(humidity_display, spacing=2)
                humidity_x = (240 - humidity_width - 20) // 2
                bitmap_fonts.draw_text(lcd, humidity_display, humidity_x, 165, lcd.white, spacing=2)
                lcd.text("%", humidity_x + humidity_width + 4, 175, lcd.white)
            else:
                lcd.write_text("--%", 95, 165, 2, 0x7BEF)  # Gray

    # Draw mode button at the bottom
    draw_mode_button(mode)

    lcd.show()

def send_sensor_data():
    """Send sensor data back to Home Assistant"""
    # Read from IMU or other sensors
    data = {
        "temperature": 22.5,
        "status": "OK",
        "mode": current_mode
    }
    uart.write(f"SENSOR:{json.dumps(data)}\n".encode())

# Display initial clock mode after welcome message
update_display_for_mode(current_mode)
print(f"Switched to {current_mode} mode")

# Main loop
last_sensor_update = time.ticks_ms()
last_clock_update = time.ticks_ms()
last_custom_update = time.ticks_ms()
last_touch_time = 0

while True:
    # Check for incoming commands from Home Assistant
    if uart.any():
        cmd_line = uart.readline()
        if cmd_line:
            print(f"Raw UART data received: {cmd_line}")
            process_command(cmd_line)

    # Check for touch events
    if touch.Flag == 1:
        current_time = time.ticks_ms()
        # Only process touch if at least 500ms has passed since last touch
        if time.ticks_diff(current_time, last_touch_time) > 500:
            touch.Flag = 0  # Reset flag
            x = touch.X_point
            y = touch.Y_point

            # Check if touch is in button area (y: 210-240)
            if y >= 210 and y <= 240:
                print(f"Mode button touched at ({x}, {y})")
                cycle_mode()
                last_touch_time = current_time
        else:
            # Reset flag even if we ignore the touch
            touch.Flag = 0

    # Update clock display every minute if in clock mode
    if current_mode == "Clock" and time.ticks_diff(time.ticks_ms(), last_clock_update) > 60000:
        update_display_for_mode(current_mode)
        last_clock_update = time.ticks_ms()

    # Cycle mode display every 10 seconds
    if current_mode == "Cycle" and time.ticks_diff(time.ticks_ms(), last_custom_update) > 10000:
        current_custom_index = (current_custom_index + 1) % len(custom_sub_modes)
        print(f"Cycle mode cycling to: {custom_sub_modes[current_custom_index]}")
        update_display_for_mode(current_mode)
        last_custom_update = time.ticks_ms()

    # Send sensor data periodically (every 10 seconds)
    if time.ticks_diff(time.ticks_ms(), last_sensor_update) > 10000:
        send_sensor_data()
        last_sensor_update = time.ticks_ms()

    time.sleep(0.1)