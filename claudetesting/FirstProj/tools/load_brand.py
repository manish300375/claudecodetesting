"""Validate brand/ assets and print the normalized brand dict as JSON."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = ROOT / "brand"
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
REQUIRED_COLORS = ["primary", "secondary", "accent", "text", "background"]


def load_brand(brand_dir: Path = BRAND_DIR) -> dict:
    cfg_path = brand_dir / "brand.json"
    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path}")
    brand = json.loads(cfg_path.read_text())
    errors = []
    colors = brand.get("colors", {})
    for c in REQUIRED_COLORS:
        if not HEX.match(colors.get(c, "")):
            errors.append(f"colors.{c} must be a #RRGGBB hex value")
    logo = brand_dir / brand.get("logo", "")
    if not logo.is_file():
        errors.append(f"logo not found: {logo}")
    typo = brand.get("typography", {})
    for key in ("heading_file", "body_file"):
        if typo.get(key) and not (brand_dir / typo[key]).is_file():
            errors.append(f"font file not found: {brand_dir / typo[key]}")
    if errors:
        raise SystemExit("Brand validation failed:\n- " + "\n- ".join(errors))
    brand["logo_path"] = str(logo)
    light = brand.get("logo_light")  # optional reversed logo for dark backgrounds (cover)
    if light and not (brand_dir / light).is_file():
        raise SystemExit(f"Brand validation failed:\n- logo_light not found: {brand_dir / light}")
    brand["logo_light_path"] = str(brand_dir / light) if light else str(logo)
    bold = typo.get("body_bold_file")
    if bold and not (brand_dir / bold).is_file():
        raise SystemExit(f"Brand validation failed:\n- font file not found: {brand_dir / bold}")
    brand["body_bold_path"] = str(brand_dir / bold) if bold else None
    brand["heading_path"] = str(brand_dir / typo["heading_file"]) if typo.get("heading_file") else None
    brand["body_path"] = str(brand_dir / typo["body_file"]) if typo.get("body_file") else None
    return brand


if __name__ == "__main__":
    print(json.dumps(load_brand(), indent=2))
    sys.exit(0)
