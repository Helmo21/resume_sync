"""
PDF Resume Generator
Creates professional ATS-friendly PDF resumes from JSON data
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from typing import Dict
import os
from datetime import datetime


def create_resume_pdf(resume_data: Dict, output_filename: str = None) -> str:
    """
    Generate a professional ATS-friendly PDF from resume JSON data.
    Returns the path to the generated PDF.
    """
    print("\n" + "="*80)
    print("STEP 4: GENERATE PDF RESUME")
    print("="*80)

    # Generate filename if not provided
    if not output_filename:
        name = resume_data.get('contact', {}).get('name', 'resume').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_resume_{timestamp}.pdf"

    print(f"\n⏳ Creating PDF: {output_filename}")

    try:
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Container for the 'Flowable' objects
        elements = []

        # Define styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#cccccc'),
            borderPadding=4,
            backColor=colors.HexColor('#f5f5f5')
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            leading=14
        )

        # ---- HEADER: Name and Contact Info ----
        contact = resume_data.get('contact', {})
        name = contact.get('name', 'Your Name')
        elements.append(Paragraph(name, title_style))

        # Contact line
        contact_parts = []
        if contact.get('email'):
            contact_parts.append(contact['email'])
        if contact.get('phone'):
            contact_parts.append(contact['phone'])
        if contact.get('location'):
            contact_parts.append(contact['location'])
        if contact.get('linkedin'):
            contact_parts.append(f"LinkedIn: {contact['linkedin']}")

        contact_line = " | ".join(contact_parts)
        elements.append(Paragraph(contact_line, contact_style))
        elements.append(Spacer(1, 0.1*inch))

        # ---- SUMMARY ----
        summary = resume_data.get('summary', '')
        if summary:
            elements.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
            elements.append(Paragraph(summary, body_style))
            elements.append(Spacer(1, 0.1*inch))

        # ---- EXPERIENCE ----
        experiences = resume_data.get('experience', [])
        if experiences:
            elements.append(Paragraph("PROFESSIONAL EXPERIENCE", heading_style))

            for exp in experiences:
                # Job title and company
                title_company = f"<b>{exp.get('title', 'Job Title')}</b> | {exp.get('company', 'Company')}"
                if exp.get('location'):
                    title_company += f" | {exp['location']}"
                elements.append(Paragraph(title_company, body_style))

                # Dates
                start = exp.get('start_date', '')
                end = exp.get('end_date', '')
                if start or end:
                    date_range = f"<i>{start} - {end}</i>"
                    elements.append(Paragraph(date_range, body_style))

                # Achievements/Description
                achievements = exp.get('achievements', [])
                if achievements:
                    for achievement in achievements:
                        bullet = f"• {achievement}"
                        elements.append(Paragraph(bullet, body_style))
                elif exp.get('description'):
                    # Fallback if no structured achievements
                    desc = exp.get('description', '')
                    elements.append(Paragraph(desc, body_style))

                elements.append(Spacer(1, 0.1*inch))

        # ---- EDUCATION ----
        education = resume_data.get('education', [])
        if education:
            elements.append(Paragraph("EDUCATION", heading_style))

            for edu in education:
                degree_school = f"<b>{edu.get('degree', 'Degree')}</b> | {edu.get('school', 'School')}"
                if edu.get('graduation_year'):
                    degree_school += f" | {edu['graduation_year']}"
                if edu.get('gpa'):
                    degree_school += f" | GPA: {edu['gpa']}"
                elements.append(Paragraph(degree_school, body_style))

            elements.append(Spacer(1, 0.1*inch))

        # ---- SKILLS ----
        skills = resume_data.get('skills', [])
        if skills:
            elements.append(Paragraph("SKILLS", heading_style))
            skills_text = ", ".join(skills)
            elements.append(Paragraph(skills_text, body_style))

        # Build PDF
        doc.build(elements)

        print(f"\n✓ PDF generated successfully: {output_filename}")
        print(f"   File size: {os.path.getsize(output_filename) / 1024:.1f} KB")

        return output_filename

    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        raise


if __name__ == "__main__":
    # Test with sample data
    print("Testing PDF Generator...")

    sample_resume = {
        "contact": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "(555) 123-4567",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/johndoe"
        },
        "summary": "Results-driven Software Engineer with 5+ years of experience building scalable web applications. Expertise in Python, React, and cloud infrastructure. Proven track record of delivering high-impact projects.",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "start_date": "01/2020",
                "end_date": "Present",
                "achievements": [
                    "Led development of microservices architecture serving 1M+ users, improving performance by 40%",
                    "Mentored team of 5 junior engineers, improving code quality and delivery speed",
                    "Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes"
                ]
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "location": "Remote",
                "start_date": "06/2018",
                "end_date": "12/2019",
                "achievements": [
                    "Built RESTful APIs using Python/Flask serving 100K+ daily requests",
                    "Developed React frontend components increasing user engagement by 25%",
                    "Optimized database queries reducing response time by 60%"
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of Technology",
                "graduation_year": "2018",
                "gpa": "3.8"
            }
        ],
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "AWS",
            "Docker", "PostgreSQL", "Redis", "Git", "Agile/Scrum"
        ]
    }

    pdf_path = create_resume_pdf(sample_resume, "test_resume.pdf")
    print(f"\n✓ Test PDF created: {pdf_path}")
