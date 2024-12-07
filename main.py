import requests as req
import parsel as sel
import datetime as dt
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

URL = 'https://www.ifspcaraguatatuba.edu.br/noticias'
load_dotenv()

page = req.get(URL)
queryble = sel.Selector(page.text)
news_date = dt.datetime.now() - dt.timedelta(days=1)
data = {'values': []}
items = queryble.xpath('.//form[contains(@id, "adminForm")]/div[contains(@class, "tile-list-1")]/div[contains(@class,"tileItem")]')
for item in items:
    _data = {}
    _data['date'] = item.xpath('.//div[contains(@class,"tileInfo")]/ul/li[4]/text()').get().strip()
    if _data['date'] == news_date.strftime('%d/%m/%y'):
        _data['author'] = item.xpath('.//div[contains(@class,"tileInfo")]/ul/li[1]/text()').get().replace('Escrito por ', '')
        _data['category'] = item.xpath('.//div[contains(@class, "tileContent")]/span[contains(@class,"subtitle")]/text()').get().capitalize()
        _data['abstract'] = item.xpath('.//div[contains(@class,"tileContent")]/h2/a/text()').get()
        _data['link'] = URL.replace('/noticias',item.xpath('.//div[contains(@class,"tileContent")]/h2/a/@href').get())
        _data['description'] = item.xpath('.//div[contains(@class,"tileContent")]/span[contains(@class,"description")]/p/text()').get()
        data['values'].append(_data)
    elif dt.datetime.strptime(_data['date'], '%d/%m/%y').date() < news_date.date():
        break

env = Environment(loader=FileSystemLoader('./templates'))
template = env.get_template('index.html')
html_content = template.render(data)

is_test = True

if is_test:
    with open("email_preview.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    exit()

recipients = os.getenv('RECIPIENTS').split(',')
msg = MIMEMultipart("related")
msg["Subject"] = "IFSPCAR Notícias"
msg["To"] = ", ".join(recipients)
msg["From"] = os.getenv('SENDER')
msg.attach(MIMEText(html_content, "html"))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(os.getenv('SENDER'), os.getenv("PSWD_APP"))
        smtp_server.sendmail(os.getenv('SENDER'), recipients, msg.as_string())
except Exception as e:
    print(f"Error sending email: {e}")
