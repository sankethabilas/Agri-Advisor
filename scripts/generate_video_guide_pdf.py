"""
Generate a professional, publication-quality PDF guide for the Agri-Advisor Gen AI Video Production.
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for footer page numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "AGRI-ADVISOR | Gen AI Video Production & Demo Guide")
            self.setFont("Helvetica", 8)
            self.drawRightString(558, 755, "Autonomous Multi-Agent AI System")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 748, 558, 748)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Confidential & Academic Submission Reference — Agri-Advisor System")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def create_video_guide_pdf(output_filename: str):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1B4D3E")  # Forest / Agri emerald
    secondary_color = colors.HexColor("#0D9488") # Teal
    dark_slate = colors.HexColor("#0F172A")
    body_color = colors.HexColor("#334155")
    code_bg = colors.HexColor("#F1F5F9")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=body_color,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=body_color,
        leftIndent=15,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=body_color
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=dark_slate
    )

    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # Title Banner
    story.append(Paragraph("Agri-Advisor: Gen AI Video Production Kit", title_style))
    story.append(Paragraph("Complete 3–5 Minute Presentation Blueprint, Word-for-Word Script, Tool Prompts & Visual Asset Capture Checklist", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=0, spaceAfter=12))

    # Executive Overview
    story.append(Paragraph("1. Recommended Video Structure & Timing Plan", h1_style))
    story.append(Paragraph(
        "To achieve maximum marks and academic credibility, maintain a balanced <b>30% AI Presenter / 40% Live System Demo / 20% Architecture & Tech / 10% Responsible AI & Commercialization</b> blend over <b>4 minutes and 30 seconds</b>.",
        body_style
    ))

    # Timing Table
    timing_data = [
        [Paragraph("Time", table_header_style), Paragraph("Section / Topic", table_header_style), Paragraph("Screen Visual (What to Show)", table_header_style), Paragraph("Key Message / Focus", table_header_style)],
        [Paragraph("0:00 - 0:25", table_cell_bold), Paragraph("1. Problem Statement", table_cell_style), Paragraph("AI Presenter + B-roll of crop fields & climate variability challenges", table_cell_style), Paragraph("Information fragmentation, yield losses, disease delays in Sri Lanka", table_cell_style)],
        [Paragraph("0:25 - 0:55", table_cell_bold), Paragraph("2. Solution Overview", table_cell_style), Paragraph("Agri-Advisor Hero UI + System Logo + Value Proposition slide", table_cell_style), Paragraph("Agentic multi-agent agricultural intelligence platform", table_cell_style)],
        [Paragraph("0:55 - 1:45", table_cell_bold), Paragraph("3. Agent Architecture", table_cell_style), Paragraph("Interactive Architecture Diagram (Supervisor, Crop, Disease, Sentinel)", table_cell_style), Paragraph("Orchestration, intent routing, tool usage, asynchronous telemetry", table_cell_style)],
        [Paragraph("1:45 - 2:50", table_cell_bold), Paragraph("4. Live System Demo", table_cell_style), Paragraph("Screen Recording: Streamlit Bento UI, Query execution, Sentinel map", table_cell_style), Paragraph("Real-time crop advice, leaf symptom diagnosis, disease anomaly alert", table_cell_style)],
        [Paragraph("2:50 - 3:25", table_cell_bold), Paragraph("5. Core Technologies", table_cell_style), Paragraph("Tech stack badges: FastAPI, Gemini 1.5, RAG, ChromaDB, APScheduler", table_cell_style), Paragraph("NLP intent parser, DOA knowledge base retrieval, prompt security", table_cell_style)],
        [Paragraph("3:25 - 3:55", table_cell_bold), Paragraph("6. Responsible AI", table_cell_style), Paragraph("Split screen: Trilingual UI, DOA 1920 hotline citation, safety badge", table_cell_style), Paragraph("Hallucination guardrails, confidence scoring, farmer privacy", table_cell_style)],
        [Paragraph("3:55 - 4:20", table_cell_bold), Paragraph("7. Commercialization", table_cell_style), Paragraph("Business model slide: Free Farmer App, B2B API, Gov Dashboard", table_cell_style), Paragraph("Scalability, cloud deployment, Agritech monetization roadmap", table_cell_style)],
        [Paragraph("4:20 - 4:35", table_cell_bold), Paragraph("8. Conclusion & Impact", table_cell_style), Paragraph("AI Presenter closing + Agri-Advisor GitHub/Contact badge", table_cell_style), Paragraph("Empowering 2M+ smallholders with resilient AI agronomy", table_cell_style)],
    ]

    t_timing = Table(timing_data, colWidths=[65, 95, 185, 160])
    t_timing.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_timing)
    story.append(Spacer(1, 10))

    # Page Break for Script Section
    story.append(PageBreak())

    # Section 2: Complete Word-for-Word Voiceover Script
    story.append(Paragraph("2. Complete Word-for-Word Video Script (Timed)", h1_style))
    story.append(Paragraph("Use this script directly for your voiceover generation in <b>ElevenLabs</b>, <b>HeyGen</b>, or live audio narration.", body_style))

    script_sections = [
        ("0:00 - 0:25 | Scene 1: The Agricultural Crisis", [
            "[Visual: AI Presenter in professional attire + subtle agricultural background / B-roll of Sri Lankan paddy fields]",
            "Voiceover: \"Agriculture sustains over two million farming families in Sri Lanka, yet smallholders face catastrophic yield losses each season due to unpredictable weather, emerging crop diseases, and fragmented advisory services. When a farmer encounters a mysterious leaf blight or prepares for the Maha planting season, actionable expert advice from agricultural instructors is often delayed or inaccessible. To solve this critical bottleneck, we built Agri-Advisor.\""
        ]),
        ("0:25 - 0:55 | Scene 2: Introducing Agri-Advisor", [
            "[Visual: Cut to Agri-Advisor Streamlit Dashboard — Bento grid, real-time microclimate widget, and modern dark mode UI]",
            "Voiceover: \"Agri-Advisor is an autonomous, agentic AI platform engineered specifically for Sri Lankan agriculture. Powered by state-of-the-art Large Language Models, specialized Retrieval-Augmented Generation, and multi-agent coordination, Agri-Advisor delivers instant, scientifically verified cultivation plans, rapid visual disease diagnoses, and autonomous regional outbreak surveillance in Sinhala, Tamil, and English.\""
        ]),
        ("0:55 - 1:45 | Scene 3: Multi-Agent Architecture & Communication", [
            "[Visual: Animated Architecture Diagram highlighting Orchestrator Hub and 4 specialized agents]",
            "Voiceover: \"Under the hood, Agri-Advisor operates through a robust multi-agent architecture. At the center is our Orchestrator Supervisor, which receives farmer inquiries, validates input security against prompt injection, and executes multi-intent query parsing.\n"
            "The Orchestrator dispatches tasks to specialized autonomous agents via asynchronous REST and MCP protocols:\n"
            "First, the Crop Specialist Agent queries our curated Sri Lanka Department of Agriculture knowledge base to formulate 8-section cultivation schedules for paddy, maize, and chillies.\n"
            "Second, the Disease Specialist Agent processes visual symptoms and leaf images using multi-modal AI and symptom vector matching.\n"
            "Third, our Autonomous Outbreak Sentinel Agent executes continuous background surveillance, aggregating diagnosis telemetry across 25 administrative districts to predict epidemic hotspots before they spread.\""
        ]),
        ("1:45 - 2:50 | Scene 4: Live System Demonstration (The Core 40%)", [
            "[Visual: Screen recording of user interacting with the live Streamlit application at localhost:8501]",
            "Voiceover: \"Let's see Agri-Advisor in action.\n"
            "[Action: Typing query 'I have 2 acres of sandy loam in Anuradhapura for Yala season. Recommend fertilizer and water management for Bg 352']\n"
            "Notice how the multi-agent pipeline stepper activates in real-time. Within 1.2 seconds, the Crop Agent synthesizes a complete cultivation advisory: seed rate calculation, basal and top-dressing fertilizer schedules, water management, and expected harvest yield.\n"
            "[Action: Switching to Crop Health tab and uploading a leaf image showing Brown Spot]\n"
            "Next, a farmer uploads a leaf photo. The Disease Agent classifies the pathology with an 88% confidence score, cites symptoms, recommends organic and chemical treatments, and embeds the official DOA 1920 agricultural hotline for emergency escalation.\n"
            "[Action: Navigating to Outbreak Sentinel Surveillance Radar]\n"
            "Finally, the Outbreak Sentinel command center displays active surveillance across districts. When diagnosis clusters breach statistical thresholds, the Sentinel automatically dispatches trilingual SMS and WhatsApp alerts to registered farmers in the zone.\""
        ]),
        ("2:50 - 3:25 | Scene 5: Technical Stack & Information Retrieval", [
            "[Visual: Fast-paced technical infographic with code snippets and architecture icons]",
            "Voiceover: \"Our technical stack is built for enterprise-grade reliability and speed. The backend is powered by FastAPI with asynchronous ASGI concurrency. We utilize Google Gemini 1.5 Pro and Flash with structured JSON schemas and function calling.\n"
            "Information Retrieval is anchored on the official Sri Lanka Department of Agriculture knowledge base, utilizing hybrid vector search and deterministic rule verification to eliminate hallucinations. State management and telemetry are backed by MongoDB and SQLite with full ACID compliance.\""
        ]),
        ("3:25 - 3:55 | Scene 6: Responsible AI & Security Guardrails", [
            "[Visual: Responsible AI slide with security shields, multilingual UI samples, and disclaimer banners]",
            "Voiceover: \"Responsible AI is woven into every layer of Agri-Advisor. We enforce zero-trust input sanitization to neutralize prompt injection and jailbreak attempts. To prevent hallucinations, every recommendation includes verifiable DOA citations and confidence indicators. Low-confidence queries automatically fail-safe to human extension officers. We respect farmer privacy through anonymized district telemetry, and democratize access with native Sinhala, Tamil, and English support.\""
        ]),
        ("3:55 - 4:20 | Scene 7: Commercialization & Business Viability", [
            "[Visual: Market opportunity slide, B2B/B2G pricing tiers, and national scaling map]",
            "Voiceover: \"Agri-Advisor features a high-impact commercialization roadmap. We operate a Freemium model for smallholder farmers, providing core advisory services at zero cost. For commercial agribusinesses, seed suppliers, and microfinance insurers, we offer tiered B2B API subscriptions for microclimate data and disease telemetry. Furthermore, our Outbreak Sentinel integrates as a B2G National Pest Surveillance Dashboard for the Ministry of Agriculture.\""
        ]),
        ("4:20 - 4:35 | Scene 8: Conclusion & Call to Action", [
            "[Visual: AI Presenter returns + Agri-Advisor system logo, GitHub repository QR code, and contact information]",
            "Voiceover: \"Agri-Advisor demonstrates how Agentic AI can transform traditional agriculture into a proactive, resilient, and data-driven ecosystem. Thank you for your time, and we welcome your questions.\""
        ])
    ]

    for header, paragraphs in script_sections:
        story.append(Paragraph(header, h2_style))
        for p in paragraphs:
            if p.startswith("[Visual:"):
                story.append(Paragraph(f"<b>{p}</b>", callout_style))
            else:
                story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 4))

    # Page Break for Prompts & Assets
    story.append(PageBreak())

    # Section 3: Prompts for AI Video Generators
    story.append(Paragraph("3. Exact Prompts for Gen AI Video Tools", h1_style))
    story.append(Paragraph("Copy and paste these exact prompts into your chosen AI tools to generate avatars, B-roll, and narration.", body_style))

    # HeyGen / Synthesia Prompt Box
    story.append(Paragraph("A. HeyGen / Synthesia Presenter Prompt", h2_style))
    story.append(Paragraph(
        "<b>Avatar Selection:</b> Professional Tech Presenter / Consultant (Male or Female, Smart Casual / Blazer with green accent)<br/>"
        "<b>Background:</b> Modern high-tech clean glass office with subtle green agricultural foliage or smart agritech laboratory bokeh.<br/>"
        "<b>Voice Tone:</b> Confident, articulate, warm, executive, paced at 145 words per minute.<br/>"
        "<b>Camera Framing:</b> Medium close-up (chest-up), looking directly into lens with natural gestures.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    # Pika / Midjourney / Runway B-roll Prompts
    story.append(Paragraph("B. Pika / Midjourney / Runway B-Roll Video Prompts", h2_style))
    broll_prompts = [
        ("Prompt 1 (Problem B-Roll):", "Cinematic drone shot flying over lush green Sri Lankan terraced rice paddy fields in Anuradhapura, golden hour sunlight, hyper-realistic, 4K, 24fps --ar 16:9"),
        ("Prompt 2 (Farmer Interaction):", "A Sri Lankan farmer holding a modern smartphone in a crop field, inspecting a leaf while interacting with a clean AI mobile application interface, soft sunlight, professional documentary style, 4K --ar 16:9"),
        ("Prompt 3 (AI Architecture Concept):", "Futuristic holographic multi-agent network visualization, interconnected glowing green nodes exchanging data streams over agricultural topographic map, dark slate tech background, sleek 3D render, 8K --ar 16:9"),
        ("Prompt 4 (Disease Outbreak Radar):", "Modern digital command center with high-tech glowing radar map showing district heatmaps and epidemic alerts, high contrast cyber-green and slate interface, 4K --ar 16:9")
    ]
    for label, prompt in broll_prompts:
        story.append(Paragraph(f"<b>{label}</b>", bullet_style))
        story.append(Table([[Paragraph(prompt, code_style)]], colWidths=[500], style=[
            ('BACKGROUND', (0,0), (-1,-1), code_bg),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(Spacer(1, 3))

    # ElevenLabs Prompt Box
    story.append(Spacer(1, 4))
    story.append(Paragraph("C. ElevenLabs Voice Settings & Pronunciation Notes", h2_style))
    story.append(Paragraph(
        "<b>Recommended Voice:</b> 'Adam' (Deep & Professional) or 'Rachel' (Clear & Authoritative)<br/>"
        "<b>Stability:</b> 0.65 | <b>Clarity / Similarity:</b> 0.85 | <b>Style Exaggeration:</b> 0.10<br/>"
        "<b>Pronunciation Guide:</b><br/>"
        "• <i>DOA</i> → Pronounce as 'D-O-A' (Department of Agriculture)<br/>"
        "• <i>Maha / Yala</i> → Pronounce as 'Mah-hah' / 'Yah-lah' (Sri Lankan cultivation seasons)<br/>"
        "• <i>Bg 352</i> → Pronounce as 'B-g three-fifty-two'<br/>"
        "• <i>Anuradhapura</i> → Pronounce as 'Ah-noo-rah-dah-poo-rah'",
        bullet_style
    ))

    # Page Break for Asset Checklist
    story.append(PageBreak())

    # Section 4: Visual Asset Capture Checklist
    story.append(Paragraph("4. Visual Asset Capture Checklist (What to Record)", h1_style))
    story.append(Paragraph(
        "Capture these exact 7 screenshots and 4 screen recordings from your local running environment (<b>http://localhost:8501</b> and <b>http://localhost:8000/docs</b>) to assemble your 40% demo section.",
        body_style
    ))

    assets_data = [
        [Paragraph("Asset ID", table_header_style), Paragraph("Type", table_header_style), Paragraph("Screen / Component to Capture", table_header_style), Paragraph("Action to Perform / Duration", table_header_style)],
        [Paragraph("REC-01", table_cell_bold), Paragraph("Video (MP4)", table_cell_style), Paragraph("AI Workspace Tab (Query Execution)", table_cell_style), Paragraph("Record typing query 'Cultivation plan for Chilli in Jaffna Yala', click Generate, capture multi-agent pipeline stepper animating (15s)", table_cell_style)],
        [Paragraph("REC-02", table_cell_bold), Paragraph("Video (MP4)", table_cell_style), Paragraph("Advisory Output View", table_cell_style), Paragraph("Smooth scroll through the generated 8-section plan (Fertilizer table, Pest alert, DOA 1920 hotline card, Export PDF button) (15s)", table_cell_style)],
        [Paragraph("REC-03", table_cell_bold), Paragraph("Video (MP4)", table_cell_style), Paragraph("Crop Health Diagnosis Tab", table_cell_style), Paragraph("Upload diseased leaf sample image, show instant diagnosis card with 88% confidence and organic remedy breakdown (15s)", table_cell_style)],
        [Paragraph("REC-04", table_cell_bold), Paragraph("Video (MP4)", table_cell_style), Paragraph("Outbreak Sentinel Radar Tab", table_cell_style), Paragraph("Click 'Run Autonomous Scan', show anomaly detection alert triggered for Anuradhapura Paddy Blast with trilingual notification preview (15s)", table_cell_style)],
        [Paragraph("IMG-01", table_cell_bold), Paragraph("Screenshot", table_cell_style), Paragraph("Bento Grid Dashboard", table_cell_style), Paragraph("Full-screen capture of main dashboard with Agro-Weather widget and market crop prices", table_cell_style)],
        [Paragraph("IMG-02", table_cell_bold), Paragraph("Screenshot", table_cell_style), Paragraph("Agent Network Topology View", table_cell_style), Paragraph("Agent status cards showing latency metrics (Crop Agent: 1.1s, Disease Agent: 1.4s, Sentinel: Active)", table_cell_style)],
        [Paragraph("IMG-03", table_cell_bold), Paragraph("Screenshot", table_cell_style), Paragraph("FastAPI Swagger Docs (/docs)", table_cell_style), Paragraph("Interactive API endpoints at localhost:8000/docs showing /api/v1/orchestrator and /api/v1/sentinel", table_cell_style)],
        [Paragraph("IMG-04", table_cell_bold), Paragraph("Screenshot", table_cell_style), Paragraph("Pytest Terminal Test Suite", table_cell_style), Paragraph("Terminal output showing pytest green test execution for Sentinel anomaly classification & stats", table_cell_style)],
    ]

    t_assets = Table(assets_data, colWidths=[55, 65, 175, 210])
    t_assets.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_assets)
    story.append(Spacer(1, 10))

    # Section 5: Video Assembly & Editing Instructions
    story.append(Paragraph("5. Step-by-Step Video Assembly in CapCut / Canva / Premiere", h1_style))
    story.append(Paragraph(
        "<b>Step 1: Audio Assembly</b> — Import the ElevenLabs voiceover MP3 or generate the HeyGen avatar video with the script above.<br/>"
        "<b>Step 2: Timeline Layout (16:9, 1080p 60fps)</b> —<br/>"
        "• <i>0:00 - 0:55:</i> Full-screen HeyGen Presenter + crossfade to Agri-Advisor Bento UI screenshot.<br/>"
        "• <i>0:55 - 1:45:</i> Full-screen Architecture Diagram with glowing highlight boxes as each agent is mentioned.<br/>"
        "• <i>1:45 - 2:50:</i> Full-screen live screen recordings (REC-01 to REC-04). Add a Picture-in-Picture (PiP) circular avatar of the presenter in the bottom right corner.<br/>"
        "• <i>2:50 - 4:20:</i> Tech Stack & Commercialization slides with smooth slide-in animations.<br/>"
        "• <i>4:20 - 4:35:</i> Full-screen Presenter closing with GitHub repository QR code.<br/>"
        "<b>Step 3: Captions & Audio Polish</b> — Auto-generate subtitles with high contrast yellow/white text and add soft ambient corporate background music (-22dB).",
        bullet_style
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_filename}")


if __name__ == "__main__":
    output_path = os.path.abspath("docs/Agri_Advisor_GenAI_Video_Production_Kit.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    create_video_guide_pdf(output_path)
