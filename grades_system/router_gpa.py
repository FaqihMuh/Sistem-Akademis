from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import FileResponse
import os
from pathlib import Path

from pmb_system.database import get_db
from auth_system.dependencies import get_current_user
from auth_system.models import User, RoleEnum
from grades_system.services.gpa_service import calculate_ips, calculate_ipk, get_transcript
from grades_system.schemas import StudentGradeResponse

# Import for PDF generation with ReportLab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

router = APIRouter(prefix="/api/gpa", tags=["GPA"])


@router.get("/ips/{nim}/{semester}")
def get_ips(
    nim: str,
    semester: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate IPS for a student in a specific semester"""
    # Check if current user has access to view this student's data
    if current_user.role == RoleEnum.MAHASISWA:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya bisa melihat data sendiri"
            )
    elif current_user.role not in [RoleEnum.ADMIN, RoleEnum.DOSEN]:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki akses untuk melihat data ini"
            )
    
    ips = calculate_ips(db, nim, semester)
    return {"nim": nim, "semester": semester, "ips": ips}


@router.get("/ipk/{nim}")
def get_ipk(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate IPK for a student"""
    # Check if current user has access to view this student's data
    if current_user.role == RoleEnum.MAHASISWA:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya bisa melihat data sendiri"
            )
    elif current_user.role not in [RoleEnum.ADMIN, RoleEnum.DOSEN]:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki akses untuk melihat data ini"
            )
    
    ipk = calculate_ipk(db, nim)
    return {"nim": nim, "ipk": ipk}


@router.get("/transcript/{nim}")
def get_student_transcript(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get academic transcript for a student"""
    # Check if current user has access to view this student's data
    if current_user.role == RoleEnum.MAHASISWA:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya bisa melihat data sendiri"
            )
    elif current_user.role not in [RoleEnum.ADMIN, RoleEnum.DOSEN]:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki akses untuk melihat data ini"
            )
    
    transcript = get_transcript(db, nim)
    if not transcript.get("biodata"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data mahasiswa tidak ditemukan"
        )

    return transcript


@router.get("/transcript/{nim}/pdf")
def get_student_transcript_pdf(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate academic transcript as PDF using ReportLab"""
    # Check if current user has access to view this student's data
    if current_user.role == RoleEnum.MAHASISWA:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya bisa melihat data sendiri"
            )
    elif current_user.role not in [RoleEnum.ADMIN, RoleEnum.DOSEN]:
        if current_user.nim != nim:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak memiliki akses untuk melihat data ini"
            )

    # Get transcript data
    transcript = get_transcript(db, nim)
    if not transcript.get("biodata"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data mahasiswa tidak ditemukan"
        )

    # Define output directory and create if not exists
    output_dir = Path("generated_pdfs")
    output_dir.mkdir(exist_ok=True)

    # Create PDF file path
    pdf_path = output_dir / f"transkrip_{nim}.pdf"

    # Create PDF using ReportLab
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=50)
    elements = []

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Center alignment
        spaceAfter=12,
        spaceBefore=12,
    )

    # Add header with logo and title
    logo_path = Path("web_dashboard/static/logoistn.png")
    if logo_path.exists():
        logo = Image(str(logo_path), width=80, height=80)
        elements.append(logo)
        elements.append(Spacer(1, 12))

    # Title
    elements.append(Paragraph("TRANSKRIP AKADEMIK", title_style))

    # Horizontal line
    elements.append(Spacer(1, 12))
    # Create a line separator
    line = Table([['']], colWidths=500)
    line.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.black),
    ]))
    elements.append(line)

    # Biodata section
    elements.append(Spacer(1, 20))
    biodata_data = [
        ['NIM', ':', transcript['biodata']['nim']],
        ['Nama', ':', transcript['biodata']['nama']],
        ['Program Studi', ':', transcript['biodata']['program_studi']],
        ['Fakultas', ':', transcript['biodata']['fakultas']],
    ]

    biodata_table = Table(biodata_data, colWidths=[100, 20, 300])
    biodata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(biodata_table)

    # Add space before courses
    elements.append(Spacer(1, 20))

    # Courses per semester
    for semester_data in transcript['semester_list']:
        # Semester title
        semester_title = Paragraph(f"Semester {semester_data['semester']}", styles['Heading2'])
        elements.append(semester_title)

        # Course table
        # Define table headers
        course_data = [['Kode MK', 'Nama MK', 'SKS', 'Nilai Huruf', 'Mutu']]

        # Add course rows
        for course in semester_data['courses']:
            course_data.append([
                course['kode'],
                course['nama'],
                str(course['sks']),
                course['nilai_huruf'],
                f"{course['mutu']:.2f}"
            ])

        # Create table with style
        course_table = Table(course_data)
        course_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(course_table)
        elements.append(Spacer(1, 20))

    # Footer section - Total SKS, IPK, Predikat
    footer_data = [
        ['Total SKS', str(transcript['total_sks'])],
        ['IPK', f"{transcript['ipk']:.2f}"],
        ['Predikat', transcript['predikat']],
    ]

    footer_table = Table(footer_data, colWidths=[150, 200])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
    ]))
    elements.append(footer_table)

    # Signature area
    elements.append(Spacer(1, 30))

    # Signature table
    signature_data = [
        ['Dekan,', 'Jakarta, ____________ 20__'],
        ['', ''],
        ['______________________', ''],
        ['(Nama Dekan)', '']
    ]

    signature_table = Table(signature_data, colWidths=[200, 200])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    elements.append(signature_table)

    # Build PDF
    doc.build(elements)

    # Return the PDF file
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"transkrip_{nim}.pdf",
        headers={
            'Content-Disposition': f'attachment; filename="transkrip_{nim}.pdf"'
        }
    )