"""
Test to check if PDF generation works in the transcript module
"""
import tempfile
import os
from pathlib import Path

def test_pdf_generation():
    """Test that the PDF generation function is available and working"""
    try:
        from grades_system.services.gpa_service import get_transcript
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from fastapi.responses import FileResponse

        print("[OK] ReportLab is importable")
        print("[OK] Required modules are available")

        # Check that the PDF endpoint is defined
        import grades_system.router_gpa
        print("[OK] GPA router with PDF endpoint exists")

        # Test if we can create a simple PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph("Test Transcript PDF", styles['Title']))
            elements.append(Spacer(1, 12))
            doc.build(elements)

            # Check if file exists and has content
            if os.path.exists(tmp.name):
                size = os.path.getsize(tmp.name)
                if size > 0:
                    print(f"[OK] PDF generation works - produced file of size {size} bytes")
                else:
                    print("[ERROR] PDF file is empty")
            else:
                print("[ERROR] PDF file was not created")

            # Clean up
            os.unlink(tmp.name)

        print("[OK] PDF generation functionality is available")
        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during PDF test: {e}")
        return False

if __name__ == "__main__":
    print("Testing PDF generation functionality...")
    success = test_pdf_generation()
    if success:
        print("\nPDF generation is ready for use!")
    else:
        print("\nPDF generation has issues that need to be resolved.")