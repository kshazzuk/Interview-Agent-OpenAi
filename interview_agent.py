import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from openai import OpenAI
from fpdf import FPDF
from PIL import Image
import base64

# --- CONFIG ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

client = OpenAI(api_key=OPENAI_API_KEY)


def get_content_and_image(date_str):
    # 1. Generate Text Content (Interview Question)
    text_prompt = """
    Generate exactly 1 advanced C# or ASP.NET Core interview question.
    Format clearly with headers:
    Question:
    Answer:
    Deep Dive:
    Code:

    Do NOT use ASCII diagrams.
    """

    text_response = client.responses.create(
        model="gpt-4.1",
        input=text_prompt
    )

    text_content = text_response.output_text

    # 2. Generate Technical Diagram Image
    topic_line = text_content.splitlines()[0][:60]

    image_prompt = (
        f"A professional, clean technical architectural diagram for {topic_line}. "
        "Minimalist, dark mode, modern UI, sharp lines, enterprise-grade, "
        "high quality, 16:9 aspect ratio."
    )

    image_response = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1792x1024",
        quality="high"
    )

    image_base64 = image_response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    img_path = f"diagram_{date_str}.png"
    with open(img_path, "wb") as f:
        f.write(image_bytes)

    return text_content, img_path


def create_pdf(text, img_path, date_str):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 100, 255)
    pdf.cell(0, 15, ".NET Interview Mastery", ln=True, align="C")

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Generated on {date_str}", ln=True, align="C")
    pdf.ln(5)

    # Content
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, text)

    # Image
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Visual Representation:", ln=True)

    pdf.image(img_path, x=15, w=180)

    pdf_path = f"Interview_Prep_{date_str}.pdf"
    pdf.output(pdf_path)

    return pdf_path


def send_email(content, img_path, pdf_path):
    msg = EmailMessage()
    today = datetime.now().strftime("%b %d, %Y")

    msg["Subject"] = f"🚀 [{today}] C# & ASP.NET Prep"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.set_content(
        "Daily Interview Prep is ready!\n\n"
        "Check the attached PDF for the full deep dive and architectural diagram.\n\n"
        f"{content}"
    )

    for path in [img_path, pdf_path]:
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="octet-stream",
                filename=os.path.basename(path)
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)


if __name__ == "__main__":
    date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        content, img_path = get_content_and_image(date_str)
        pdf_path = create_pdf(content, img_path, date_str)
        send_email(content, img_path, pdf_path)
        print(f"✅ Success: Email sent with OpenAI-generated content for {date_str}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
