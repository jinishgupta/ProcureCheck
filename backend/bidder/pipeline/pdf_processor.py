import fitz
import os
import shutil

class DocumentProcessor:
    def __init__(self, file_path, output_dir):
        self.file_path = file_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.doc = None
        self.is_image = False
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg']:
            self.is_image = True
            self.total_pages = 1
        else:
            if ext == '.docx':
                pdf_path = os.path.join(self.output_dir, "temp_converted.pdf")
                if not os.path.exists(pdf_path):
                    try:
                        from docx2pdf import convert
                        convert(file_path, pdf_path)
                    except Exception as e:
                        print(f"Warning: docx2pdf failed: {e}. Ensure MS Word is available.")
                        raise e
                self.file_path = pdf_path
            
            self.doc = fitz.open(self.file_path)
            self.total_pages = len(self.doc)
            
    def get_page_content(self, page_num):
        """
        Returns (content_type, content)
        content_type is "text" (native digital PDF) or "image" (scanned page)
        """
        if self.is_image:
            if page_num != 0:
                raise ValueError("Image only has page 0")
            dest = os.path.join(self.output_dir, f"page_0{os.path.splitext(self.file_path)[1]}")
            shutil.copy(self.file_path, dest)
            return ("image", dest)
            
        if page_num < 0 or page_num >= self.total_pages:
            raise ValueError(f"Page {page_num} out of bounds")
            
        page = self.doc[page_num]
        native_text = page.get_text().strip()
        
        # Routing logic: If sufficient text is extracted directly, it's digital.
        if len(native_text) > 50:
            return ("text", native_text)
            
        # Fallback to OCR (scanned page)
        path = os.path.join(self.output_dir, f"page_{page_num}.png")
        if not os.path.exists(path):
            pix = page.get_pixmap(dpi=300)
            pix.save(path)
        return ("image", path)