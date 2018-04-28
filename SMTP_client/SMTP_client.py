import socket
import ssl
import base64
import configparser
import mimetypes


class SMTP_client:
    def __init__(self):
        self.message_dir = 'message/'
        self.server = ()
        self.login = ''
        self.password = ''
        self.receivers = []
        self.subject = ''
        self.letter = ''
        self.attachments = []
        self.boundary = '------==--bound.246224.web52j.yandex.ru'
        self.parse_config()

    def parse_config(self):
        conf_file = self.message_dir + 'config.cfg'
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(conf_file, encoding='utf-8')
        self.server = (config['Server']['Address'], int(config['Server']['Port']))
        self.login = config['From']['Login']
        self.password = config['From']['Password']
        self.receivers = config['To']['Logins'].split(',')
        message = config['Message']
        self.subject = message['Subject']
        self.letter = message['Text']
        self.attachments = message['Attachments'].split(',') if message['Attachments'] else []

    def send_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.server)
            s = ssl.wrap_socket(s)
            print(s.recv(1024).decode())
            login = base64.b64encode(self.login.encode())
            password = base64.b64encode(self.password.encode())
            print(self.send_command(f'EHLO {self.login}'.encode(), s))
            print(self.send_command(b'AUTH LOGIN', s))
            print(self.send_command(login, s))
            print(self.send_command(password, s))
            print(self.send_command(f'MAIL FROM: {self.login}'.encode(), s))
            for receiver in self.receivers:
                receiver = receiver.strip()
                print(self.send_command(f'RCPT TO: {receiver}'.encode(), s))
                print(self.send_command(b'DATA', s))
                print(self.send_command(self.create_message(receiver), s))
            print(self.send_command(b'QUIT', s))

    @staticmethod
    def send_command(str, s):
        str += b'\n'
        s.send(str)
        return s.recv(1024).decode()

    def parse_message(self):
        text = ''
        with open(self.message_dir + self.letter) as letter:
            for line in letter:
                line = line if not line.startswith('.') else '.' + line
                text += line
        return text


    def parse_attachments(self):
        message = b''
        for attachment in self.attachments:
            attachment = attachment.strip()
            file = self.message_dir + attachment
            with open(file, 'rb') as f:
                encoded_attachment = base64.b64encode(f.read())
            mime_type = mimetypes.guess_type(file)[0]
            message += f'{self.boundary}\n' \
                       f'Content-Disposition: attachment;\n\tfilename="{attachment}"\n' \
                       f'Content-Transfer-Encoding: base64\n' \
                       f'Content-Type: {mime_type};\n\tname="{attachment}"\n' \
                       f'\n'.encode() + encoded_attachment + b'\n'
        return message

    def create_message(self, receiver):
        if self.attachments:
            return f'From: {self.login}\n' \
                f'To: {receiver}\n' \
                f'Subject: {self.subject}\n' \
                'MIME-Version: 1.0\n' \
                f'Content-Type: multipart/mixed;\n\tboundary="{self.boundary}"\n\n\n' \
                f'{self.boundary}\n' \
                f'Content-Transfer-Encoding: 8bit\n' \
                f'Content-Type: text/plain; charset=utf-8\n\n' \
                f'{self.parse_message()}\n'.encode() + self.parse_attachments() + \
                f'{self.boundary}--\n.'.encode()
        else:
            return f'From: {self.login}\n' \
                f'To: {receiver}\n' \
                f'Subject: {self.subject}\n' \
                'MIME-Version: 1.0\n' \
                f'Content-Transfer-Encoding: 8bit\n' \
                f'Content-Type: text/plain; charset=utf-8\n\n' \
                f'{self.parse_message()}\n' \
                f'\n.'.encode()


if __name__ == '__main__':
    smtp = SMTP_client()
    smtp.send_message()




