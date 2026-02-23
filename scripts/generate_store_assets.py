from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path("marketing/store_assets")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        )
    candidates.extend(
        [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def canvas(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (239, 246, 255))
    d = ImageDraw.Draw(img)
    for y in range(h):
        c = 246 - int((y / max(1, h - 1)) * 22)
        d.line((0, y, w, y), fill=(232, c, 255))
    return img


def header(draw: ImageDraw.ImageDraw, title: str, subtitle: str, w: int) -> None:
    draw.text((44, 32), title, fill=(15, 23, 42), font=font(44, bold=True))
    draw.text((44, 92), subtitle, fill=(71, 85, 105), font=font(22))
    draw.line((44, 130, w - 44, 130), fill=(203, 213, 225), width=2)


def toggle(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, enabled: bool) -> None:
    draw.text((x, y + 2), label, fill=(30, 41, 59), font=font(22, bold=True))
    w = 90
    h = 44
    bx = x + 460
    by = y
    bg = (16, 185, 129) if enabled else (148, 163, 184)
    rounded(draw, (bx, by, bx + w, by + h), 22, bg)
    knob_x = bx + w - 38 if enabled else bx + 6
    rounded(draw, (knob_x, by + 6, knob_x + 32, by + 38), 16, (255, 255, 255))


def textbox(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, lines: list[str]) -> None:
    rounded(draw, (x, y, x + w, y + h), 12, (255, 255, 255))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, outline=(203, 213, 225), width=2)
    ty = y + 16
    for line in lines:
        draw.text((x + 16, ty), line, fill=(51, 65, 85), font=font(20))
        ty += 34


def badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color: tuple[int, int, int]) -> None:
    w = 18 + int(len(text) * 12.5)
    rounded(draw, (x, y, x + w, y + 38), 12, color)
    draw.text((x + 12, y + 8), text, fill=(255, 255, 255), font=font(18, bold=True))


def button(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, primary: bool = True) -> None:
    w = 170 + int(len(text) * 2)
    h = 48
    bg = (15, 118, 110) if primary else (255, 255, 255)
    fg = (255, 255, 255) if primary else (15, 118, 110)
    rounded(draw, (x, y, x + w, y + h), 10, bg)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=10, outline=(15, 118, 110), width=2)
    draw.text((x + 16, y + 13), text, fill=fg, font=font(18, bold=True))


def shot_popup() -> Image.Image:
    img = canvas(1280, 800)
    d = ImageDraw.Draw(img)
    header(d, "Popup controls", "Global and per-site safety toggles", 1280)

    rounded(d, (360, 170, 920, 720), 16, (248, 250, 252))
    d.rounded_rectangle((360, 170, 920, 720), radius=16, outline=(203, 213, 225), width=2)
    d.text((390, 200), "Submit Auto-Clicker", fill=(15, 23, 42), font=font(28, bold=True))
    badge(d, 390, 248, "ACTIVE (DRY-RUN)", (16, 185, 129))

    toggle(d, 390, 320, "Global Enabled", True)
    toggle(d, 390, 390, "Enabled For This Site", True)
    toggle(d, 390, 460, "Dry-Run Mode", True)

    d.text((390, 540), "Site: https://forms.example.com", fill=(71, 85, 105), font=font(20))
    d.text((390, 575), "Last action: 2026-02-23 15:57", fill=(71, 85, 105), font=font(20))
    button(d, 390, 630, "Open Options", primary=False)
    return img


def shot_options_allowlist() -> Image.Image:
    img = canvas(1280, 800)
    d = ImageDraw.Draw(img)
    header(d, "Options: URL allowlist", "Only listed URLs are eligible for automation", 1280)

    rounded(d, (80, 170, 1200, 740), 14, (255, 255, 255))
    d.rounded_rectangle((80, 170, 1200, 740), radius=14, outline=(203, 213, 225), width=2)
    d.text((110, 205), "Allowlist URL Patterns", fill=(15, 23, 42), font=font(30, bold=True))
    d.text((110, 250), "One pattern per line, wildcard supported.", fill=(71, 85, 105), font=font(20))

    textbox(
        d,
        110,
        290,
        1060,
        280,
        [
            "https://github.com/*",
            "https://*.example.com/forms/*",
            "http://localhost:3000/*",
            "https://portal.internal.company/*",
        ],
    )
    button(d, 110, 610, "Save", primary=True)
    button(d, 320, 610, "Reset Defaults", primary=False)
    badge(d, 520, 616, "Saved at 10:42:11", (100, 116, 139))
    return img


def shot_options_controls() -> Image.Image:
    img = canvas(1280, 800)
    d = ImageDraw.Draw(img)
    header(d, "Options: detection controls", "Tune labels, selector scope, and cooldown", 1280)

    rounded(d, (80, 170, 1200, 740), 14, (255, 255, 255))
    d.rounded_rectangle((80, 170, 1200, 740), radius=14, outline=(203, 213, 225), width=2)

    d.text((110, 205), "Button Text Patterns", fill=(15, 23, 42), font=font(26, bold=True))
    textbox(d, 110, 245, 520, 220, ["Submit", "Continue", "Apply", "Yes"])

    d.text((670, 205), "Container CSS selector", fill=(15, 23, 42), font=font(26, bold=True))
    textbox(d, 670, 245, 500, 70, ["form, [role='dialog'], .modal, main"])

    d.text((670, 340), "Cooldown (ms)", fill=(30, 41, 59), font=font(22, bold=True))
    textbox(d, 670, 375, 220, 70, ["5000"])

    d.text((930, 340), "Debounce (ms)", fill=(30, 41, 59), font=font(22, bold=True))
    textbox(d, 930, 375, 240, 70, ["250"])

    toggle(d, 110, 500, "Global Enabled", False)
    toggle(d, 110, 570, "Dry-Run Mode", True)

    button(d, 910, 660, "Save", primary=True)
    return img


def shot_overlay_active() -> Image.Image:
    img = canvas(1280, 800)
    d = ImageDraw.Draw(img)
    header(d, "Live page overlay", "Visible status while automation is active", 1280)

    rounded(d, (120, 190, 1160, 720), 14, (255, 255, 255))
    d.rounded_rectangle((120, 190, 1160, 720), radius=14, outline=(203, 213, 225), width=2)

    d.text((160, 230), "Checkout Confirmation", fill=(15, 23, 42), font=font(34, bold=True))
    d.text((160, 285), "Do you want to submit these changes?", fill=(51, 65, 85), font=font(24))

    button(d, 160, 355, "Submit", primary=True)
    button(d, 360, 355, "Cancel", primary=False)

    rounded(d, (820, 610, 1130, 700), 12, (5, 46, 22))
    d.rounded_rectangle((820, 610, 1130, 700), radius=12, outline=(21, 128, 61), width=2)
    d.text((840, 635), "Auto-click active (DRY-RUN)", fill=(220, 252, 231), font=font(18, bold=True))
    d.text((840, 663), "Last: 10:44:31", fill=(220, 252, 231), font=font(16))
    return img


def shot_blocked() -> Image.Image:
    img = canvas(1280, 800)
    d = ImageDraw.Draw(img)
    header(d, "Safety guard", "Automation blocked on non-allowlisted URL", 1280)

    rounded(d, (140, 210, 1140, 700), 14, (255, 255, 255))
    d.rounded_rectangle((140, 210, 1140, 700), radius=14, outline=(203, 213, 225), width=2)

    d.text((180, 250), "Current URL", fill=(15, 23, 42), font=font(26, bold=True))
    textbox(d, 180, 290, 920, 70, ["https://unknown-site.example/submit"])

    badge(d, 180, 390, "NOT ALLOWLISTED", (185, 28, 28))
    d.text(
        (180, 450),
        "No click is executed until this URL pattern is explicitly added in Options.",
        fill=(51, 65, 85),
        font=font(24),
    )
    button(d, 180, 545, "Open Options", primary=False)
    return img


def promo_small() -> Image.Image:
    img = canvas(440, 280)
    d = ImageDraw.Draw(img)
    rounded(d, (0, 0, 439, 279), 20, (15, 118, 110))
    d.text((24, 42), "Submit Auto-Clicker", fill=(255, 255, 255), font=font(34, bold=True))
    d.text((24, 104), "Allowlist-only automation", fill=(209, 250, 229), font=font(20))
    d.text((24, 136), "Dry-run by default", fill=(209, 250, 229), font=font(20))
    d.text((24, 168), "Visible active indicator", fill=(209, 250, 229), font=font(20))
    return img


def promo_marquee() -> Image.Image:
    img = canvas(1400, 560)
    d = ImageDraw.Draw(img)
    rounded(d, (0, 0, 1399, 559), 24, (15, 118, 110))
    d.text((58, 88), "Submit Auto-Clicker (Safe)", fill=(255, 255, 255), font=font(70, bold=True))
    d.text((58, 186), "VS Code + Chrome/Edge workflow automation with strict safety guards", fill=(209, 250, 229), font=font(30))
    d.text((58, 250), "Allowlists  |  Dry-run  |  Cooldowns  |  Per-site control", fill=(236, 253, 245), font=font(30, bold=True))
    return img


def save(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / name, format="PNG", optimize=True)


def main() -> int:
    save(shot_popup(), "screenshot-01-popup-controls-1280x800.png")
    save(shot_options_allowlist(), "screenshot-02-options-allowlist-1280x800.png")
    save(shot_options_controls(), "screenshot-03-options-controls-1280x800.png")
    save(shot_overlay_active(), "screenshot-04-overlay-active-1280x800.png")
    save(shot_blocked(), "screenshot-05-safety-blocked-1280x800.png")
    save(promo_small(), "small-promo-tile-440x280.png")
    save(promo_marquee(), "marquee-promo-tile-1400x560.png")
    print(f"Generated store assets in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

