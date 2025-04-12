from PIL import Image
import os

icon_dir = "C:/Users/teren/Tides/icons/"
gif_files = [
    "small_craft.gif",
    "gale.gif",
    "storm.gif",
    "hurricane.gif"
]

for gif_file in gif_files:
    gif_path = os.path.join(icon_dir, gif_file)
    if os.path.exists(gif_path):
        try:
            img = Image.open(gif_path)
            # Take first frame for static PNG
            img = img.convert("RGBA")
            png_file = gif_file.replace(".gif", ".png")
            png_path = os.path.join(icon_dir, png_file)
            img.save(png_path, "PNG")
            print(f"Converted {gif_file} to {png_file}")
        except Exception as e:
            print(f"Failed to convert {gif_file}: {e}")
    else:
        print(f"{gif_file} not found")