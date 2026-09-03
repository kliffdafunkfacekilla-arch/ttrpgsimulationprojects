#!/usr/bin/env python3
"""Tile Image Cutter

Utility script to load a sprite sheet (or any large image) containing map tiles,
overlay a configurable grid, preview the result, and optionally slice the image
into individual tile files ready for use in the Ostraka map renderer.

Features:
- Supports PNG, JPG, BMP, etc.
- User specifies tile width and height (default 64x64).
- Visual preview using Pillow + Matplotlib.
- Saves sliced tiles to a target directory with sequential naming.
- No external GUI dependencies beyond Pillow and Matplotlib (both lightweight).

Usage example::
    python cut_tiles.py --input path\\to\\tilesheet.png \
                        --tile-width 64 --tile-height 64 \
                        --output-dir path\\to\\public\\textures

The script will create the output directory if it does not exist and write files
named ``tile_0_0.png`` (column_row)."""

import os
import argparse
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cut a sprite sheet into map tiles with a grid overlay.")
    parser.add_argument("--input", "-i", required=True, help="Path to the source image (sprite sheet).")
    parser.add_argument("--tile-width", "-w", type=int, default=64, help="Width of each tile in pixels.")
    parser.add_argument("--tile-height", "-h", type=int, default=64, help="Height of each tile in pixels.")
    parser.add_argument("--output-dir", "-o", required=True, help="Directory where sliced tiles will be saved.")
    parser.add_argument("--preview", action="store_true", help="Show a preview with grid overlay before cutting.")
    return parser.parse_args()

def load_image(path: str) -> Image.Image:
    img = Image.open(path)
    img = img.convert("RGBA")  # Ensure a consistent mode
    return img

def draw_grid(img: Image.Image, tile_size: Tuple[int, int]) -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    tile_w, tile_h = tile_size
    for x in range(0, w, tile_w):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 128), width=1)
    for y in range(0, h, tile_h):
        draw.line([(0, y), (w, y)], fill=(255, 0, 0, 128), width=1)
    return img

def preview_image(img: Image.Image):
    plt.figure(figsize=(8, 8))
    plt.imshow(img)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def slice_tiles(img: Image.Image, tile_size: Tuple[int, int], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    w, h = img.size
    tile_w, tile_h = tile_size
    cols = w // tile_w
    rows = h // tile_h
    for col in range(cols):
        for row in range(rows):
            left = col * tile_w
            upper = row * tile_h
            right = left + tile_w
            lower = upper + tile_h
            tile = img.crop((left, upper, right, lower))
            tile_name = f"tile_{col}_{row}.png"
            tile_path = os.path.join(output_dir, tile_name)
            tile.save(tile_path)
    print(f"Saved {cols * rows} tiles to '{output_dir}'.")

def main():
    args = parse_args()
    img = load_image(args.input)
    tile_size = (args.tile_width, args.tile_height)

    if args.preview:
        preview_img = img.copy()
        preview_img = draw_grid(preview_img, tile_size)
        preview_image(preview_img)
        answer = input("Proceed with slicing the image? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    slice_tiles(img, tile_size, args.output_dir)

if __name__ == "__main__":
    main()
