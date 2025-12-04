from LCD_1inch28 import LCD_1inch28
from circular_gauge import CircularGauge, rgb_to_brg565
import time

# Initialize the LCD display
lcd = LCD_1inch28()

# Set brightness to maximum
lcd.set_bl_pwm(65535)

print("=== CircularGauge Screen Tests ===")
print("Starting comprehensive gauge tests...")

# Test 1: Basic top arc gauge with default settings
print("\nTest 1: Top arc gauge - 12 segments, 50%")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=110,
    thickness=12,
    segments=12,
    start_angle=135,  # Top-left
    end_angle=405,    # Top-right (270° arc)
    gap_degrees=2,
    color=lcd.white
)
gauge.update(50)
lcd.text("Top Arc 50%", 80, 120, lcd.white)
lcd.show()
print("  Top arc: 50% fill with 12 segments")
time.sleep(10)

# Test 2: Different segment counts
print("\nTest 2: Segment count variations")
for seg_count in [4, 8, 16, 20]:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=10,
        segments=seg_count,
        start_angle=135,
        end_angle=405,
        gap_degrees=3,
        color=lcd.white
    )
    gauge.update(66)
    lcd.text(f"Segments: {seg_count}", 75, 120, lcd.white)
    lcd.show()
    print(f"  {seg_count} segments at 66%")
    time.sleep(10)

# Test 3: Percentage progression (0% to 100%)
print("\nTest 3: Animated 0% to 100% progression")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=110,
    thickness=12,
    segments=16,
    start_angle=135,
    end_angle=405,
    gap_degrees=2,
    color=lcd.white,
    background_color=rgb_to_brg565(64, 64, 64)  # Dark grey
)
for val in range(0, 101, 10):
    lcd.fill(lcd.black)
    gauge.update(val)
    lcd.text(f"Value: {val}%", 85, 120, lcd.white)
    lcd.show()
    print(f"  {val}%")
    time.sleep(0.5)

time.sleep(10)

# Test 4: Full circle (360 degrees)
print("\nTest 4: Full circle gauge")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=100,
    thickness=8,
    segments=20,
    start_angle=0,
    end_angle=360,
    gap_degrees=2,
    color=lcd.white
)
gauge.update(75)
lcd.text("Full Circle 75%", 65, 120, lcd.white)
lcd.show()
print("  Full 360° circle at 75%")
time.sleep(10)

# Test 5: Different angle ranges
print("\nTest 5: Various arc ranges")
arc_configs = [
    (0, 180, "Right Half"),      # Right semicircle
    (90, 270, "Top Half"),        # Top semicircle
    (270, 450, "Bottom Half"),    # Bottom semicircle (270° to 90°)
    (225, 495, "Bottom Arc"),     # Bottom arc (speedometer style)
    (45, 315, "Three-Quarter"),   # 270° from top-right to bottom
]
for start, end, label in arc_configs:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=10,
        segments=12,
        start_angle=start,
        end_angle=end,
        gap_degrees=2,
        color=lcd.white
    )
    gauge.update(60)
    lcd.text(label, 70, 120, lcd.white)
    lcd.show()
    print(f"  {label}: {start}° to {end}° at 60%")
    time.sleep(10)

# Test 6: Bottom arc (speedometer style) demo
print("\nTest 6: Bottom arc speedometer demo")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=150,  # Move center down for better visibility
    radius=100,
    thickness=15,
    segments=16,
    start_angle=225,  # Bottom-left
    end_angle=495,    # Bottom-right (270° arc)
    gap_degrees=2,
    color=rgb_to_brg565(0, 255, 0),  # Green
    background_color=rgb_to_brg565(32, 32, 32)  # Dark grey
)
for val in [0, 25, 50, 75, 100]:
    lcd.fill(lcd.black)
    gauge.update(val)
    lcd.text("Speedometer", 75, 20, lcd.white)
    lcd.text(f"{val}%", 105, 140, lcd.white)
    lcd.show()
    print(f"  Bottom arc at {val}%")
    time.sleep(1.5)

# Test 7: Different thickness values
print("\nTest 7: Thickness variations")
for thickness in [5, 10, 15, 20]:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=thickness,
        segments=12,
        start_angle=135,
        end_angle=405,
        gap_degrees=2,
        color=lcd.white
    )
    gauge.update(70)
    lcd.text(f"Thickness: {thickness}px", 70, 220, lcd.white)
    lcd.show()
    print(f"  Thickness {thickness}px at 70%")
    time.sleep(2)

# Test 8: Color variations (using BRG format)
print("\nTest 8: Different colors")
colors = [
    (lcd.white, "White"),
    (lcd.red, "Red (BRG Green)"),
    (lcd.green, "Green (BRG Blue)"),
    (lcd.blue, "Blue (BRG Red)"),
    (rgb_to_brg565(255, 128, 0), "Orange"),
    (rgb_to_brg565(128, 0, 255), "Purple"),
]
for color, label in colors:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=12,
        segments=12,
        start_angle=135,
        end_angle=405,
        gap_degrees=2,
        color=color
    )
    gauge.update(80)
    lcd.text(label, 70, 220, lcd.white)
    lcd.show()
    print(f"  {label} at 80%")
    time.sleep(2)

# Test 9: Background color (filled vs unfilled segments)
print("\nTest 9: With background color")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=110,
    thickness=12,
    segments=16,
    start_angle=135,
    end_angle=405,
    gap_degrees=2,
    color=lcd.white,
    background_color=rgb_to_brg565(64, 64, 64)  # Dark grey unfilled
)
gauge.update(40)
lcd.text("With Background", 65, 220, lcd.white)
lcd.show()
print("  40% with dark grey background segments")
time.sleep(3)

# Test 10: Edge cases
print("\nTest 10: Edge cases")
edge_cases = [
    (0, "0% Empty"),
    (100, "100% Full"),
    (1, "1% Minimal"),
    (99, "99% Nearly Full"),
]
for val, label in edge_cases:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=12,
        segments=12,
        start_angle=135,
        end_angle=405,
        gap_degrees=2,
        color=lcd.white,
        background_color=rgb_to_brg565(64, 64, 64)
    )
    gauge.update(val)
    lcd.text(label, 80, 220, lcd.white)
    lcd.show()
    print(f"  {label}")
    time.sleep(2)

# Test 11: Incremental update test
print("\nTest 11: Incremental update performance")
lcd.fill(lcd.black)
gauge = CircularGauge(
    lcd=lcd,
    center_x=120,
    center_y=120,
    radius=110,
    thickness=12,
    segments=12,
    start_angle=135,
    end_angle=405,
    gap_degrees=2,
    color=lcd.white,
    background_color=rgb_to_brg565(64, 64, 64)
)
gauge.update(0)
lcd.show()

for val in range(0, 101, 8):
    old_val = gauge.value
    gauge.set_value(val)
    gauge.draw_incremental(old_val)
    lcd.fill_rect(70, 220, 100, 10, lcd.black)  # Clear text area
    lcd.text(f"Incr: {val}%", 75, 220, lcd.white)
    lcd.show()
    print(f"  Incremental update to {val}%")
    time.sleep(0.3)

# Test 12: Clockwise gauges
print("\nTest 12: Clockwise drawing")
clockwise_configs = [
    (45, 315, "Right Side CW"),     # 90° clockwise on right
    (135, 45, "Top Side CW"),       # 90° clockwise on top
    (225, 135, "Left Side CW"),     # 90° clockwise on left
    (315, 225, "Bottom Side CW"),   # 90° clockwise on bottom
]
for start, end, label in clockwise_configs:
    lcd.fill(lcd.black)
    gauge = CircularGauge(
        lcd=lcd,
        center_x=120,
        center_y=120,
        radius=110,
        thickness=12,
        segments=8,
        start_angle=start,
        end_angle=end,
        gap_degrees=2,
        color=rgb_to_brg565(255, 128, 0),  # Orange
        background_color=rgb_to_brg565(32, 32, 32),
        clockwise=True
    )
    gauge.update(75)
    lcd.text(label, 65, 220, lcd.white)
    lcd.show()
    print(f"  {label}: {start}° to {end}° (clockwise) at 75%")
    time.sleep(2)

# Test 13: Clockwise vs Counter-clockwise comparison
print("\nTest 13: Clockwise vs Counter-clockwise comparison")
# Counter-clockwise (normal)
lcd.fill(lcd.black)
gauge_ccw = CircularGauge(
    lcd=lcd,
    center_x=60,
    center_y=120,
    radius=50,
    thickness=10,
    segments=8,
    start_angle=0,
    end_angle=270,
    gap_degrees=2,
    color=rgb_to_brg565(0, 255, 0),  # Green
    clockwise=False
)
gauge_ccw.update(75)
lcd.text("CCW", 35, 180, lcd.white)

# Clockwise
gauge_cw = CircularGauge(
    lcd=lcd,
    center_x=180,
    center_y=120,
    radius=50,
    thickness=10,
    segments=8,
    start_angle=0,
    end_angle=270,
    gap_degrees=2,
    color=rgb_to_brg565(255, 0, 0),  # Red
    clockwise=True
)
gauge_cw.update(75)
lcd.text("CW", 165, 180, lcd.white)

lcd.text("0->270deg 75%", 65, 20, lcd.white)
lcd.show()
print("  Side-by-side: CCW (green) vs CW (red)")
time.sleep(4)

# Final summary display
print("\n=== All Tests Complete ===")
lcd.fill(lcd.black)
lcd.text("All Tests", 80, 100, lcd.white)
lcd.text("Complete!", 80, 120, lcd.white)
lcd.show()

print("\nCircularGauge test suite finished successfully!")
print("Display will remain on. Press Ctrl+C to exit.")

# Keep the display on
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nScreen test ended")
