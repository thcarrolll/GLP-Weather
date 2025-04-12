# gauges_test.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import math
import numpy as np
import streamlit as st
import io
import os
from weather_data import get_current_conditions, degrees_to_cardinal, get_wave_height
from gauge_config import TITLE_FONT, GAUGE_PALETTE, FALLBACK_FONTS

# Set page config
st.set_page_config(layout="wide", page_title="Gauge Test App")

# Initialize session state
if 'palette' not in st.session_state:
    st.session_state.palette = GAUGE_PALETTE.copy()
if 'font' not in st.session_state:
    st.session_state.font = TITLE_FONT
if 'prev_font' not in st.session_state:
    st.session_state.prev_font = TITLE_FONT

# Load custom font if available (e.g., Patrick Hand)
FONT_PATH = "path/to/PatrickHand.ttf"  # Adjust this to your TTF file location
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    fm.FontProperties(fname=FONT_PATH)

class CompassRoseGauge:
    def __init__(self, width=50, height=18.75, color_palette=None, font=None):
        self.palette = color_palette if color_palette else GAUGE_PALETTE
        self.font = font if font else TITLE_FONT
        self.fig = plt.figure(figsize=(width, height), facecolor=self.palette['figure_bg'])
        
        gauge_width = 1.78
        gap = 0.25
        left_margin = (width - (8 * gauge_width + 7 * gap)) / 2
        top_row_y = 0.35
        gauge_height = 2.5
        
        self.ax1 = self.fig.add_axes([left_margin / width, top_row_y, gauge_width / width, gauge_height / height])  # Wind Direction
        self.ax2 = self.fig.add_axes([(left_margin + gauge_width + gap) / width, top_row_y, gauge_width / width, gauge_height / height])  # Wind Speed
        self.ax3 = self.fig.add_axes([(left_margin + 2 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Temperature
        self.ax4 = self.fig.add_axes([(left_margin + 3 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Precipitation
        self.ax5 = self.fig.add_axes([(left_margin + 4 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Barometric Pressure
        self.ax6 = self.fig.add_axes([(left_margin + 5 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Humidity
        self.ax7 = self.fig.add_axes([(left_margin + 6 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Cloud Cover
        self.ax8 = self.fig.add_axes([(left_margin + 7 * (gauge_width + gap)) / width, top_row_y, gauge_width / width, gauge_height / height])  # Wave Height
        
        for ax in (self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6, self.ax7, self.ax8):
            ax.set_xlim(-1.215, 1.215)
            ax.set_ylim(-1.215, 1.215)
            ax.set_aspect('equal')
            ax.axis('off')
        
        self.fig.canvas.manager.set_window_title("Weather Dashboard Gauges - Test")

    def draw_compass_rose(self, wind_direction, wind_speed, wind_gusts, temperature, precip_24h, 
                          baro_pressure, humidity, cloud_cover, wave_height, baro_pressure_3h_ago=None):
        # Wind Direction (ax1)
        wind_dir_text = degrees_to_cardinal(wind_direction)
        self.ax1.clear()
        self.ax1.set_xlim(-1.215, 1.215)
        self.ax1.set_ylim(-1.215, 1.215)
        self.ax1.set_aspect('equal')
        self.ax1.axis('off')

        outer_circle = patches.Circle((0, 0), 1.215, edgecolor=self.palette['border'], facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax1.add_patch(outer_circle)
        inner_circle = patches.Circle((0, 0), 0.9, edgecolor=self.palette['border'], facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax1.add_patch(inner_circle)

        directions = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
        for label, angle in directions.items():
            rad = math.radians(-angle + 90)
            length = 1.035 if label in ["N", "E", "S", "W"] else 0.945
            inner_length = 1.08 if label in ["N", "E", "S", "W"] else 0.99
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = inner_length * 0.72 * math.cos(rad)
            y_inner = inner_length * 0.72 * math.sin(rad)
            self.ax1.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], linewidth=1.08)
            label_x = 1.125 * math.cos(rad) if label in ["N", "E", "S", "W"] else 1.035 * math.cos(rad)
            label_y = 1.125 * math.sin(rad) if label in ["N", "E", "S", "W"] else 1.035 * math.sin(rad)
            self.ax1.text(label_x, label_y, label, ha='center', va='center', 
                         fontsize=9 if label in ["N", "E", "S", "W"] else 7.2, family=self.font, 
                         color=self.palette['text'])

        for angle in range(0, 360, 15):
            if angle % 45 != 0:
                rad = math.radians(-angle + 90)
                x_outer = 1.08 * math.cos(rad)
                y_outer = 1.08 * math.sin(rad)
                x_inner = 1.035 * math.cos(rad)
                y_inner = 1.035 * math.sin(rad)
                self.ax1.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], linewidth=0.72)

        needle_length = 0.81
        rad = math.radians(90 - wind_direction)
        tip_x = needle_length * math.cos(rad)
        tip_y = needle_length * math.sin(rad)
        self.ax1.arrow(0, 0, tip_x, tip_y, color=self.palette['needle'], width=0.018, head_width=0.054, 
                      head_length=0.09, length_includes_head=True)

        center_circle = patches.Circle((0, 0), 0.27, edgecolor=self.palette['border'], facecolor=self.palette['gauge_bg'], 
                                     linewidth=1.5, alpha=0.9)
        self.ax1.add_patch(center_circle)
        self.ax1.text(0, 0, wind_dir_text, ha='center', va='center', fontsize=10.8, family=self.font, 
                     color=self.palette['needle'], zorder=10)
        self.ax1.text(0, -0.4, "Wind Direction", ha='center', va='center', fontsize=10, family=self.font, 
                     color=self.palette['border'])

        # Wind Speed (ax2)
        self.ax2.clear()
        self.ax2.set_xlim(-1.215, 1.215)
        self.ax2.set_ylim(-1.215, 1.215)
        self.ax2.set_aspect('equal')
        self.ax2.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax2.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax2.add_patch(inner_semi)

        max_speed = 100
        for speed in range(0, max_speed + 1, 10):
            angle = 180 - (speed / max_speed) * 180
            rad = math.radians(angle)
            length = 1.035 if speed % 20 == 0 else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax2.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if speed % 20 == 0 else 0.72)
            if speed % 20 == 0:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax2.text(label_x, label_y, str(speed), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        self.ax2.text(0, 0.36, f"{int(wind_speed)} MPH", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        self.ax2.text(0, 0.18, "Gusts", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['gust_needle'], zorder=10)

        speed_angle = 180 - (wind_speed / max_speed) * 180
        speed_rad = math.radians(speed_angle)
        speed_tip_x = 0.855 * math.cos(speed_rad)
        speed_tip_y = 0.855 * math.sin(speed_rad)
        self.ax2.arrow(0, 0, speed_tip_x, speed_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)

        gust_angle = 180 - (wind_gusts / max_speed) * 180
        gust_rad = math.radians(gust_angle)
        gust_tip_x = 0.765 * math.cos(gust_rad)
        gust_tip_y = 0.765 * math.sin(gust_rad)
        self.ax2.arrow(0, 0, gust_tip_x, gust_tip_y, color=self.palette['gust_needle'], width=0.0135, 
                      head_width=0.036, head_length=0.072, length_includes_head=True)
        self.ax2.text(0, -0.4, "Wind Speed", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Temperature (ax3)
        self.ax3.clear()
        self.ax3.set_xlim(-1.215, 1.215)
        self.ax3.set_ylim(-1.215, 1.215)
        self.ax3.set_aspect('equal')
        self.ax3.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax3.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax3.add_patch(inner_semi)

        min_temp, max_temp = -20, 120
        temp_range = max_temp - min_temp
        for temp in range(min_temp, max_temp + 1, 10):
            normalized_temp = (temp - min_temp) / temp_range
            angle = 180 - (normalized_temp * 180)
            rad = math.radians(angle)
            length = 1.035 if temp % 20 == 0 else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax3.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if temp % 20 == 0 else 0.72)
            if temp % 20 == 0:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax3.text(label_x, label_y, str(temp), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        self.ax3.text(0, 0.27, f"{int(temperature)}°F", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        temp_angle = 180 - ((temperature - min_temp) / temp_range) * 180
        temp_rad = math.radians(temp_angle)
        temp_tip_x = 0.81 * math.cos(temp_rad)
        temp_tip_y = 0.81 * math.sin(temp_rad)
        self.ax3.arrow(0, 0, temp_tip_x, temp_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)
        self.ax3.text(0, -0.4, "Temperature", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Precipitation (ax4)
        self.ax4.clear()
        self.ax4.set_xlim(-1.215, 1.215)
        self.ax4.set_ylim(-1.215, 1.215)
        self.ax4.set_aspect('equal')
        self.ax4.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax4.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax4.add_patch(inner_semi)

        min_precip, max_precip = 0, 15
        precip_range = max_precip - min_precip
        labeled_values = [0, 3, 6, 9, 12, 15]
        for precip in range(min_precip, max_precip + 1):
            normalized_precip = (precip - min_precip) / precip_range
            angle = 180 - (normalized_precip * 180)
            rad = math.radians(angle)
            length = 1.035 if precip in labeled_values else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax4.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if precip in labeled_values else 0.72)
            if precip in labeled_values:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax4.text(label_x, label_y, str(precip), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        self.ax4.text(0, 0.27, f"{precip_24h:.2f} in", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        precip_24h = min(max(precip_24h, min_precip), max_precip)
        precip_angle = 180 - ((precip_24h - min_precip) / precip_range) * 180
        precip_rad = math.radians(precip_angle)
        precip_tip_x = 0.81 * math.cos(precip_rad)
        precip_tip_y = 0.81 * math.sin(precip_rad)
        self.ax4.arrow(0, 0, precip_tip_x, precip_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)
        self.ax4.text(0, -0.4, "Precipitation 24 hrs.", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Barometric Pressure (ax5)
        self.ax5.clear()
        self.ax5.set_xlim(-1.215, 1.215)
        self.ax5.set_ylim(-1.215, 1.215)
        self.ax5.set_aspect('equal')
        self.ax5.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax5.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax5.add_patch(inner_semi)

        min_baro, max_baro = 28, 30.7
        change_baro = 30.0
        labeled_values = [28, 30, 30.7]
        tick_angles = np.linspace(180, 0, 9)
        for angle in tick_angles:
            rad = math.radians(angle)
            length = 1.035 if angle in [180, 90, 0] else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax5.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if angle in [180, 90, 0] else 0.72)

        for baro in labeled_values:
            if baro <= change_baro:
                normalized_baro = (baro - min_baro) / (change_baro - min_baro)
                angle = 180 - (normalized_baro * 90)
            else:
                normalized_baro = (baro - change_baro) / (max_baro - change_baro)
                angle = 90 - (normalized_baro * 90)
            rad = math.radians(angle)
            label_x = 1.125 * math.cos(rad)
            label_y = 1.125 * math.sin(rad)
            if baro == 30.7:
                label_x = 1.2 * math.cos(rad)
                label_y = 1.2 * math.sin(rad) - 0.1
            label = "Change" if baro == 30 else f"{baro:.1f}"
            self.ax5.text(label_x, label_y, label, ha='center', va='center', fontsize=7.2, 
                         family=self.font, color=self.palette['text'], zorder=10)

        radius = 1.0
        stormy_angles = np.linspace(165, 135, len("Stormy"))
        for i, char in enumerate("Stormy"):
            angle = stormy_angles[i]
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            rotation = angle - 90
            self.ax5.text(x, y, char, ha='center', va='center', fontsize=7.2, 
                         family=self.font, color=self.palette['text'], rotation=rotation, zorder=5)

        clear_angles = np.linspace(45, 15, len("Clear"))
        for i, char in enumerate("Clear"):
            angle = clear_angles[i]
            rad = math.radians(angle)
            x = radius * math.cos(rad)
            y = radius * math.sin(rad)
            rotation = angle - 90
            self.ax5.text(x, y, char, ha='center', va='center', fontsize=7.2, 
                         family=self.font, color=self.palette['text'], rotation=rotation, zorder=5)

        self.ax5.text(0, 0.27, f"{baro_pressure:.2f}", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        baro_pressure = min(max(baro_pressure, min_baro), max_baro)
        if baro_pressure <= change_baro:
            normalized_baro = (baro_pressure - min_baro) / (change_baro - min_baro)
            baro_angle = 180 - (normalized_baro * 90)
        else:
            normalized_baro = (baro_pressure - change_baro) / (max_baro - change_baro)
            baro_angle = 90 - (normalized_baro * 90)
        baro_angle = max(0, min(180, baro_angle))
        baro_rad = math.radians(baro_angle)
        baro_tip_x = 0.81 * math.cos(baro_rad)
        baro_tip_y = 0.81 * math.sin(baro_rad)
        self.ax5.arrow(0, 0, baro_tip_x, baro_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)

        if baro_pressure_3h_ago is not None:
            baro_pressure_3h_ago = min(max(baro_pressure_3h_ago, min_baro), max_baro)
            if baro_pressure_3h_ago <= change_baro:
                normalized_baro_3h = (baro_pressure_3h_ago - min_baro) / (change_baro - min_baro)
                baro_angle_3h = 180 - (normalized_baro_3h * 90)
            else:
                normalized_baro_3h = (baro_pressure_3h_ago - change_baro) / (max_baro - change_baro)
                baro_angle_3h = 90 - (normalized_baro_3h * 90)
            baro_angle_3h = max(0, min(180, baro_angle_3h))
            baro_rad_3h = math.radians(baro_angle_3h)
            baro_tip_x_3h = 0.72 * math.cos(baro_rad_3h)
            baro_tip_y_3h = 0.72 * math.sin(baro_rad_3h)
            self.ax5.arrow(0, 0, baro_tip_x_3h, baro_tip_y_3h, color=self.palette['baro_3h_needle'], 
                          width=0.0135, head_width=0.036, head_length=0.072, length_includes_head=True)

        self.ax5.text(0, -0.4, "Barometric Pressure", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Humidity (ax6)
        self.ax6.clear()
        self.ax6.set_xlim(-1.215, 1.215)
        self.ax6.set_ylim(-1.215, 1.215)
        self.ax6.set_aspect('equal')
        self.ax6.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax6.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax6.add_patch(inner_semi)

        min_humidity, max_humidity = 0, 100
        humidity_range = max_humidity - min_humidity
        for hum in range(0, max_humidity + 1, 10):
            normalized_hum = (hum - min_humidity) / humidity_range
            angle = 180 - (normalized_hum * 180)
            rad = math.radians(angle)
            length = 1.035 if hum % 20 == 0 else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax6.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if hum % 20 == 0 else 0.72)
            if hum % 20 == 0:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax6.text(label_x, label_y, str(hum), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        humidity_clamped = min(max(humidity, min_humidity), max_humidity)
        self.ax6.text(0, 0.27, f"{int(humidity_clamped)}%", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        hum_angle = 180 - ((humidity_clamped - min_humidity) / humidity_range) * 180
        hum_rad = math.radians(hum_angle)
        hum_tip_x = 0.81 * math.cos(hum_rad)
        hum_tip_y = 0.81 * math.sin(hum_rad)
        self.ax6.arrow(0, 0, hum_tip_x, hum_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)
        self.ax6.text(0, -0.4, "Humidity", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Cloud Cover (ax7)
        self.ax7.clear()
        self.ax7.set_xlim(-1.215, 1.215)
        self.ax7.set_ylim(-1.215, 1.215)
        self.ax7.set_aspect('equal')
        self.ax7.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax7.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax7.add_patch(inner_semi)

        min_cloud, max_cloud = 0, 100
        cloud_range = max_cloud - min_cloud
        for cloud in range(0, max_cloud + 1, 10):
            normalized_cloud = (cloud - min_cloud) / cloud_range
            angle = 180 - (normalized_cloud * 180)
            rad = math.radians(angle)
            length = 1.035 if cloud % 20 == 0 else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax7.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if cloud % 20 == 0 else 0.72)
            if cloud % 20 == 0:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax7.text(label_x, label_y, str(cloud), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        cloud_cover_clamped = min(max(cloud_cover, min_cloud), max_cloud)
        self.ax7.text(0, 0.27, f"{int(cloud_cover_clamped)}%", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        cloud_angle = 180 - ((cloud_cover_clamped - min_cloud) / cloud_range) * 180
        cloud_rad = math.radians(cloud_angle)
        cloud_tip_x = 0.81 * math.cos(cloud_rad)
        cloud_tip_y = 0.81 * math.sin(cloud_rad)
        self.ax7.arrow(0, 0, cloud_tip_x, cloud_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)
        self.ax7.text(0, -0.4, "Cloud Cover", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

        # Wave Height (ax8)
        self.ax8.clear()
        self.ax8.set_xlim(-1.215, 1.215)
        self.ax8.set_ylim(-1.215, 1.215)
        self.ax8.set_aspect('equal')
        self.ax8.axis('off')

        outer_semi = patches.Arc((0, 0), 2.43, 2.43, theta1=0, theta2=180, edgecolor=self.palette['border'], 
                                facecolor='none', linewidth=2.0, alpha=0.9)
        self.ax8.add_patch(outer_semi)
        inner_semi = patches.Wedge((0, 0), 0.9, 0, 180, edgecolor=self.palette['border'], 
                                  facecolor=self.palette['gauge_bg'], linewidth=1.5, alpha=0.9)
        self.ax8.add_patch(inner_semi)

        min_wave, max_wave = 0, 30
        wave_range = max_wave - min_wave
        labeled_values = [0, 5, 10, 15, 20, 25, 30]
        for wave in range(0, max_wave + 1, 5):
            normalized_wave = (wave - min_wave) / wave_range
            angle = 180 - (normalized_wave * 180)
            rad = math.radians(angle)
            length = 1.035 if wave in labeled_values else 0.945
            x_outer = length * math.cos(rad)
            y_outer = length * math.sin(rad)
            x_inner = (length - 0.09) * math.cos(rad)
            y_inner = (length - 0.09) * math.sin(rad)
            self.ax8.plot([x_inner, x_outer], [y_inner, y_outer], color=self.palette['border'], 
                         linewidth=1.08 if wave in labeled_values else 0.72)
            if wave in labeled_values:
                label_x = 1.125 * math.cos(rad)
                label_y = 1.125 * math.sin(rad)
                self.ax8.text(label_x, label_y, str(wave), ha='center', va='center', fontsize=7.2, 
                             family=self.font, color=self.palette['text'])

        self.ax8.text(0, 0.27, f"{wave_height:.1f} ft", ha='center', va='center', fontsize=10.8, 
                     family=self.font, color=self.palette['needle'], zorder=10)
        wave_height = min(max(wave_height, min_wave), max_wave)
        wave_angle = 180 - ((wave_height - min_wave) / wave_range) * 180
        wave_rad = math.radians(wave_angle)
        wave_tip_x = 0.81 * math.cos(wave_rad)
        wave_tip_y = 0.81 * math.sin(wave_rad)
        self.ax8.arrow(0, 0, wave_tip_x, wave_tip_y, color=self.palette['needle'], width=0.018, 
                      head_width=0.054, head_length=0.09, length_includes_head=True)
        self.ax8.text(0, -0.4, "Wave Height", ha='center', va='center', fontsize=10, 
                     family=self.font, color=self.palette['border'])

    def get_image(self):
        buf = io.BytesIO()
        self.fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        return buf

def update_gauge_config(font, palette):
    config_content = f"""# gauge_config.py
TITLE_FONT = "{font}"
FALLBACK_FONTS = {FALLBACK_FONTS}
GAUGE_PALETTE = {{
    'figure_bg': '{palette['figure_bg']}',
    'gauge_bg': '{palette['gauge_bg']}',
    'border': '{palette['border']}',
    'text': '{palette['text']}',
    'needle': '{palette['needle']}',
    'gust_needle': '{palette['gust_needle']}',
    'baro_3h_needle': '{palette['baro_3h_needle']}'
}}
"""
    config_path = "gauge_config.py"
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        st.success("Config saved!")
    except Exception as e:
        st.error(f"Failed to save config: {str(e)}")

def main():
    st.markdown("""
    <style>
    .gauge-container {
        width: 100%;
        text-align: center;
        overflow-x: auto;
        background-color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Gauge Style")
        common_fonts = [
            "Architects Daughter", "Patrick Hand", "Georgia", "Arial", "Times New Roman",
            "Verdana", "Helvetica", "Courier New", "Comic Sans MS", "Trebuchet MS", "serif", "sans-serif"
        ]
        selected_font = st.selectbox("Font", common_fonts, index=common_fonts.index(st.session_state.font) if st.session_state.font in common_fonts else 0)
        
        # Update font and trigger redraw if changed
        if selected_font != st.session_state.font:
            st.session_state.prev_font = st.session_state.font
            st.session_state.font = selected_font
            st.rerun()  # Replaced experimental_rerun with rerun

        st.session_state.palette["figure_bg"] = st.color_picker("Figure Background", st.session_state.palette["figure_bg"])
        st.session_state.palette["gauge_bg"] = st.color_picker("Gauge Background", st.session_state.palette["gauge_bg"])
        st.session_state.palette["border"] = st.color_picker("Border", st.session_state.palette["border"])
        st.session_state.palette["text"] = st.color_picker("Text", st.session_state.palette["text"])
        st.session_state.palette["needle"] = st.color_picker("Needle", st.session_state.palette["needle"])
        st.session_state.palette["gust_needle"] = st.color_picker("Gust Needle", st.session_state.palette["gust_needle"])
        st.session_state.palette["baro_3h_needle"] = st.color_picker("Baro 3h Needle", st.session_state.palette["baro_3h_needle"])

        if st.button("Save Config"):
            update_gauge_config(st.session_state.font, st.session_state.palette)

    # Load data
    conditions = get_current_conditions()
    wave_height, _ = get_wave_height()
    wind_direction = conditions["wind_direction"]
    wind_speed = conditions["wind_speed"]
    wind_gusts = conditions["wind_gust"] if isinstance(conditions["wind_gust"], (int, float)) else 0
    temperature = conditions["temperature"]
    precip_24h = conditions["precipitation_totals"]["24h"]
    baro_pressure = conditions.get("barometric_pressure", 30.0)
    humidity = conditions["humidity"]
    cloud_cover = conditions["cloud_cover"]
    baro_pressure_3h_ago = baro_pressure - 0.1

    # Validate font
    active_font = st.session_state.font
    available_fonts = set(fm.fontManager.get_font_names())
    if active_font not in available_fonts:
        st.warning(f"Font {active_font} not available, falling back to {TITLE_FONT}")
        active_font = TITLE_FONT

    # Draw gauges
    gauge = CompassRoseGauge(color_palette=st.session_state.palette, font=active_font)
    gauge.draw_compass_rose(wind_direction, wind_speed, wind_gusts, temperature, precip_24h, 
                            baro_pressure, humidity, cloud_cover, wave_height, baro_pressure_3h_ago)
    
    st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
    st.image(gauge.get_image(), width=2000)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()