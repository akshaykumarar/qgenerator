"""Packaging SKU Catalog and 5-Vendor Multi-Format Document Generator (Root Entry)."""
from src.generator.packaging_generator import (
    DEFAULT_PACKAGING_SKUS,
    apply_user_feedback,
    generate_vendor_dataset,
    generate_vendor1_excel,
    generate_vendor2_pdf,
    generate_vendor3_docx,
    generate_vendor4_angled_photo,
    generate_vendor5_email,
)

if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(f"Generating 5-vendor packaging dataset (Prompt: '{prompt}')...")
    files = generate_vendor_dataset(target_dir="./vendor_dataset", feedback_prompt=prompt)
    print(f"Generated {len(files)} vendor proposal artifacts in ./vendor_dataset:")
    for f in files:
        print(f" - {f}")