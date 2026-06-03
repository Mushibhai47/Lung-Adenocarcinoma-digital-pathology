"""
extract_slide_mapping.py
========================
Extracts FICHA numbers from slide label images using OCR.
Run this on Vania's Mac where the .mrxs slides are stored.

Requirements (install once):
    pip install openslide-python pillow pytesseract
    brew install tesseract openslide   (on Mac)

Usage:
    python extract_slide_mapping.py /Volumes/Extreme\ SSD/Vania/slides/
    (or whatever folder contains the .mrxs files)
"""

import sys
import os
import re
import csv
import openslide
from PIL import Image
import pytesseract

def extract_label(slide_path):
    """Extract label image from .mrxs slide."""
    try:
        slide = openslide.OpenSlide(slide_path)
        if 'label' in slide.associated_images:
            label_img = slide.associated_images['label']
            slide.close()
            return label_img
        slide.close()
    except Exception as e:
        print(f"  ERROR opening {slide_path}: {e}")
    return None

def parse_ficha(ocr_text):
    """
    Parse OCR text to FICHA format.
    Label shows: '6607/15' or '6607|15' → H15-06607
    Also handles: '6607 15', '6607-15', '06607/2015'
    """
    # Clean up common OCR errors
    text = ocr_text.replace('|', '/').replace('\\', '/').replace(' ', '')
    text = re.sub(r'[^\w/]', '', text)

    # Pattern: NNNN/YY (case/year, 2-digit year)
    match = re.search(r'(\d{3,6})[/](\d{2})(?!\d)', text)
    if match:
        case_num = match.group(1).zfill(5)
        year = match.group(2)
        return f"H{year}-{case_num}"

    # Pattern: NNNN/YYYY (case/4-digit year)
    match = re.search(r'(\d{3,6})[/](\d{4})', text)
    if match:
        case_num = match.group(1).zfill(5)
        year = match.group(2)[-2:]
        return f"H{year}-{case_num}"

    # Pattern: NNNN YY (space separated)
    match = re.search(r'(\d{4,6})\s+(\d{2})$', ocr_text.strip())
    if match:
        case_num = match.group(1).zfill(5)
        year = match.group(2)
        return f"H{year}-{case_num}"

    return None

def get_slide_id(filename):
    """Extract R#-S# from filename like slide-2025-12-02T13-03-55-R1-S15.mrxs"""
    match = re.search(r'(R\d+-S\d+)', filename)
    return match.group(1) if match else filename

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_slide_mapping.py /path/to/slides/")
        print("Example: python extract_slide_mapping.py '/Volumes/Extreme SSD/Vania/slides/'")
        sys.exit(1)

    slides_dir = sys.argv[1]
    output_csv = os.path.join(os.path.dirname(slides_dir), 'slide_ficha_mapping.csv')

    mrxs_files = sorted([
        f for f in os.listdir(slides_dir) if f.endswith('.mrxs')
    ])

    print(f"Found {len(mrxs_files)} .mrxs files")
    print(f"Output: {output_csv}\n")

    results = []
    failed = []

    for fname in mrxs_files:
        slide_id = get_slide_id(fname)
        slide_path = os.path.join(slides_dir, fname)
        print(f"Processing {slide_id}...", end=' ')

        label = extract_label(slide_path)
        if label is None:
            print("NO LABEL")
            failed.append((slide_id, fname, '', 'no_label'))
            continue

        # OCR the label
        try:
            text = pytesseract.image_to_string(label, config='--psm 6')
            text_clean = text.strip().replace('\n', ' ')
            ficha = parse_ficha(text)

            if ficha:
                print(f"→ {ficha}  (raw: '{text_clean}')")
                results.append({'slide_id': slide_id, 'filename': fname, 'FICHA': ficha, 'ocr_raw': text_clean})
            else:
                print(f"PARSE FAILED  (raw: '{text_clean}')")
                failed.append((slide_id, fname, text_clean, 'parse_failed'))
        except Exception as e:
            print(f"OCR ERROR: {e}")
            failed.append((slide_id, fname, '', str(e)))

    # Save mapping
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['slide_id', 'FICHA', 'filename', 'ocr_raw'])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n=== DONE ===")
    print(f"Mapped: {len(results)} slides")
    print(f"Failed: {len(failed)} slides")
    print(f"Saved to: {output_csv}")

    if failed:
        print(f"\nFailed slides (check manually):")
        for slide_id, fname, raw, reason in failed:
            print(f"  {slide_id}: {reason} | raw='{raw}'")

if __name__ == '__main__':
    main()