"""Save all 14 pages as images."""
import fitz, os

pdf_path = r"C:\Users\Owner\Desktop\MTSU_2026_Spring\NPDB Project\Medical_Liability_Decoded.pdf"
out_dir = r"C:\Users\Owner\Desktop\MTSU_2026_Spring\NPDB Project\mld_pages"
os.makedirs(out_dir, exist_ok=True)

doc = fitz.open(pdf_path)
for i in range(len(doc)):
    page = doc[i]
    pix = page.get_pixmap(dpi=200)
    img_path = os.path.join(out_dir, f"page_{i+1}.png")
    pix.save(img_path)
    print(f"Saved page {i+1}")
print("Done")
