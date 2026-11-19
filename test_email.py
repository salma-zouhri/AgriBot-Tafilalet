import os, ssl, smtplib
from email.message import EmailMessage

sender = os.environ.get("GMAIL_USER")
app_password = os.environ.get("GMAIL_APP_PASSWORD")
receiver = sender  # envoie à toi-même pour tester

msg = EmailMessage()
msg["Subject"] = "Test AgriBot"
msg["From"] = sender
msg["To"] = receiver
msg.set_content("Ceci est un test depuis ton app AgriBot 🌱")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(msg)
    print("✅ Email envoyé avec succès")
except Exception as e:
    print("❌ Erreur:", e)