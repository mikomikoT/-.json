from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# アクセストークンを入力
access_token = 'your-access_token'
credentials = Credentials(token=access_token)

#Gmail API clientの作成
service = build('gmail', 'v1', credentials=credentials)


#gmail APIを使用しファイルをダウンロードする

import base64
import os
from googleapiclient.http import MediaFileUpload

download_directory = '/content/downloads'


"""指定されたメッセージからPNG添付ファイルをダウンロード"""
def download_attachments(service, user_id, msg_id, store_dir):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    parts = message['payload'].get('parts', [])
    for part in parts:
        if 'filename' in part and part['filename'].endswith('.png'):
            if 'data' in part['body']:
                data = part['body']['data']
            else:
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
                data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            path = os.path.join(store_dir, part['filename'])

            if not os.path.exists(store_dir):
                os.makedirs(store_dir)
            with open(path, "wb") as f:
                f.write(file_data)
            print(f"Downloaded {part['filename']} to {path}")

def get_messages_with_attachments(service, user_id):
    """ユーザーのメッセージから添付ファイルを含むメッセージを取得"""
    response = service.users().messages().list(userId=user_id, labelIds=['INBOX'], q="has:attachment").execute()
    messages = response.get('messages', [])
    return messages[:10]  # 最新10件のメッセージからファイルを抽出

download_directory = '/content/downloads'
messages = get_messages_with_attachments(service, 'me')

for message in messages:
    download_attachments(service, 'me', message['id'], download_directory)






# gemini1.5proによってダウンロードファイルを解析
import os
import google.generativeai as genai
GOOGLE_API_KEY="your-GOOGLE_API_KEY"
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-pro-latest')

# ファイルのアップロード
sample_file = genai.upload_file(path="/content/downloads/image.png", display_name="Sample bill")

# モデルによる内容生成
response = model.generate_content(["この請求書の概要をJSON形式で出力してください", sample_file])
print(response.text)

# テキストをJSON形式に変換
import json

json_data = {'text': response.text}

# JSONファイルに書き込むパスを指定
json_file_name = '/app/data/bill.json'

# ディレクトリが存在しない場合は作成
os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

# JSONファイルに書き込み
with open(json_file_name, 'w') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=4)  # UTF-8とインデントを設定

print(f"Data written to {json_file_name}")




#gmail APIを使用し、作成したjsonファイルを転送
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
from googleapiclient.discovery import build

def create_message_with_attachment(sender, to, subject, message_text, file):
    """Create a message for an email with an attachment."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    
    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(file)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)

   
    with open(file, 'rb') as fp:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        encoders.encode_base64(msg)

    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
        return message
    except Exception as error:
        print('An error occurred: %s' % error)

credentials = Credentials(token=access_token)

service = build('gmail', 'v1', credentials=credentials)

# メールの作成
sender_email = '~~@gmail.com'
recipient_email = '~~@gmail.com'
subject = 'Invoice is ready'
body_text = 'こちら請求書のjsonファイルとなります。'
file_path = '/app/data/bill.json'  

# メッセージを送信
message = create_message_with_attachment(sender_email, recipient_email, subject, body_text, file_path)
send_message(service, 'me', message)
