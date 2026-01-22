import os
import smtplib
from flask import Flask, render_template, request, redirect, url_for, session
from email.message import EmailMessage
from openai import OpenAI
from dotenv import load_dotenv

# ================================
# LOAD ENV VARIABLES
# ================================
load_dotenv()

# ================================
# CONFIGURATION
# ================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

CANDIDATE_NAME = "Vamsi Krishna"
PHONE_NUMBER = "+91-XXXXXXXXXX"
LINKEDIN_URL = "https://www.linkedin.com/in/your-profile"
EMAIL_ADDRESS = "vamsikrishna9656@gmail.com"

UPLOAD_FOLDER = "uploads"

# ================================
# APP SETUP
# ================================
app = Flask(__name__)
app.secret_key = "preview-secret-key"  # needed for session
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = OpenAI(api_key=OPENAI_API_KEY)

# ================================
# AI FUNCTION (JD ONLY)
# ================================


def generate_email_from_jd(job_title, jd, hr_name):
    prompt = f"""
You are a professional career assistant.

Write a concise, formal job application email.

Rules:
- Do NOT include subject line
- Start with: Dear {hr_name},
- Fully based on the Job Description
- No placeholders
- No emojis

Candidate Name: {CANDIDATE_NAME}
Job Title: {job_title}

Job Description:
{jd}

Signature (use exactly):
{CANDIDATE_NAME}
Phone: {PHONE_NUMBER}
LinkedIn: {LINKEDIN_URL}
Email: {EMAIL_ADDRESS}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()

# ================================
# EMAIL SENDER
# ================================


def send_email(hr_email, subject, body, resume_path):
    msg = EmailMessage()
    msg["From"] = GMAIL_EMAIL
    msg["To"] = hr_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(resume_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(resume_path)
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.send_message(msg)

# ================================
# ROUTES
# ================================


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        hr_email = request.form["hr_email"]
        hr_name = request.form["hr_name"]
        job_title = request.form["job_title"]
        jd = request.form["job_description"]
        resume = request.files["resume"]

        resume_path = os.path.join(
            app.config["UPLOAD_FOLDER"], resume.filename)
        resume.save(resume_path)

        email_body = generate_email_from_jd(job_title, jd, hr_name)
        subject = f"Application for {job_title} | {CANDIDATE_NAME}"

        # Store in session for preview
        session["hr_email"] = hr_email
        session["subject"] = subject
        session["email_body"] = email_body
        session["resume_path"] = resume_path

        return redirect(url_for("preview"))

    return render_template("index.html")


@app.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST":
        # Read edited values from preview form
        hr_email = request.form["hr_email"]
        subject = request.form["subject"]
        email_body = request.form["email_body"]
        resume_path = session["resume_path"]

        send_email(
            hr_email,
            subject,
            email_body,
            resume_path
        )
        return redirect(url_for("success"))

    return render_template(
        "preview.html",
        hr_email=session["hr_email"],
        subject=session["subject"],
        email_body=session["email_body"]
    )


@app.route("/success")
def success():
    return render_template("success.html")


# ================================
# RUN
# ================================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
