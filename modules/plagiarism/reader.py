# =============================================================================
# modules/plagiarism/reader.py  —  CareerVerse AI
# Extracts plain text from PDF, DOCX and TXT files.
# Used by both the Plagiarism Detector and (via modules/resume/reader.py
# which imports this) the Resume Analyzer + Interview Preparation modules.
# =============================================================================

import os


def extract_text(filepath: str) -> str:
    """
    Dispatch to the correct extractor based on file extension.
    Returns a plain-text string. Returns '' on any error so callers
    can decide how to handle an empty result.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.pdf':
        return _extract_pdf(filepath)
    elif ext == '.docx':
        return _extract_docx(filepath)
    elif ext == '.txt':
        return _extract_txt(filepath)
    else:
        return ''


# -----------------------------------------------------------------------------
# PDF  —  PyMuPDF (fitz)
# -----------------------------------------------------------------------------

def _extract_pdf(filepath: str) -> str:
    """
    Extract text from all pages of a PDF using PyMuPDF.
    Pages are joined with a newline so sentence segmentation
    in the plagiarism engine treats page boundaries correctly.
    """
    try:
        import fitz  # PyMuPDF
        doc   = fitz.open(filepath)
        pages = [page.get_text('text') for page in doc]
        doc.close()
        return '\n'.join(pages)
    except Exception as e:
        print(f"[reader] PDF extraction failed for {filepath}: {e}")
        return ''


# -----------------------------------------------------------------------------
# DOCX  —  python-docx
# -----------------------------------------------------------------------------

def _extract_docx(filepath: str) -> str:
    """
    Extract text from a DOCX file paragraph by paragraph.
    Tables are intentionally skipped — resumes and documents
    submitted for plagiarism checks typically carry their
    important content in body paragraphs.
    """
    try:
        from docx import Document
        doc        = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"[reader] DOCX extraction failed for {filepath}: {e}")
        return ''


# -----------------------------------------------------------------------------
# TXT  —  plain read
# -----------------------------------------------------------------------------

def _extract_txt(filepath: str) -> str:
    """
    Read a plain text file, trying UTF-8 first then falling back
    to latin-1 so accented characters in student submissions
    don't cause a crash.
    """
    for encoding in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[reader] TXT extraction failed for {filepath}: {e}")
            return ''
    return ''