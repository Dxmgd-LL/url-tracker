import os
import json
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
import configparser


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['SMTP']['SMTP_USERNAME'], config['SMTP']['SMTP_PASSWORD'],config['SMTP']['SMTP_SERVER'],config['SMTP']['SMTP_PORT'],config['SMTP']['EMAIL_RECIPIENT'],config['URL']['URL'],config['URL']['DETAIL_URL']

SMTP_USERNAME, SMTP_PASSWORD, SMTP_SERVER,SMTP_PORT ,EMAIL_RECIPIENT,URL,DETAIL_URL= read_config()

print("SMTP_USERNAME= ",SMTP_USERNAME,"SMTP_PASSWORD=", SMTP_PASSWORD, "SMTP_SERVER= ",SMTP_SERVER, "SMTP_PORT=",SMTP_PORT, "EMAIL_RECIPIENT=",EMAIL_RECIPIENT,"URL = ",URL, "DETAIL_URL = ",DETAIL_URL)

def main():
    # Load previous items
    if os.path.exists('prev_items.txt') and os.path.getsize('prev_items.txt') > 0:
        with open('prev_items.txt', 'r') as f:
            prev_items = json.load(f)
    else:
        prev_items = []

    # Scrape new items
    new_items = scrape_items(URL)
    print("new items: ", new_items)

    # Compare with previous items
    new_item_ids = {item['node_id'] for item in new_items}
    prev_item_ids = {item['node_id'] for item in prev_items}
    if new_item_ids != prev_item_ids:
        # Send email notification
        send_email_notification([item for item in new_items if item['node_id'] not in prev_item_ids])

        # Save new items
        with open('prev_items.txt', 'w') as f:
            json.dump(new_items, f)


def scrape_items(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print("Response status code: ", response.status_code)  # Print the status code
    print("Response content: ", response.content)  # Print the response content

    # If the status code is not 200, return the previous items without scraping
    if response.status_code != 200:
        print("Failed to retrieve the webpage. Status code: ", response.status_code)
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    attachment = soup.find('div', class_='attachment attachment-before')
    if attachment:
        attachment.decompose()
    
    items = []

    for article in soup.select('.view-content.view-rows article'):
        node_id = article['data-history-node-id']
        a_tag = article.find('a')
        href = a_tag['href']
        price_field = a_tag.select_one('.price .field__item')
        print("history id: ", node_id)
        print("price field: ", price_field)
        price = price_field.text.strip() if price_field else 'N/A'
        print("price : ", price)
        name = a_tag.select_one('h2 span').text.strip()
        print("name  : ", name)
        post_date = a_tag.select_one('.node__pubdate').text.strip()
        print("post date  : ", post_date)
        items.append({'node_id': node_id, 'name': name, 'price': price, 'href': DETAIL_URL + href, 'post_date': post_date})



    return items

def send_email_notification(items):
    msg = MIMEText(
        "<br>".join(
            f'<a href="{item["href"]}">{item["name"]}</a>: {item["price"]} {item["post_date"]}' for item in items
        ),
        "html"
    )
    msg['Subject'] = f'{len(items)} new items on sale'
    msg['From'] = SMTP_USERNAME
    msg['To'] = EMAIL_RECIPIENT

    s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    print("username in send_email: ",SMTP_USERNAME)
    print("password in send_email: ",SMTP_PASSWORD)
    s.ehlo()
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    s.sendmail(SMTP_USERNAME, [EMAIL_RECIPIENT], msg.as_string())
    s.quit()

if __name__ == "__main__":
    main()
