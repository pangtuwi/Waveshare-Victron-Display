# Circular Gauge Display Module
# Draws segmented circular gauge/progress indicators on LCD_1inch28 display
# Supports configurable segments, angles, thickness, gaps, and colors

import math


class CircularGauge:
    """
    Progressive fill circular gauge for LCD_1inch28 display.
    Draws arc segments that fill based on 0-100% value.

    Angle System (0° = right, increases counter-clockwise):
        - 0° = Right (3 o'clock)
        - 90° = Top (12 o'clock)
        - 180° = Left (9 o'clock)
        - 270° = Bottom (6 o'clock)

    Example - Top arc gauge:
        gauge = CircularGauge(
            lcd=lcd,
            center_x=120,
            center_y=120,
            radius=100,
            thickness=10,
            segments=12,
            start_angle=135,  # Top-left
            end_angle=405,    # Top-right (270° arc)
            gap_degrees=2,
            color=lcd.white
        )
        gauge.set_value(75)  # 75% filled
        gauge.draw()
        lcd.show()

    Example - Bottom arc gauge (speedometer style):
        gauge = CircularGauge(
            lcd=lcd,
            center_x=120,
            center_y=120,
            radius=100,
            thickness=10,
            segments=12,
            start_angle=225,  # Bottom-left
            end_angle=495,    # Bottom-right (270° arc)
            gap_degrees=2,
            color=lcd.white
        )

    Example - Clockwise gauge (right side, 90° arc):
        gauge = CircularGauge(
            lcd=lcd,
            center_x=120,
            center_y=120,
            radius=100,
            thickness=10,
            segments=8,
            start_angle=45,   # Top-right
            end_angle=315,    # Bottom-right (90° clockwise)
            gap_degrees=2,
            color=lcd.white,
            clockwise=True
        )
    """

    def __init__(self, lcd, center_x, center_y, radius, thickness=10,
                 segments=12, start_angle=135, end_angle=405,
                 gap_degrees=2, color=0xFFFF, background_color=None,
                 clockwise=False):
        """
        Initialize circular gauge.

        Args:
            lcd: LCD_1inch28 instance (framebuffer)
            center_x: X coordinate of gauge center (0-239)
            center_y: Y coordinate of gauge center (0-239)
            radius: Outer radius in pixels
            thickness: Arc thickness in pixels (default 10)
            segments: Number of segments (4-20, default 12)
            start_angle: Starting angle in degrees (0=right, 90=top, 180=left, 270=bottom)
                        Default 135 = top-left for a top arc
            end_angle: Ending angle in degrees (can be >360 for wraparound arcs)
                      Default 405 = top-right (270° arc from top-left)
            gap_degrees: Gap between segments in degrees (default 2)
            color: RGB565 color for filled segments (default white)
            background_color: RGB565 color for unfilled segments (None=don't draw)
            clockwise: If True, draw clockwise from start to end angle (default False)
        """
        self.lcd = lcd
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.thickness = thickness
        self.segments = max(4, min(20, segments))  # Clamp to 4-20 range
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.gap_degrees = gap_degrees
        self.color = color
        self.background_color = background_color
        self.clockwise = clockwise
        self.value = 0

        # Pre-calculate segment angles for performance
        self.segment_angles = self._calculate_segment_angles()

    def _calculate_segment_angles(self):
        """
        Calculate start/end angles for each segment with gaps.

        Returns:
            List of tuples: [(start_angle, end_angle), ...]
        """
        if self.clockwise:
            # For clockwise: calculate arc going in decreasing angle direction
            total_arc = self.start_angle - self.end_angle
            # Handle wraparound (e.g., 45° to 315° clockwise = 90°, not -270°)
            if total_arc <= 0:
                total_arc += 360
        else:
            # For counter-clockwise: calculate arc going in increasing angle direction
            total_arc = self.end_angle - self.start_angle
            # Handle wraparound (e.g., 315° to 45° counter-clockwise = 90°, not -270°)
            if total_arc <= 0:
                total_arc += 360

        total_gaps = self.gap_degrees * self.segments
        usable_arc = total_arc - total_gaps
        segment_arc = usable_arc / self.segments

        segments = []
        current = self.start_angle

        for i in range(self.segments):
            if self.clockwise:
                segments.append((current, current - segment_arc))
                current -= segment_arc + self.gap_degrees
            else:
                segments.append((current, current + segment_arc))
                current += segment_arc + self.gap_degrees

        return segments

    def set_value(self, percentage):
        """
        Set gauge value as percentage.

        Args:
            percentage: Value from 0-100
        """
        self.value = max(0, min(100, percentage))

    def draw(self):
        """
        Draw the gauge to the LCD buffer.
        Call lcd.show() or lcd.Windows_show() afterward to display.
        """
        filled_count = int((self.value / 100.0) * self.segments)

        for i, (start_deg, end_deg) in enumerate(self.segment_angles):
            if i < filled_count:
                # Draw filled segment
                self._draw_thick_arc(start_deg, end_deg, self.color)
            elif self.background_color is not None:
                # Draw unfilled segment
                self._draw_thick_arc(start_deg, end_deg, self.background_color)

    def _draw_thick_arc(self, start_deg, end_deg, color):
        """
        Draw thick arc segment using parametric circle algorithm.

        Args:
            start_deg: Starting angle in degrees
            end_deg: Ending angle in degrees
            color: RGB565 color value
        """
        # Convert to radians
        start_rad = math.radians(start_deg)
        end_rad = math.radians(end_deg)

        # Determine direction based on start/end relationship
        drawing_clockwise = start_deg > end_deg

        # Draw from inner radius to outer radius for thickness
        for r in range(self.radius - self.thickness + 1, self.radius + 1):
            # Calculate step size (smaller for larger radii for smooth arcs)
            angle_step = 1.0 / r if r > 0 else 0.1

            angle = start_rad

            if drawing_clockwise:
                # Draw clockwise (decrement angle)
                while angle >= end_rad:
                    # Parametric circle equations
                    # Y uses negative sin because Y increases downward on display
                    # This makes: 0°=right, 90°=top, 180°=left, 270°=bottom
                    x = int(self.center_x + r * math.cos(angle))
                    y = int(self.center_y - r * math.sin(angle))

                    # Bounds check (display is 240x240)
                    if 0 <= x < 240 and 0 <= y < 240:
                        self.lcd.pixel(x, y, color)

                    angle -= angle_step
            else:
                # Draw counter-clockwise (increment angle)
                while angle <= end_rad:
                    # Parametric circle equations
                    # Y uses negative sin because Y increases downward on display
                    # This makes: 0°=right, 90°=top, 180°=left, 270°=bottom
                    x = int(self.center_x + r * math.cos(angle))
                    y = int(self.center_y - r * math.sin(angle))

                    # Bounds check (display is 240x240)
                    if 0 <= x < 240 and 0 <= y < 240:
                        self.lcd.pixel(x, y, color)

                    angle += angle_step

    def update(self, percentage):
        """
        Convenience method: set value and draw in one call.

        Args:
            percentage: Value from 0-100
        """
        self.set_value(percentage)
        self.draw()

    def draw_with_partial_refresh(self):
        """
        Draw gauge and refresh only the gauge area (more efficient).
        Calculates bounding box and uses Windows_show().
        """
        # Calculate bounding box with small padding
        x_min = max(0, self.center_x - self.radius - 5)
        x_max = min(239, self.center_x + self.radius + 5)
        y_min = max(0, self.center_y - self.radius - 5)
        y_max = min(239, self.center_y + self.radius + 5)

        self.draw()
        self.lcd.Windows_show(x_min, y_min, x_max, y_max)

    def draw_incremental(self, old_value):
        """
        Only redraw segments that changed (more efficient than full redraw).

        Args:
            old_value: Previous percentage value (0-100)
        """
        old_filled = int((old_value / 100.0) * self.segments)
        new_filled = int((self.value / 100.0) * self.segments)

        if new_filled > old_filled:
            # Fill additional segments
            for i in range(old_filled, new_filled):
                start_deg, end_deg = self.segment_angles[i]
                self._draw_thick_arc(start_deg, end_deg, self.color)
        elif new_filled < old_filled:
            # Unfill segments
            for i in range(new_filled, old_filled):
                start_deg, end_deg = self.segment_angles[i]
                if self.background_color is not None:
                    self._draw_thick_arc(start_deg, end_deg, self.background_color)
                # Note: If no background_color, we can't erase efficiently
                # In that case, full redraw is needed


def rgb_to_brg565(r, g, b):
    """
    Convert RGB888 (0-255 per channel) to BRG565 format for MicroPython framebuf.

    Note: The LCD_1inch28 driver uses BRG format instead of RGB.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        16-bit BRG565 color value

    Example:
        red_color = rgb_to_brg565(255, 0, 0)  # Returns red in BRG format
        green_color = rgb_to_brg565(0, 255, 0)  # Returns green in BRG format
    """
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
