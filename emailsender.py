import datetime
import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List


class Email:
    """
    Class for sending emails.

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
        self.__secure_context = ssl.create_default_context()

    def send_email(self, remote_addr: str,
                   subject: str = "Movement detected",
                   text_content: str = None,
                   date_time: str = None,
                   jpg_images: List[bytes] = None):
        """
        Method that sends desired email to recipient.

        :param remote_addr: Email address of recipient.
        :param subject: Subject of email.
                        Optional, default value is "Movement detected"
        :param text_content: Text content of email.
                             Optional, default value is warning about movement with current time and date.
        :param date_time: Date that is written in email. Optional, default is datetime.now()
        :param jpg_images: List of images to include. Optional, default is no image.
        :return: None
        """
        if date_time is None:
            date_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if text_content is None:
            text_content = """\
                            Warning! Detected movement on camera. Movement was captured at """ + \
                           date_time \
                           + """\
                            and related images was saved to server.
                            """
        else:
            text_content += "\n" + date_time
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = self.sender_address
        message["To"] = remote_addr
        text = text_content
        message.attach(MIMEText(text, "plain"))
        if jpg_images is not None:
            index = 0
            for image in jpg_images:
                img = MIMEImage(image)
                img.add_header('Content-Disposition', "attachment", filename="img" + str(index))
                message.attach(img)
                index += 1

        with smtplib.SMTP_SSL(self.sender_smtp_server, self.SSL_port, context=self.__secure_context) as server:
            server.login(self.sender_address, self.sender_password)
            server.sendmail(self.sender_address, remote_addr, message.as_string())

