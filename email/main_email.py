import imaplib
import smtplib
import os
import email

from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate


class MailReceiving():
    '''
    Подключение IMAP4_SSL для получения писем
    '''
    def __init__(self, host: str, port: int, user: str, passwd: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd


    @property
    def connect(self):
        '''
        Осуществляем подключение к почтовому серверу
        '''
        server = imaplib.IMAP4_SSL(self.host, self.port)
        server.login(self.user, self.passwd)
        return server


    def search_inbox_mail(self, pattern='(UNSEEN)') -> list:
        '''
        Функция подключается к почте и забирает все письма по признаку
        pattern - признак по которому будем искать письма
        'ALL' - все письма из папки входящих
        '(UNSEEN)' - все непрочитанные письма

        Возвращает список с кортежами (от кого, дата-время, сообщение)
        '''
        result = []

        server = self.connect
        server.select("inbox")
        status, mes = server.search(None, pattern)
        if status == 'OK': # Проверяем статус запроса
            for num in mes[0].split(): # Получаем список номеров писем
                typ, data = server.fetch(num, '(RFC822)') # Парсим письмо
                original = email.message_from_bytes(data[0][1]) # Получаем нормальное письмо
                result.append((
                    original['Envelope-From'], # Получаем отправителя
                    original['Date'],          # Получаем дату отправки
                    original.get_payload()     # Получаем сообщение
                ))
            return result


class MailSend():
    def __init__(self, host: str, port: int, user: str, passwd: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd


    @property
    def connect(self):
        '''
        Осуществляем подключение к почтовому серверу
        '''
        server = smtplib.SMTP(self.host, self.port)
        server.starttls()
        server.ehlo()
        server.login(self.user, self.passwd)
        return server

    @property
    def create_email(self):
        # Создаем маил!
        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["Date"] = formatdate(localtime=True)
        return msg

    def send_email(self, msg, to_email):
        # Отправляем собранное сообщение
        try:
            server = self.connect
            server.sendmail(self.user, to_email, msg.as_string())
        except smtplib.SMTPException as err:
            print('Что - то пошло не так...', err)
            return

        server.quit()
        return True

    def send_message(self, to_email: str, message, subject='Hi'):
        '''
        На вход  емайл на который отправляем сообщение, сообщение, тему письма
        Составляем письмо и отправляем
        На выход булевое значение с результатом отправки
        '''
        msg = self.create_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message))

        return self.send_email(msg, to_email)


    def send_file(self, to_email: str, file_path: str, message='', subject='Hi'):
        '''
        На вход  емайл на который отправляем файл, абсолютный путь до файла, сообщение, тему письма
        Составляем письмо и отправляем
        На выход булевое значение с результатом отправки
        '''

        # Создаем сообщение
        msg = self.create_email
        msg["Subject"] = subject

        if message:
            msg.attach(MIMEText(message))

        attachment = MIMEBase('application', "octet-stream") # Загружаем файл
        file_name = os.path.basename(file_path) # Получаем имя файла
        header = 'Content-Disposition', f'attachment; filename="{file_name}"'
        try:
            with open(file_path, "rb") as fh:
                data = fh.read()
            attachment.set_payload(data)
            encoders.encode_base64(attachment)
            attachment.add_header(*header)
            msg.attach(attachment)
        except IOError:
            print(f"Ошибка при открытии файла вложения {file_name}")

        return self.send_email(msg, to_email)
