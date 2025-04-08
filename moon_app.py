from datetime import date, datetime
import ephem
from PIL import Image, ImageDraw

def get_moon_phase(date_obj):
    new_moon = ephem.previous_new_moon(date_obj)  # Find last New Moon
    moon = ephem.Moon()
    moon.compute(date_obj)
    days_since = (date_obj - ephem.localtime(new_moon).date()).days
    lunar_cycle = 29.530588
    phase_fraction = (days_since % lunar_cycle) / lunar_cycle
    phases = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ]
    if phase_fraction < 0.02 or phase_fraction >= 0.98:
        return 0, phases[0]
    elif 0.02 <= phase_fraction < 0.23:
        return 1, phases[1]
    elif 0.23 <= phase_fraction < 0.27:
        return 2, phases[2]
    elif 0.27 <= phase_fraction < 0.48:
        return 3, phases[3]
    elif 0.48 <= phase_fraction < 0.52:
        return 4, phases[4]
    elif 0.52 <= phase_fraction < 0.73:
        return 5, phases[5]
    elif 0.73 <= phase_fraction < 0.77:
        return 6, phases[6]
    elif 0.77 <= phase_fraction < 0.98:
        return 7, phases[7]

def get_next_full_moon():
    today = date.today()
    observer = ephem.Observer()
    observer.date = today
    next_full = ephem.next_full_moon(today)
    next_full_date = ephem.localtime(next_full).date()
    return next_full_date.strftime('%a, %b %d, %Y')

def get_moon_plot():
    today = date.today()
    phase_index, current_phase = get_moon_phase(today)
    next_full_moon = get_next_full_moon()
    img = Image.new("RGB", (400, 100), "black")
    draw = ImageDraw.Draw(img)
    phases = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ]

    for i, phase in enumerate(phases):
        x_offset = i * 50 + 5
        draw.ellipse((x_offset, 25, x_offset + 40, 65), fill="white")
        if i == 1:  # Waxing Crescent
            draw.ellipse((x_offset + 15, 25, x_offset + 40, 65), fill="black")
        elif i == 2:  # First Quarter
            draw.rectangle((x_offset + 20, 25, x_offset + 40, 65), fill="black")
        elif i == 3:  # Waxing Gibbous
            draw.ellipse((x_offset, 25, x_offset + 25, 65), fill="black")
        elif i == 5:  # Waning Gibbous
            draw.ellipse((x_offset + 15, 25, x_offset + 40, 65), fill="black")
        elif i == 6:  # Last Quarter
            draw.rectangle((x_offset, 25, x_offset + 20, 65), fill="black")
        elif i == 7:  # Waning Crescent
            draw.ellipse((x_offset, 25, x_offset + 25, 65), fill="black")
        if i == phase_index:
            draw.rectangle((x_offset - 3, 22, x_offset + 43, 68), outline="red", width=2)
    
    phase_info = f"Current Phase: {current_phase}\nNext Full Moon: {next_full_moon}"
    return img, phase_info

if __name__ == "__main__":
    img, text = get_moon_plot()
    img.show()
    print(text)