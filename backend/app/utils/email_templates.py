APP_NAME = "Ethiopian Job Platform"


def verification_email_html(verification_url: str, first_name: str) -> tuple[str, str]:
    subject = f"Verify your email - {APP_NAME}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Welcome to {APP_NAME}</h2>
        <p>Hi {first_name},</p>
        <p>Thank you for creating an account. Please verify your email address by clicking the button below:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}"
               style="background-color: #2563eb; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Verify Email
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            This link expires in 24 hours. If you did not create an account, please ignore this email.
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="color: #9ca3af; font-size: 12px;">{APP_NAME} &copy; 2026</p>
    </body>
    </html>
    """
    return subject, html


def welcome_email_html(first_name: str) -> tuple[str, str]:
    subject = f"Welcome to {APP_NAME}!"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Your account is verified!</h2>
        <p>Hi {first_name},</p>
        <p>Your email has been successfully verified. Welcome to {APP_NAME}!</p>
        <p>You can now:</p>
        <ul>
            <li>Complete your profile to attract employers</li>
            <li>Browse and apply for jobs</li>
            <li>Save jobs for later</li>
        </ul>
        <p style="text-align: center; margin: 30px 0;">
            <a href="https://jobfinder.local"
               style="background-color: #2563eb; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Get Started
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="color: #9ca3af; font-size: 12px;">{APP_NAME} &copy; 2026</p>
    </body>
    </html>
    """
    return subject, html


def resend_verification_html(verification_url: str, first_name: str) -> tuple[str, str]:
    subject = f"Verify your email - {APP_NAME}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Email Verification</h2>
        <p>Hi {first_name},</p>
        <p>You requested a new verification link. Click below to verify your email:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}"
               style="background-color: #2563eb; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Verify Email
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            This link expires in 24 hours.
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="color: #9ca3af; font-size: 12px;">{APP_NAME} &copy; 2026</p>
    </body>
    </html>
    """
    return subject, html
