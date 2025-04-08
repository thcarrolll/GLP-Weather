# compass_gauge.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

class CompassGauge:
    def __init__(self, width=2, height=2):
        # Create figure (size in inches, scaled like the clock)
        self.fig, self.ax = plt.subplots(figsize=(width, height), facecolor='#f8f1e9')  # Off-white background
        self.ax.set_xlim(-1.2, 1.2)
        self.ax.set_ylim(-1.2, 1.2)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

    def draw_compass(self, wind_direction=0, wind_speed=0):
        # Clear previous content
        self.ax.clear()
        self.ax.set_xlim(-1.2, 1.2)
        self.ax.set_ylim(-1.2, 1.2)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.set_facecolor('#f8f1e9')

        # Draw outer circle
        face = patches.Circle((0, 0), 1, edgecolor='black', facecolor='none', linewidth=2)
        self.ax.add_patch(face)

        # Draw cardinal directions (N, E, S, W as text)
        directions = {"N": 0, "E": 90, "S": 180, "W": 270}
        for label, angle in directions.items():
            rad = math.radians(angle)
            x = 1.05 * math.cos(rad)  # Slightly outside the circle
            y = 1.05 * math.sin(rad)
            self.ax.text(x, y, label, ha='center', va='center', fontsize=12, family='serif')

        # Draw needle (straight with a slight arrowhead)
        needle_length = 0.9  # Almost to the edge
        rad = math.radians(wind_direction - 90)  # Adjust for 0° at North, clockwise
        tip_x = needle_length * math.cos(rad)
        tip_y = needle_length * math.sin(rad)
        self.ax.plot([0, tip_x], [0, tip_y], color='black', linewidth=3)  # Main needle
        # Add small arrowhead
        arrow_size = 0.1
        angle_offset = math.pi / 6  # 30° for arrowhead wings
        wing1_x = tip_x - arrow_size * math.cos(rad + angle_offset)
        wing1_y = tip_y - arrow_size * math.sin(rad + angle_offset)
        wing2_x = tip_x - arrow_size * math.cos(rad - angle_offset)
        wing2_y = tip_y - arrow_size * math.sin(rad - angle_offset)
        self.ax.plot([tip_x, wing1_x], [tip_y, wing1_y], color='black', linewidth=1)
        self.ax.plot([tip_x, wing2_x], [tip_y, wing2_y], color='black', linewidth=1)
        # Center dot
        self.ax.plot(0, 0, 'o', color='black', markersize=6)

        # Draw wind speed (just the number)
        self.ax.text(0, 0, str(wind_speed), ha='center', va='center', fontsize=14, family='serif', color='black')

        # Refresh display (non-blocking for integration)
        plt.draw()

    def update(self, wind_direction, wind_speed):
        self.draw_compass(wind_direction, wind_speed)

    def show(self):
        plt.show()

# Test the compass standalone
if __name__ == "__main__":
    gauge = CompassGauge()
    gauge.draw_compass(wind_direction=45, wind_speed=12)  # Example: 45°, 12
    gauge.show()