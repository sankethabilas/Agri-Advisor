"""
Generate a dedicated, professional PDF document for the Generative AI Video Creation Platform System Architecture.
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
        
        if self._pageNumber > 1:
            self.drawString(54, 755, "SYSTEM ARCHITECTURE: Gen AI Multi-Agent Video Platform")
            self.setFont("Helvetica", 8)
            self.drawRightString(558, 755, "Enterprise Engineering Blueprint")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 748, 558, 748)

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Autonomous Multi-Agent Collaboration & LLM Reasoning Framework")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def create_architecture_pdf(output_filename: str):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0F172A")   # Deep Slate
    brand_blue = colors.HexColor("#0284C7")      # Cyan / Blue
    purple_accent = colors.HexColor("#7C3AED")   # Violet
    dark_slate = colors.HexColor("#0F172A")
    body_color = colors.HexColor("#334155")
    code_bg = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=brand_blue,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=purple_accent,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=body_color,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=body_color,
        leftIndent=12,
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=body_color
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=dark_slate
    )

    story = []

    # Title Banner
    story.append(Paragraph("System Architecture: Generative AI Video Platform", title_style))
    story.append(Paragraph("Multi-Agent Autonomous Collaboration, LLM Reasoning Core & Closed-Loop Quality Control", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=brand_blue, spaceBefore=0, spaceAfter=10))

    # Section 1: Overview
    story.append(Paragraph("1. System Overview & Cognitive Decoupling", h1_style))
    story.append(Paragraph(
        "The platform automatically transforms natural-language video ideas into broadcast-ready videos. "
        "Crucially, the <b>Large Language Model (LLM) acts as the cognitive brain and orchestrator</b> (performing planning, script decomposition, prompt synthesis, and quality auditing) rather than directly generating raw video pixels. "
        "Domain-specialized AI agents interface through a <b>Unified Model Gateway</b> to drive diffusion image generators, video motion models, neural TTS, and music synthesizers.",
        body_style
    ))

    # Section 2: 6-Layer Architecture Breakdown
    story.append(Paragraph("2. 6-Layer Architectural Hierarchy", h1_style))

    layers_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Component Name", table_header_style), Paragraph("Key Responsibilities & Technologies", table_header_style)],
        [Paragraph("Layer 1", table_cell_bold), Paragraph("Presentation Layer", table_cell_style), Paragraph("Next.js / Streamlit web interface for prompt entry, style selection (16:9/9:16), voice selection, real-time pipeline stepper, and final video player.", table_cell_style)],
        [Paragraph("Layer 2", table_cell_bold), Paragraph("API & Application Services", table_cell_style), Paragraph("FastAPI Gateway, OAuth2/JWT authentication, rate limiting, prompt sanitization, asynchronous Celery/Redis job queues, and WebSocket event streams.", table_cell_style)],
        [Paragraph("Layer 3", table_cell_bold), Paragraph("Cognitive Orchestration (Brain)", table_cell_style), Paragraph("Orchestrator Agent (DAG state coordinator) + LLM Reasoning Engine (Gemini 1.5 Pro / GPT-4o) for task decomposition, context routing, and agent synchronization.", table_cell_style)],
        [Paragraph("Layer 4", table_cell_bold), Paragraph("Specialized AI Agent Swarm", table_cell_style), Paragraph("8 Autonomous Agents: (1) Script & Story, (2) Storyboard, (3) Prompt Engineering, (4) Visual Asset, (5) Video Generation, (6) Voice & Audio, (7) Video Editor, (8) QC Critic.", table_cell_style)],
        [Paragraph("Layer 5", table_cell_bold), Paragraph("Model Gateway & Foundation Models", table_cell_style), Paragraph("Unified proxy routing to Diffusion models (Flux, SDXL), Video Gen (Gen-3, Sora, Kling), Neural TTS (ElevenLabs), and Music AI (Suno, MusicLM).", table_cell_style)],
        [Paragraph("Layer 6", table_cell_bold), Paragraph("Data & Storage Infrastructure", table_cell_style), Paragraph("Vector Database (Chroma/Pinecone) for character/style embeddings, PostgreSQL for job metadata, Redis for caching, S3/MinIO for raw clips & final MP4.", table_cell_style)],
    ]

    t_layers = Table(layers_data, colWidths=[50, 120, 334])
    t_layers.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_layers)
    story.append(Spacer(1, 8))

    # Section 3: Specialized Agent Responsibilities
    story.append(Paragraph("3. Specialized AI Agent Swarm & Delegation Matrix", h1_style))

    agents_data = [
        [Paragraph("Specialized Agent", table_header_style), Paragraph("Input Artifact", table_header_style), Paragraph("Execution Output", table_header_style), Paragraph("Target Generative Model", table_header_style)],
        [Paragraph("1. Script Agent", table_cell_bold), Paragraph("User prompt & tone constraints", table_cell_style), Paragraph("Scene-by-scene structured dialogue & narration", table_cell_style), Paragraph("LLM (Structured JSON Mode)", table_cell_style)],
        [Paragraph("2. Storyboard Agent", table_cell_bold), Paragraph("Scene-by-scene script", table_cell_style), Paragraph("Camera angles, lighting, characters & duration specs", table_cell_style), Paragraph("LLM Reasoning & Rules Engine", table_cell_style)],
        [Paragraph("3. Prompt Agent", table_cell_bold), Paragraph("Storyboard specifications", table_cell_style), Paragraph("Model-optimized positive/negative prompts & seeds", table_cell_style), Paragraph("LLM Prompt Optimizer", table_cell_style)],
        [Paragraph("4. Visual Agent", table_cell_bold), Paragraph("Visual generation prompts", table_cell_style), Paragraph("Consistent character reference sheets & keyframe art", table_cell_style), Paragraph("Diffusion Models (Flux / SDXL)", table_cell_style)],
        [Paragraph("5. Video Agent", table_cell_bold), Paragraph("Keyframes + video prompts", table_cell_style), Paragraph("Individual high-motion video clips per scene", table_cell_style), Paragraph("Runway Gen-3 / Sora / Kling", table_cell_style)],
        [Paragraph("6. Audio Agent", table_cell_bold), Paragraph("Dialogue text + mood tags", table_cell_style), Paragraph("Neural narration, SFX & adaptive music stems", table_cell_style), Paragraph("ElevenLabs TTS + Suno AI", table_cell_style)],
        [Paragraph("7. Editing Agent", table_cell_bold), Paragraph("Video clips + audio stems", table_cell_style), Paragraph("Timeline cut, color grading, subtitles & final sync", table_cell_style), Paragraph("FFmpeg / Automated NLE Engine", table_cell_style)],
        [Paragraph("8. QC Critic Agent", table_cell_bold), Paragraph("Draft video + original specs", table_cell_style), Paragraph("Pass/Fail score + Selective regeneration instructions", table_cell_style), Paragraph("Vision-LLM (Gemini / GPT-4V)", table_cell_style)],
    ]

    t_agents = Table(agents_data, colWidths=[85, 120, 165, 134])
    t_agents.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), purple_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_agents)

    # Page Break for Flow & QC Loop
    story.append(PageBreak())

    # Section 4: Closed-Loop QC Feedback & Self-Healing
    story.append(Paragraph("4. End-to-End Workflow & Self-Healing QC Feedback Loop", h1_style))
    story.append(Paragraph(
        "<b>Sequential Flow:</b> User Prompt &rarr; API Gateway &rarr; Orchestrator Agent &rarr; LLM Planning &rarr; Script Agent &rarr; Storyboard Agent &rarr; Prompt Agent &rarr; Visual Agent &rarr; Video Agent &rarr; Audio Agent &rarr; Editing Agent &rarr; QC Critic Agent.<br/><br/>"
        "<b>Closed-Loop Quality Control:</b><br/>"
        "• <b>Acceptance Path (Score &ge; 85%):</b> The video meets all prompt adherence, audio-visual sync, and physical coherence thresholds &rarr; Published to Object Storage & delivered to User.<br/>"
        "• <b>Rejection & Self-Healing Path (Score &lt; 85%):</b> The QC Critic Agent detects flaws (e.g., motion distortion in Scene 3 or desynced voiceover) and issues a structured retry payload to the Orchestrator. The Orchestrator initiates <b>targeted re-execution only for the defective subtask</b> (avoiding expensive full-video regeneration).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 5: Scenario Walkthrough
    story.append(Paragraph("5. Example Scenario: 60-Second Futuristic City Video", h1_style))

    scenario_data = [
        [Paragraph("Step", table_header_style), Paragraph("Executing Agent / Module", table_header_style), Paragraph("Operational Workflow & Intermediate Output", table_header_style)],
        [Paragraph("1", table_cell_bold), Paragraph("User Input", table_cell_style), Paragraph("'Create a 60-second cinematic sci-fi video of a futuristic city with flying cars and sky gardens. 16:9, deep male narration.'", table_cell_style)],
        [Paragraph("2", table_cell_bold), Paragraph("Orchestrator + LLM", table_cell_style), Paragraph("Decomposes request into 4 distinct 15s scenes: (1) Skyline Establishing Shot, (2) Maglev Highway, (3) Bio-dome Garden, (4) Horizon Outro.", table_cell_style)],
        [Paragraph("3", table_cell_bold), Paragraph("Script Agent", table_cell_style), Paragraph("Generates 4 narrative beats with precise word counts tuned for 145 wpm narration.", table_cell_style)],
        [Paragraph("4", table_cell_bold), Paragraph("Storyboard Agent", table_cell_style), Paragraph("Defines camera angles (aerial drone, tracking dolly, macro focal lens) and cyber-organic lighting parameters.", table_cell_style)],
        [Paragraph("5", table_cell_bold), Paragraph("Prompt Agent", table_cell_style), Paragraph("Generates optimized diffusion & video prompts with negative prompts for artifact reduction.", table_cell_style)],
        [Paragraph("6", table_cell_bold), Paragraph("Visual Agent", table_cell_style), Paragraph("Generates 4 master keyframe images with consistent architectural styles using Vector DB seeds.", table_cell_style)],
        [Paragraph("7", table_cell_bold), Paragraph("Video Agent", table_cell_style), Paragraph("Generates 4 high-definition video clips applying camera motion vectors (Runway Gen-3 / Sora).", table_cell_style)],
        [Paragraph("8", table_cell_bold), Paragraph("Voice & Audio Agent", table_cell_style), Paragraph("Synthesizes voiceover in ElevenLabs, generates ambient synth score, and layers futuristic vehicle sound effects.", table_cell_style)],
        [Paragraph("9", table_cell_bold), Paragraph("Video Editing Agent", table_cell_style), Paragraph("Assembles timeline, applies seamless crossfades, aligns audio stems, and renders high-contrast subtitles.", table_cell_style)],
        [Paragraph("10", table_cell_bold), Paragraph("QC Critic Agent", table_cell_style), Paragraph("Audits motion smoothness and audio alignment &rarr; Score: 93% (PASS) &rarr; Final 4K MP4 delivered to user.", table_cell_style)],
    ]

    t_scenario = Table(scenario_data, colWidths=[30, 110, 364])
    t_scenario.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), brand_blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_scenario)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully generated at: {output_filename}")


if __name__ == "__main__":
    output_path = os.path.abspath("docs/Gen_AI_Video_Platform_System_Architecture.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    create_architecture_pdf(output_path)
