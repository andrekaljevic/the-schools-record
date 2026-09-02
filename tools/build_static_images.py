"""Generate the responsive school artwork served from ``static/schools``.

Sources are the repository's own illustrations: the 1200px sketches in
``assets/school-sketches`` where they exist, and the 480px renditions in
``public/schools`` otherwise.  Transparency is composited onto white because the
card artwork sits on a solid ground and the hero artwork multiplies over paper.

    python tools/build_static_images.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKETCHES = ROOT / "assets" / "school-sketches"
SMALL = ROOT / "public" / "schools"
TARGET = ROOT / "static" / "schools"

SCHOOL_IDS = ("eton", "westminster", "winchester", "kcs", "st-pauls", "spgs", "wycombe")


def flatten(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    ground = Image.new("RGBA", image.size, (255, 255, 255, 255))
    return Image.alpha_composite(ground, image).convert("RGB")


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for school_id in SCHOOL_IDS:
        small = flatten(Image.open(SMALL / f"{school_id}-480.webp"))
        small.save(TARGET / f"{school_id}-480.webp", "WEBP", quality=86, method=3)
        sketch = SKETCHES / f"{school_id}.webp"
        if sketch.exists():
            large = flatten(Image.open(sketch))
            width, height = large.size
            large.save(TARGET / f"{school_id}-1200.webp", "WEBP", quality=72, method=3)
            large.resize((800, round(height * 800 / width)), Image.LANCZOS).save(
                TARGET / f"{school_id}-800.webp", "WEBP", quality=74, method=3
            )
        else:
            for width in (800, 1200):
                small.save(
                    TARGET / f"{school_id}-{width}.webp", "WEBP", quality=86, method=3
                )
        print(f"built {school_id}")


if __name__ == "__main__":
    main()
