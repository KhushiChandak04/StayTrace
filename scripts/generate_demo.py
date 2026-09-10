from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "demo"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int = 24):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_scene(path: Path, move_out: bool) -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (224, 228, 230))
    d = ImageDraw.Draw(img)
    # wall/floor
    d.rectangle((0, 0, w, 500), fill=(238, 235, 224))
    d.rectangle((0, 500, w, h), fill=(174, 151, 116))
    # window
    d.rectangle((80, 90, 330, 300), fill=(146, 198, 226), outline=(65, 75, 82), width=8)
    d.line((205, 90, 205, 300), fill=(65, 75, 82), width=6)
    d.line((80, 195, 330, 195), fill=(65, 75, 82), width=6)
    # desk
    desk_y = 460
    d.rectangle((690, desk_y - 105, 1080, desk_y), fill=(113, 78, 48), outline=(70, 50, 35), width=5)
    d.rectangle((720, desk_y, 755, 650), fill=(79, 55, 40))
    d.rectangle((1010, desk_y, 1045, 650), fill=(79, 55, 40))
    # chair
    d.rectangle((460, 410, 600, 450), fill=(71, 91, 103))
    d.rectangle((480, 280, 580, 420), fill=(71, 91, 103))
    d.rectangle((505, 450, 530, 610), fill=(60, 65, 70))
    # bed
    d.rectangle((350, 500, 690, 640), fill=(196, 196, 203), outline=(90, 90, 100), width=4)
    d.rectangle((350, 460, 690, 520), fill=(216, 218, 225), outline=(90, 90, 100), width=4)
    # cupboard
    d.rectangle((910, 70, 1170, 300), fill=(154, 121, 87), outline=(82, 62, 50), width=5)
    d.line((1040, 70, 1040, 300), fill=(82, 62, 50), width=4)
    # base labels
    d.text((45, 25), "STAYTRACE DEMO ROOM", fill=(30, 35, 40), font=font(30))
    d.text((45, 680), "MOVE-OUT" if move_out else "MOVE-IN", fill=(40, 45, 50), font=font(24))

    if move_out:
        # new wall damage
        d.arc((400, 110, 520, 250), 5, 175, fill=(110, 82, 68), width=7)
        d.line((460, 145, 470, 245), fill=(110, 82, 68), width=7)
        # desk scratch / marker
        d.line((805, 400, 965, 442), fill=(55, 45, 42), width=9)
        # missing chair: repaint area over chair location
        d.rectangle((430, 260, 620, 470), fill=(238, 235, 224))
        # moved object: book on bed
        d.rectangle((480, 500, 565, 560), fill=(55, 75, 105), outline=(30, 40, 50), width=3)
        # stain on bed
        d.ellipse((605, 530, 655, 580), fill=(148, 120, 105))
    img.save(path, quality=95)


draw_scene(OUT / "move_in_room.jpg", move_out=False)
draw_scene(OUT / "move_out_room.jpg", move_out=True)
print(f"Created {OUT / 'move_in_room.jpg'}")
print(f"Created {OUT / 'move_out_room.jpg'}")
