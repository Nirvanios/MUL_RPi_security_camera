import smtplib
import ssl
import datetime
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


class Email:
    """Class for sending emails.

    Simple class that can send emails to specified email address.
    Mostly used for alarming user of movement in front of camera.
    """

    def __init__(self, sender_address: str, sender_password: str, sender_smtp_server: str, SSL_port: int = 465):
        """
        Initialize secure context and stores important data.

        :param sender_address: Email address from which is email sent.
        :param sender_password: Password to email address from which is email sent.
        :param sender_smtp_server: SMTP server of email address from which is email sent.
        :param SSL_port: Port of SMTP server.
        """
        self.sender_smtp_server = sender_smtp_server
        self.sender_password = sender_password
        self.sender_address = sender_address
        self.SSL_port = SSL_port
        self.secure_context = ssl.create_default_context()

    def send_email(self, remote_addr: str, subject: str = "Movement detected", text_content: str = None, jpg_image: bytes = None):
        """
        Method that sends desired email to recipient.

        :param remote_addr: Email address of recipient.
        :param subject: Subject of email.
                        Optional, default value is "Movement detected"
        :param text_content: Text content of email.
                             Optional, default value is warning about movement with current time and date.
        :param jpg_image: Included image. Optional, default is no image.
        :return: None
        """
        datenow = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if text_content is None:
            text_content = """\
                            Warning! Detected movement on camera. Movement was captured at """ +\
                            datenow\
                            + """\
                            and related images was saved to server.
                            """
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = self.sender_address
        message["To"] = remote_addr
        text = text_content
        message.attach(MIMEText(text, "plain"))
        if jpg_image is not None:
            img = MIMEImage(jpg_image)
            img.add_header('Content-Disposition', "attachment", filename=datenow)
            message.attach(img)

        with smtplib.SMTP_SSL(self.sender_smtp_server, self.SSL_port, context=self.secure_context) as server:
            server.login(self.sender_address, self.sender_password)
            server.sendmail(self.sender_address, remote_addr, message.as_string())

