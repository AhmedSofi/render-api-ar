from fastapi import FastAPI, Query, Response
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import re
import google.generativeai as genai
import os
import arabic_reshaper
from bidi.algorithm import get_display

app = FastAPI()

def gemini(question_and_answer: str):
    genai.configure(api_key='AIzaSyAFAmVIP6l33PQUj5G0Yk05RyH9u42g1gg')
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(
        f'صف كل سؤال وإجابته، وقدم معلومات عن السؤال والإجابة، وطرق العلاج إن وجدت، وما إذا كان يتطلب استشارة طبيب أم لا. {question_and_answer}'
    )
    return response.text

def format_text_for_pdf(input_string):
    formatted_string = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', input_string)
    formatted_string = re.sub(r'\*(.*?)\*', r'<font color="darkgrey">\1</font>', formatted_string)
    formatted_string = formatted_string.replace('*', '')
    return formatted_string

def create_pdf(input_string, output_file):
    formatted_text = format_text_for_pdf(input_string)

    # Ensure the font file is in the correct path
    font_path = 'G:/cs/api_project/Amiri-0.112/Amiri-0.112/Amiri-Regular.ttf'  # Ensure this is the correct path to the TTF file
    if not os.path.isfile(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    # Register a font that supports Arabic
    pdfmetrics.registerFont(TTFont('Arabic', font_path))

    doc = SimpleDocTemplate(output_file, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        name='Custom',
        parent=styles['BodyText'],
        fontName='Arabic',  # Use the Arabic font
        fontSize=12,
        leading=14,
        rightIndent=0,
        leftIndent=0,
        spaceAfter=10,
        alignment=2,  # Right alignment for Arabic text
        language='ar',  # Specify Arabic language
    )

    story = []

    for part in formatted_text.split('\n'):
        if part.strip():
            reshaped_text = arabic_reshaper.reshape(part)
            bidi_text = get_display(reshaped_text)
            paragraph = Paragraph(bidi_text, custom_style)
            story.append(paragraph)
            story.append(Spacer(1, 12))

    print(story)
    doc.build(story)

@app.get("/generate_pdf/")
async def generate_pdf(question: list = Query(...), answer: list = Query(...)):
    question_and_answer = ""
    for cu, (q, a) in enumerate(zip(question, answer), start=1):
        question_and_answer += f"س {cu}: {q}\nج {cu}: {a}\n"

    output_file = "output.pdf"
    input_string = gemini(question_and_answer)
    create_pdf(input_string, output_file)

    with open(output_file, 'rb') as f:
        pdf_content = f.read()

    return Response(content=pdf_content, media_type='application/pdf',
                    headers={'Content-Disposition': 'attachment; filename="output.pdf"'})

@app.get("/")
async def read_root():
    return {"Hello": "sofi770"}
