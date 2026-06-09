import os
import pikepdf
import tabula
import pandas as pd
from PIL import Image
from pdf2docx import Converter
from pypdf import PdfWriter, PdfReader
from moviepy import VideoFileClip
from typing import List

# --- CONVERSION FUNCTIONS ---

def convert_pdf_to_word(pdf_path: str, docx_path: str) -> None:
    """Converts PDF to editable Word document."""
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise Exception(f"PDF to Word conversion failed: {str(e)}")

import pdfplumber
import pandas as pd
import re

def convert_pdf_to_excel(pdf_path, excel_path):
    csv_path = excel_path.replace(".xlsx", ".csv")
    tabula.convert_into(pdf_path, csv_path, output_format="csv", pages='all', stream=True)
    try:
        df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
    except Exception as e:
        df = pd.read_csv(csv_path, sep=None, engine='python', on_bad_lines='skip')
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    df.to_excel(excel_path, index=False)
    
    if os.path.exists(csv_path):
        os.remove(csv_path)

def merge_pdfs(pdf_list: List[str], output_path: str) -> None:
    """Merges multiple PDF files into one."""
    try:
        writer = PdfWriter()
        for pdf_path in pdf_list:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise Exception(f"PDF Merge failed: {str(e)}")

def protect_pdf(input_path: str, output_path: str, password: str) -> None:
    """Encrypts a PDF with a user-provided password."""
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.save(output_path, encryption=pikepdf.Encryption(owner=password, user=password, R=4))
    except Exception as e:
        raise Exception(f"PDF Protection failed: {str(e)}")

def convert_image_to_pdf(image_path: str, output_pdf_path: str) -> None:
    """Converts image (JPG/PNG) to PDF format."""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_pdf_path, "PDF", resolution=100.0)
    except Exception as e:
        raise Exception(f"Image to PDF failed: {str(e)}")

def convert_video_to_audio(video_path: str, audio_path: str) -> None:
    """Extracts audio from video files (mp4, mov, etc)."""
    clip = None
    try:
        clip = VideoFileClip(video_path)
        if clip.audio is None:
            raise ValueError("The provided video file does not contain an audio track.")
        clip.audio.write_audiofile(audio_path, logger=None) # logger=None cleans up console output
    except Exception as e:
        raise Exception(f"Video to Audio extraction failed: {str(e)}")
    finally:
        if clip:
            clip.close() # Ensure resources are released