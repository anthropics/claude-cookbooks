"""Generate the fully synthetic ad creatives used by samples.jsonl.

Every image is composed programmatically (Pillow), so the ground-truth labels in
samples.jsonl are correct by construction — we placed the disclaimer strip, the age
badge, the before/after panels ourselves. All brands are fictional.

Run:  python build_creatives.py     (writes PNGs into ./images/)
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).parent / "images"
OUT.mkdir(exist_ok=True)
W = H = 1080


def font(size: int, bold: bool = True):
    for path, idx in [
        ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0),
    ]:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except OSError:
            continue
    return ImageFont.load_default()


def strip(d, text, bg="#1E2630", fg="#9AA4AE"):
    """Bottom small-print strip — the classic disclaimer placement."""
    d.rectangle([0, 1010, W, H], fill=bg)
    d.text((70, 1028), text, font=font(28, bold=False), fill=fg)


def badge(d, text, x=880, y=60):
    d.rectangle([x, y, x + 130, y + 90], outline="#E8E4D8", width=5)
    d.text((x + 22, y + 18), text, font=font(50), fill="#E8E4D8")


def northpeak_trail():
    """Clean sneaker ad: low text, brand visible, nothing restricted."""
    img = Image.new("RGB", (W, H), "#2E4A3A")
    d = ImageDraw.Draw(img)
    d.polygon(
        [(0, 800), (300, 500), (560, 700), (820, 420), (1080, 640), (1080, 1080), (0, 1080)],
        fill="#22382C",
    )
    d.ellipse([340, 620, 740, 820], fill="#4A5A50")  # rock
    # the shoe
    d.rounded_rectangle([400, 520, 700, 640], 40, fill="#D7DBD2")
    d.rounded_rectangle([390, 610, 720, 660], 20, fill="#B3261E")
    d.arc([420, 500, 650, 640], 180, 360, fill="#3B3F44", width=14)
    d.text((70, 90), "Run further", font=font(76), fill="#F0EEE6")
    d.text((70, 185), "this fall", font=font(76), fill="#F0EEE6")
    d.text((70, 980 - 60), "NORTHPEAK", font=font(44), fill="#F0EEE6")
    img.save(OUT / "northpeak_trail.png")


def betpeak_bonus():
    """Sportsbook: $1,500 bonus figure, 21+ badge, generic responsible-gambling strip
    (deliberately NO 1-800-GAMBLER — the NJ rule should catch it)."""
    img = Image.new("RGB", (W, H), "#101820")
    d = ImageDraw.Draw(img)
    for x, y, r, c in [
        (180, 760, 110, "#C43A20"),
        (320, 830, 95, "#1B6B4A"),
        (120, 930, 80, "#B8860B"),
        (420, 960, 70, "#3B3F8C"),
    ]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline="#E8E4D8", width=6)
        d.ellipse([x - r + 18, y - r + 18, x + r - 18, y + r - 18], outline="#E8E4D8", width=3)
    d.text((70, 130), "GET UP TO", font=font(64), fill="#E8E4D8")
    d.text((70, 210), "$1,500", font=font(170), fill="#F0A500")
    d.text((70, 400), "IN BONUS BETS", font=font(72), fill="#E8E4D8")
    d.text((70, 520), "BETPEAK", font=font(48), fill="#5AA0E0")
    badge(d, "21+")
    strip(d, "Gamble Responsibly.")
    img.save(OUT / "betpeak_bonus.png")


def peaklend_rate():
    """Finance: big promotional rate, no APR small print anywhere."""
    img = Image.new("RGB", (W, H), "#123B2E")
    d = ImageDraw.Draw(img)
    for i in range(6):
        d.arc(
            [600 - i * 60, 300 - i * 60, 1400 + i * 60, 1100 + i * 60],
            180,
            300,
            fill="#1B5240",
            width=8,
        )
    d.text((70, 140), "Personal loans", font=font(66), fill="#EAF2ED")
    d.text((70, 250), "from", font=font(66), fill="#EAF2ED")
    d.text((70, 340), "3.9%", font=font(220), fill="#8FE3B0")
    d.text((70, 620), "Decision in minutes.", font=font(52, bold=False), fill="#C9DCD1")
    d.text((70, 950), "PEAKLEND", font=font(44), fill="#EAF2ED")
    img.save(OUT / "peaklend_rate.png")


def luma_before_after():
    """Skincare: side-by-side before/after skin panels with DAY labels — prohibited
    imagery in every category under clause 1.4."""
    img = Image.new("RGB", (W, H), "#F3EDE7")
    d = ImageDraw.Draw(img)
    d.text((70, 70), "Visibly clearer skin", font=font(64), fill="#3A322C")
    d.text((70, 150), "in 14 days", font=font(64), fill="#3A322C")
    # before panel: blotchy skin swatch
    d.rectangle([70, 300, 510, 860], fill="#D9A98F", outline="#3A322C", width=3)
    for x, y, r in [(160, 420, 26), (300, 520, 34), (220, 660, 22), (400, 430, 18), (360, 740, 28)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill="#B96A55")
    d.rectangle([70, 300, 510, 360], fill="#3A322C")
    d.text((90, 310), "DAY 1", font=font(38), fill="#F3EDE7")
    # after panel: clear swatch
    d.rectangle([570, 300, 1010, 860], fill="#E7C3AC", outline="#3A322C", width=3)
    d.rectangle([570, 300, 1010, 360], fill="#3A322C")
    d.text((590, 310), "DAY 14", font=font(38), fill="#F3EDE7")
    d.text((70, 920), "LUMA SKIN", font=font(44), fill="#3A322C")
    img.save(OUT / "luma_before_after.png")


def vinepeak_wine():
    """Alcohol done right: responsible-drinking strip, 21+ badge, no people."""
    img = Image.new("RGB", (W, H), "#2A1E2B")
    d = ImageDraw.Draw(img)
    # bottle
    d.rounded_rectangle([470, 300, 610, 860], 40, fill="#3E2233")
    d.rectangle([515, 180, 565, 320], fill="#3E2233")
    d.rectangle([515, 150, 565, 200], fill="#7A4A28")
    d.rectangle([485, 480, 595, 700], fill="#EDE4D4")
    d.text((500, 520), "VINE\nPEAK", font=font(40), fill="#3E2233")
    # glass
    d.polygon([(760, 420), (900, 420), (830, 560)], fill="#5C2E44")
    d.line([830, 560, 830, 680], fill="#EDE4D4", width=8)
    d.line([770, 690, 890, 690], fill="#EDE4D4", width=8)
    d.text((70, 120), "Sunday,", font=font(84), fill="#EDE4D4")
    d.text((70, 230), "slowly.", font=font(84), fill="#EDE4D4")
    badge(d, "21+")
    strip(d, "Please Drink Responsibly.", bg="#1C141D")
    img.save(OUT / "vinepeak_wine.png")


if __name__ == "__main__":
    for fn in [northpeak_trail, betpeak_bonus, peaklend_rate, luma_before_after, vinepeak_wine]:
        fn()
        print("wrote", fn.__name__)
    print("done →", OUT)
