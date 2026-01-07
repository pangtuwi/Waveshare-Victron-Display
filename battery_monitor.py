"""
Battery Monitor Display Mode
Shows Victron battery SOC with circular gauge overlay
Based on jtj.py template from HA-Waveshare-Display repository

NOTE: This file is intended for the Waveshare RP2350B display, not the Pico W.
Copy this file to your HA-Waveshare-Display repository.
"""

from LCD_1inch28 import LCD_1inch28
from circular_gauge import CircularGauge, rgb_to_brg565
from image_display import display_image_with_overlays
from image_data import get_image
import time

class BatteryMonitor:
    """Battery SOC visualization using circular gauge"""

    # Display configuration (matching jtj.py)
    GAUGE_CENTER_X = 120
    GAUGE_CENTER_Y = 120
    GAUGE_RADIUS = 115
    GAUGE_THICKNESS = 10
    GAUGE_SEGMENTS = 20
    GAUGE_START_ANGLE = 215
    GAUGE_END_ANGLE = 320
    GAUGE_GAP = 2
    GAUGE_COLOR = 0xFFFF  # White
    GAUGE_BG_COLOR = 0xE67AE6  # Magenta (RGB 230, 135, 230 converted to BRG565)

    # Staleness threshold (3x poll interval = 15 seconds)
    STALENESS_TIMEOUT_MS = 15000

    def __init__(self, lcd, image_index=0):
        """
        Initialize battery monitor display

        Args:
            lcd: LCD_1inch28 display instance
            image_index: Which background image to use (default 0)
        """
        self.lcd = lcd
        self.current_soc = None
        self.last_update_ms = None

        # Create circular gauge with exact jtj.py configuration
        self.gauge = CircularGauge(
            lcd=lcd,
            center_x=self.GAUGE_CENTER_X,
            center_y=self.GAUGE_CENTER_Y,
            radius=self.GAUGE_RADIUS,
            thickness=self.GAUGE_THICKNESS,
            segments=self.GAUGE_SEGMENTS,
            start_angle=self.GAUGE_START_ANGLE,
            end_angle=self.GAUGE_END_ANGLE,
            gap_degrees=self.GAUGE_GAP,
            color=self.GAUGE_COLOR,
            background_color=self.GAUGE_BG_COLOR,
            clockwise=True
        )

        # Load background image
        try:
            from image_data import get_image_names
            img_names = get_image_names()
            if img_names and len(img_names) > image_index:
                img_name = img_names[image_index]
                self.image_data = get_image(img_name)
                print(f"Battery monitor: Loaded image '{img_name}'")
            else:
                print(f"Warning: No image at index {image_index}")
                self.image_data = None
        except Exception as e:
            print(f"Warning: Failed to load image {image_index}: {e}")
            self.image_data = None

    def update_soc(self, soc_percentage):
        """
        Update displayed battery SOC

        Args:
            soc_percentage: Battery SOC 0-100

        Returns:
            True if updated successfully, False otherwise
        """
        # Validate input
        if soc_percentage is None:
            print("Battery monitor: Cannot update with None value")
            return False

        if not isinstance(soc_percentage, (int, float)):
            print(f"Battery monitor: Invalid type {type(soc_percentage)}")
            return False

        if not (0 <= soc_percentage <= 100):
            print(f"Battery monitor: SOC out of range: {soc_percentage}")
            return False

        # Update state
        self.current_soc = int(soc_percentage)
        self.last_update_ms = time.ticks_ms()

        # Render to display
        self.render()

        return True

    def render(self):
        """Render image + gauge to display"""
        # Use default if no data yet
        soc = self.current_soc if self.current_soc is not None else 0

        # Render image with gauge overlay
        if self.image_data:
            display_image_with_overlays(
                lcd=self.lcd,
                image_data=self.image_data,
                gauge_items=[(self.gauge, soc)]
            )
        else:
            # Fallback: just draw gauge on black background
            self.lcd.fill(0x0000)  # Black
            self.gauge.draw_full(soc)
            self.lcd.show()

    def is_stale(self, timeout_ms=None):
        """
        Check if data is stale (no updates for timeout period)

        Args:
            timeout_ms: Staleness threshold (default from class constant)

        Returns:
            True if data is stale or never received
        """
        if timeout_ms is None:
            timeout_ms = self.STALENESS_TIMEOUT_MS

        if self.last_update_ms is None:
            return True

        elapsed = time.ticks_diff(time.ticks_ms(), self.last_update_ms)
        return elapsed > timeout_ms

    def get_status(self):
        """
        Get current monitor status

        Returns:
            Dictionary with current state
        """
        age_ms = None
        if self.last_update_ms is not None:
            age_ms = time.ticks_diff(time.ticks_ms(), self.last_update_ms)

        return {
            'soc': self.current_soc,
            'last_update_ms': self.last_update_ms,
            'is_stale': self.is_stale(),
            'age_ms': age_ms
        }
