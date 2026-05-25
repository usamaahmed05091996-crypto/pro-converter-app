import os
import pandas as pd
import pdfplumber
import pikepdf
from PIL import Image
from pdf2docx import Converter
from pypdf import PdfWriter, PdfReader
from moviepy import VideoFileClip
from typing import List

# --- CONVERSION FUNCTIONS ---

def convert_pdf_to_word(pdf_path: str, docx_path: str) -> None:
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise Exception(f"PDF to Word conversion failed: {e}")

def convert_pdf_to_excel(input_path, output_path):
    all_data = []
    
    # pdfplumber se table extract karna
    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            # 'strategy' argument ko hata dein, default settings best kaam karti hain
            table = page.extract_table()
            if table:
                all_data.extend(table)
    
    if not all_data:
        raise Exception("No table found in this PDF. It might be an image or scanned document.")
    
    # Data ko Excel mein save karna
    df = pd.DataFrame(all_data)
    # Pehli row ko header banana (agar zaroorat ho)
    df.to_excel(output_path, index=False, header=False)

# --- ADVANCED PDF TOOLS ---

def merge_pdfs(pdf_list: List[str], output_path: str) -> None:
    try:
        writer = PdfWriter()
        for pdf_path in pdf_list:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise Exception(f"PDF Merge failed: {e}")

def protect_pdf(input_path: str, output_path: str, password: str) -> None:
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.save(output_path, encryption=pikepdf.Encryption(owner=password, user=password, R=4))
    except Exception as e:
        raise Exception(f"PDF Protection failed: {e}")

def convert_image_to_pdf(image_path: str, output_pdf_path: str) -> None:
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_pdf_path, "PDF", resolution=100.0)
    except Exception as e:
        raise Exception(f"Image to PDF failed: {e}")

def convert_video_to_audio(video_path: str, audio_path: str) -> None:
    """Video file se sirf audio extract karne ke liye"""
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
    except Exception as e:
        raise Exception(f"Video to Audio failed: {e}")