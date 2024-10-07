import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_mail(subject, to_email, context, mail_type):
    try:
        # Render the HTML content using a template
        if mail_type == "otp-email":
            html_message = render_to_string('mail-templates/otp-email.html', context)
        elif mail_type == "reset-otp-email":
            html_message = render_to_string('mail-templates/email-reset-password.html', context)

        # Strip tags to create a plain text version
        plain_message = strip_tags(html_message)
        
        # Create the email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,  # Use the email from settings
            to=[to_email]
        )
        
        # Attach HTML content as an alternative
        email.attach_alternative(html_message, "text/html")
        
        # Send the email
        email.send()
        logging.info(f"OTP email sent successfully to {to_email}")
    
    except Exception as e:
        logging.error(f"Failed to send OTP email to {to_email}: {str(e)}")