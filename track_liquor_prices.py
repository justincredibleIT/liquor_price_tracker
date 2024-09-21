import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

CSV_FILE = "liquor_prices.csv"

def get_liquor_price_from_website(url, liquor_name):
    """
    Scrapes the liquor price from a given URL for a specified liquor name.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    liquor_prices = []
    for item in soup.find_all(text=re.compile(liquor_name, re.IGNORECASE)):
        price = item.find_next('span', {'class': 'price'})  # Adjust based on actual site structure
        if price:
            liquor_prices.append({'liquor_name': liquor_name, 'price': price.text.strip(), 'url': url})
    
    return liquor_prices

def track_prices(websites, liquors):
    all_prices = []
    for url in websites:
        for liquor in liquors:
            prices = get_liquor_price_from_website(url, liquor)
            if prices:
                all_prices.extend(prices)
    
    return pd.DataFrame(all_prices)

def send_email(subject, body, recipient_email):
    sender_email = os.environ.get('EMAIL_SENDER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)  # You can change this depending on your email provider
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, recipient_email, text)
    server.quit()

def check_and_notify(new_prices_df, old_prices_df, recipient_email):
    if new_prices_df.empty:
        return

    if old_prices_df is None:
        new_liquors_available = new_prices_df
    else:
        new_liquors_available = new_prices_df[~new_prices_df['liquor_name'].isin(old_prices_df['liquor_name'])]

    if not new_liquors_available.empty:
        message = f"The following liquors are now available:\n{new_liquors_available.to_string(index=False)}"
        send_email("Liquor Availability Update", message, recipient_email)

if __name__ == '__main__':
    websites = [
        'https://example-liquor-store.com',
        'https://another-liquor-shop.com'
    ]
    
    liquors = ['Jack Daniels', 'Johnnie Walker', 'Patron']

    new_prices_df = track_prices(websites, liquors)

    try:
        old_prices_df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        old_prices_df = None

    if not new_prices_df.empty:
        new_prices_df.to_csv(CSV_FILE, index=False)

    # Check and notify
    recipient_email = os.environ.get('RECIPIENT_EMAIL')
    check_and_notify(new_prices_df, old_prices_df, recipient_email)
