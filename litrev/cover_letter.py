import os
import subprocess
from datetime import datetime
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def set_font(run, font_name="Times New Roman", size_pt=11, bold=False, italic=False, color_rgb=None):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = RGBColor(*color_rgb)

def generate_cover_letter(job) -> str:
    """Generates a professional 1-page tailored Cover Letter (.docx + .pdf) in Vishant's voice."""
    doc = docx.Document()
    
    # 0.75 inch margins for clean 1-page layout
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # ── Header ──
    p_head = doc.add_paragraph()
    p_head.paragraph_format.space_after = Pt(2)
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_name = p_head.add_run("Vishant Gandhi\n")
    set_font(r_name, "Times New Roman", 15, bold=True)
    r_sub = p_head.add_run("San Diego, CA | (925) 660-2862 | vishant@gandhi.phd | www.gandhi.phd")
    set_font(r_sub, "Times New Roman", 9.5, italic=True)

    # Divider line
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(12)
    r_div = p_div.add_run("―" * 60)
    set_font(r_div, "Times New Roman", 8, color_rgb=(140, 140, 140))
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ── Date & Recipient ──
    p_date = doc.add_paragraph()
    p_date.paragraph_format.space_after = Pt(8)
    r_date = p_date.add_run(datetime.now().strftime("%B %d, %Y") + "\n")
    set_font(r_date, "Times New Roman", 11)
    r_rec = p_date.add_run(f"Hiring Team | {job.company}\n{job.location}")
    set_font(r_rec, "Times New Roman", 11, bold=True)

    # ── Salutation ──
    p_sal = doc.add_paragraph()
    p_sal.paragraph_format.space_after = Pt(8)
    r_sal = p_sal.add_run(f"Dear {job.company} Hiring Team,")
    set_font(r_sal, "Times New Roman", 11)

    is_vc = (job.job_type == "Venture") or any(k in job.title.lower() for k in ["venture", "invest", "equity", "capital", "analyst", "associate"])

    if is_vc:
        # ── Venture Capital / Investing Narrative ──
        p1 = doc.add_paragraph()
        p1.paragraph_format.space_after = Pt(8)
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(
            f"I am writing to express my enthusiastic interest in the {job.title} opportunity at {job.company}. "
            f"As a Bioengineering Ph.D. candidate at UC San Diego with active experience conducting technical due diligence "
            f"at Aquillius Ventures and leading strategic partnerships at Nucleate, I have dedicated my career to bridging the gap "
            f"between bench-scale scientific breakthrough and scalable commercial value. {job.company}'s leadership in life science "
            f"innovation makes this role the ideal vehicle for my dual identity as a scientist-strategist."
        )
        set_font(r1, "Times New Roman", 10.5)

        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(8)
        p2.paragraph_format.line_spacing = 1.15
        r2 = p2.add_run(
            "My experience has rigorously prepared me to evaluate early-stage technologies and support thesis-driven investments:\n"
            "• Commercial & Technical Due Diligence: As a Venture Analyst at Aquillius Ventures, I independently performed two comprehensive "
            "due diligences on seed-stage biotechnology ventures, stress-testing biological defensibility, intellectual property moats, and market sizing.\n"
            "• Financial Modeling & Strategy: As a Venture Fellow at the UCSD Rady School of Management, I developed multi-year pro-forma financial models "
            "for deep-tech startups, evaluating burn rate sensitivities and identifying strategic pivot points for founder executive teams.\n"
            "• Deal Sourcing & Ecosystem Building: As Director of Partnerships at Nucleate San Diego, I directed outreach to top regional investors, "
            "orchestrated 10+ ecosystem showcases, and closed corporate sponsorship agreements to back early-stage founders."
        )
        set_font(r2, "Times New Roman", 10.5)

        p3 = doc.add_paragraph()
        p3.paragraph_format.space_after = Pt(8)
        p3.paragraph_format.line_spacing = 1.15
        r3 = p3.add_run(
            f"What excites me most about {job.company} is the opportunity to apply this analytical rigor to your specific mandate in {job.location}. "
            f"Whether analyzing complex omics platforms or evaluating novel therapeutics, I combine the technical fluency to interrogate raw experimental "
            f"data with the commercial discipline to underwrite return profiles. Furthermore, my training as a Licensed Private Pilot has instilled a foundational "
            f"commitment to disciplined risk management and situational composure in high-stakes environments."
        )
        set_font(r3, "Times New Roman", 10.5)

    else:
        # ── Science / Bioengineering Narrative ──
        p1 = doc.add_paragraph()
        p1.paragraph_format.space_after = Pt(8)
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(
            f"I am writing to express my strong interest in the {job.title} position at {job.company}. "
            f"As a Bioengineering Ph.D. candidate in the Zengler Lab at UC San Diego with an extensive background in microbiome engineering, "
            f"metagenomic sequencing, and synthetic communities, I have followed {job.company}'s work with great admiration. "
            f"My research is centered on translating complex microbial dynamics into robust therapeutic and diagnostic platforms, directly aligning "
            f"with {job.company}'s scientific mission in {job.location}."
        )
        set_font(r1, "Times New Roman", 10.5)

        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(8)
        p2.paragraph_format.line_spacing = 1.15
        r2 = p2.add_run(
            "Throughout my doctoral training and prior research fellowships, I have spearheaded complex, cross-functional experimental programs:\n"
            "• Synthetic Community Engineering: Leading the development of UroCom, an engineered urinary microbial community, optimizing anaerobic "
            "culture conditions, metabolic cross-feeding, and in vitro colonization resistance assays.\n"
            "• Next-Generation Omics & Translation: Deep hands-on expertise in MetaRibo-Seq, metatranscriptomics, and absolute bacterial quantification pipelines, "
            "resulting in publications in npj Systems Biology (2025) and manuscripts under review in Nature.\n"
            "• Rigorous Project Leadership: Formerly managed high-throughput longitudinal workflows as an NIH/NIA Postbaccalaureate IRTA Fellow, "
            "coordinating end-to-end histopathology and biomarker validation across large-scale cohort studies."
        )
        set_font(r2, "Times New Roman", 10.5)

        p3 = doc.add_paragraph()
        p3.paragraph_format.space_after = Pt(8)
        p3.paragraph_format.line_spacing = 1.15
        r3 = p3.add_run(
            f"In addition to my laboratory depth, my completion of the IGE Technology Management Program at UCSD has provided me with a distinct advantage: "
            f"I design experiments with clear translational and commercial milestones in mind. I am eager to bring this blend of technical precision, "
            f"innovative problem-solving, and disciplined execution to {job.company} to accelerate your pipeline goals."
        )
        set_font(r3, "Times New Roman", 10.5)

    # ── Closing ──
    p4 = doc.add_paragraph()
    p4.paragraph_format.space_after = Pt(14)
    p4.paragraph_format.line_spacing = 1.15
    r4 = p4.add_run(
        f"Thank you for your time and consideration. I would welcome the opportunity to discuss how my research background and strategic perspective "
        f"can contribute to {job.company}'s ongoing success. I look forward to hearing from you."
    )
    set_font(r4, "Times New Roman", 10.5)

    # ── Sign-off ──
    p_sign = doc.add_paragraph()
    r_sign = p_sign.add_run("Sincerely,\n\nVishant Gandhi\nPh.D. Candidate in Bioengineering | University of California, San Diego")
    set_font(r_sign, "Times New Roman", 10.5)

    # Save to Downloads
    safe_company = "".join(c if c.isalnum() else "_" for c in job.company)
    safe_title = "".join(c if c.isalnum() else "_" for c in job.title)
    
    out_dir = os.environ.get("DOWNLOADS_DIR", "")
    if not out_dir or not os.path.exists(out_dir):
        for d in ["/home/vishant/Downloads", "/tmp", os.path.join(os.path.dirname(__file__), "..", "downloads")]:
            if os.path.exists(d):
                out_dir = d
                break
        if not out_dir:
            out_dir = "/tmp"

    temp_docx = os.path.join(out_dir, f"temp_cl_{safe_company}.docx")
    doc.save(temp_docx)

    # Convert to PDF via LibreOffice
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", temp_docx, "--outdir", out_dir]
    subprocess.run(cmd, check=True)

    final_pdf = os.path.join(out_dir, f"Vishant_Gandhi_Cover_Letter_{safe_company}_{safe_title}.pdf")
    generated_pdf = os.path.join(out_dir, f"temp_cl_{safe_company}.pdf")
    
    if os.path.exists(generated_pdf):
        os.rename(generated_pdf, final_pdf)
    if os.path.exists(temp_docx):
        os.remove(temp_docx)

    return final_pdf
