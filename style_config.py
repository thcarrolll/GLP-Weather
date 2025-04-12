# style_config.py
import matplotlib.font_manager as fm
import os

TITLE_FONT = "Georgia"
FONT_PATH = ""
FALLBACK_FONTS = ['Comic Sans MS', 'Arial', 'serif']


# Use TITLE_FONT directly if no TTF path is provided
if FONT_PATH and os.path.exists(FONT_PATH):
    try:
        fm.fontManager.addfont(FONT_PATH)
        print(f"Loaded custom font: {TITLE_FONT}")
    except:
        print(f"Failed to load {TITLE_FONT}, falling back to {FALLBACK_FONTS[0]}")
        TITLE_FONT = FALLBACK_FONTS[0]
else:
    print(f"No TTF path or not found, using TITLE_FONT as system font: {TITLE_FONT}")

# Validate TITLE_FONT, fall back if needed
if TITLE_FONT not in fm.fontManager.get_font_names():
    print(f"{TITLE_FONT} not found in system fonts, falling back")
    TITLE_FONT = next((f for f in FALLBACK_FONTS if f in fm.fontManager.get_font_names()), "serif")


PALETTE = {
    'app_bg': '#FFFFFF',
    'main_bg': '#F5F5F5',
    'card_bg': '#b3cde0',
    'metric_bg': '#b3cde0',
    'plot_bg': '#b3cde0',
    'plot_line': '#3C8D88',
    'text': '#333333',
    'title': '#000000',
    'subtitle': '#000000',  # Default to title if not set
    'border': '#333333',
    'shading': '#D0D0D0',
    'shading_alpha': 0.3
}

print("Using font:", TITLE_FONT)
print("PALETTE loaded with app_bg:", PALETTE['app_bg'])
