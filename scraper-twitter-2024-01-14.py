import os
import sys
import re
import time
import bs4
import requests
import hashlib
import random
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import *

from datetime import datetime
from PIL import Image
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(),
        #logging.FileHandler('log.log'),
    ]
)

page_down_step = (2, 5,)
page_down_interval = (1.0, 3.0,)
image_interval = (2.0, 4.0,)
headless = False
cookies = True
datetime_format = '%Y-%m-%d-%H-%M-%S%z'


root_dir = '/mnt/d/Dropbox/twitter' #os.path.join(os.getcwd(), 'twitter')
os.makedirs(root_dir, exist_ok=True)

accounts = {
    # 'test': 'test',
    # 'met_greekroman': 'MET, Greek - Roman',
    # 'met_costume': 'MET, Costume',
    # 'cma_greekroman': 'CMA, Greek - Roman', 
    # 'cma_islamic': 'CMA, Islamic',

    # 'artistvaro': 'Varo, Remedios',
    # 'artist_dali': 'Dali, Salvador',
    # 'artistmagritte': 'Magritte, Rene',
    # 'pablocubist': 'Picasso, Pablo',
    # 'artistklee': 'Klee, Paul',
    # 'artistmonet': 'Monet, Oscar-Claude',
    # 'cezanneart': 'Cezanne, Paul',
    # 'artfridakahlo': 'Kahlo, Frida',
    # 'vangoghartist': 'Van Gogh, Vincent',
    # 'boschbot': 'Bosch, Hieronymus',
    # 'artistrembrandt': 'Rembrandt, Van Rijn',
    # 'artcaravaggio': 'Caravaggio, Michelangelo',

    # '0zmnds': 'Ozymandias',
    # 'WeirdMedieval': 'Weird Medieval Guys',
    # 'yesterdaysprint': 'Yesterdays Print',
    # 'olgatuleninova': 'OlgaTuleninova',
    # 'MenschOhneMusil': 'Mordecai',


    #'artistturner': 'Turner, William',
    #'art_delacroix': 'Delacroix, Eugène',
    'artistbruegel': 'Bruegel, Pieter',
    #'BruegelBot': 'Bruegel, Pieter',
    #'artistboldini': 'Boldini, Giovanni',
    #'artistmanet': 'Manet, Edouard',
    # '': '',
    # '': '',
    # '': '',
    # '': '',
    # '': '',
}

def comment_binary(data, comment, format='JPEG'):
    with Image.open(BytesIO(data)) as img:
        img.info['comment'] = comment
        stream = BytesIO()
        img.save(stream, format='JPEG')
        return stream.getvalue()


def comment_image(image_path, comment):
    with Image.open(image_path) as img:
        img.info['comment'] = comment
        img.save(image_path)

def clean_text(text):
    return re.compile(
        "["
        "\\/<>:\"\'|?*\."
        u"\U00010000-\U0001F5FF"  # expansive range
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE
    ).sub('', text).strip('. ')

def save_html(element, filename):
    if not filename.endswith('.html'):
        filename += '.html'
    
    with open(filename, 'w') as f:
        f.write(bs4.BeautifulSoup(element.get_attribute('outerHTML'), 'html.parser').prettify())

def get_hash(data, algorithm=hashlib.sha256):
    hash = algorithm if isinstance(algorithm, hashlib._hashlib.HASH) else algorithm()
    hash.update(data)
    return hash.hexdigest()

def print_iterable(iterable, startlines:int=2, endlines:int=2):
    logging.info((startlines - 1) * '\n')

    if isinstance(iterable, dict):
        for key,val in iterable.items():
            logging.info(f'{str(key)}: {str(val)}')
    
    elif isinstance(iterable, (list, tuple, set,)):
        for key in iterable:
            logging.info(str(key))

    logging.info((endlines - 1) * '\n')



start = time.perf_counter()
driver_options = webdriver.ChromeOptions()

if cookies:
    driver_options.add_argument("user-data-dir=selenium")

if headless:
    driver_options.add_argument('--headless')
 

with webdriver.Chrome(options=driver_options) as driver:
    first = True
    dirs = set(item for item in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, item)))

    for account, fullname in accounts.items():
        start_account = time.perf_counter()
        url = f'https://twitter.com/{account}'
        logging.info(f'Getting {account}...')
        driver.get(url)

        if first and not cookies:
            logging.info('Waiting for prompts...')
            time.sleep(10)

            if driver.find_elements(By.XPATH, './/input[@autocomplete=\'username\']',):
                raise ValueError('Sign in prompt!')
            
            logging.info('No sign in prompt.')
            button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button']//span[text()='Not now']"))
            )

            button.click()
            logging.info('Clicked on notifications prompt.')
            first = False

        time.sleep(10)
        #name = clean_text(driver.find_element(By.XPATH, '//span[normalize-space() and ancestor::h2]').text)
        name = clean_text(driver.find_element(By.XPATH, '//div[@data-testid=\'UserName\']//span[text()]').text)
        current_dir = os.path.join(root_dir, name)
        os.makedirs(current_dir, exist_ok=True)
        logging.info(name)

        account_data = f'>>> {account}: {name}\n'
        #html = driver.find_element(By.TAG_NAME, 'html')
        #save_html(html, os.path.join(current_dir, name))
        #doctype = driver.execute_script('return new XMLSerializer().serializeToString(document.doctype);')

        banner = {
            '_photo': re.sub(
                '(_\d{3,4}x\d{3,4})',
                '',
                driver\
                    .find_element(
                        By.XPATH,
                        f'//img[ancestor::a[@href=\'/{account}/photo\']]',
                    )\
                    .get_attribute('src')
            ),
            'header': re.sub(
                '(/\d{3,4}x\d{3,4})',
                '',
                driver\
                    .find_element(
                        By.XPATH,
                        f'//img[ancestor::a[@href=\'/{account}/header_photo\']]',
                    )\
                    .get_attribute('src')
            ),  
        }

        image_extension = 'jpg'

        for image_file, image_url in banner.items():
            time.sleep(random.uniform(*image_interval))
            response = requests.get(image_url)
            logging.info(image_url)

            if response.status_code != 200:
                logging.info(f'{image_file}: Status {response.status_code}')
                continue

            with open(os.path.join(current_dir, f'@{name}_{image_file}.{image_extension}'), 'wb') as f:
                f.write(response.content)

        logging.info(f'>>> {name}')
        
        previous_set = set()
        current_set = set()
        hashes = set()
        counter = 0

        for image in os.listdir(current_dir):
            path = os.path.join(current_dir, image)

            if os.path.isfile(path) and not image.startswith('@'):
                with open(path, 'rb') as f:
                    hashes.add(get_hash(f.read()))

        logging.info(f'{len(hashes)} hashes.')

        time.sleep(5)

        while(True):
            previous_set = current_set
            counter += 1
            articles = driver.find_elements(By.XPATH, "//article[@aria-labelledby]")
            current_set = set(article.get_attribute('aria-labelledby') for article in articles)
            intersection = current_set.intersection(previous_set)
            difference = current_set.difference(previous_set)

            print_iterable({
                name: counter,
                'previous': len(previous_set),
                'current': len(current_set),
                'intersection': len(intersection),
                'difference': len(difference),
            })

            if previous_set and not intersection:
                ValueError('Scrolled too far.')

            if not current_set or (previous_set and not difference):
                filecount = len(list(filter(
                    lambda f: not f.startswith('@'),
                    os.listdir(current_dir),
                )))

                if not filecount:
                    os.rmdir(current_dir)

                logging.info(f'{name} DONE ({filecount})! {time.perf_counter() - start_account:.0f}s\n\n')
                break

            for article in articles:
                if article.get_attribute('aria-labelledby') in previous_set:
                    continue
                
                if not article.get_elements(By.XPATH, f'.//a[@href=\'/  {account}\']//span[text()=\'@{account}\']',):
                    logging.info('REPOST!')
                
                article_datetime = datetime.fromisoformat(
                    re.sub(
                        'Z$',
                        '+00:00',
                        article.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
                    )
                ).strftime(datetime_format)

                if article.find_elements(
                    By.XPATH,
                    './/span[contains(text(), \'reposted\')]',
                ):
                    repost_user = article.find_element(
                        By.XPATH,
                        './/span[starts-with(text(), \'@\')]',
                    ).text
                    logging.info(f'REPOST {repost_user}')
                    continue
                    
                if article.find_elements(
                    By.XPATH,
                    './/div[@dir=\'ltr\']/span[text()=\'AD\']',
                ):
                    ad_user = article.find_element(
                        By.XPATH,
                        './/div[@data-testid=\'User-Name\']//span[starts-with(text(), \'@\')]',
                    ).text
                    logging.info(f'AD {ad_user}')
                    continue
                
                article_text = re.sub(
                    '\s+',
                    ' ',
                    ' '.join(
                        p.text.strip()
                        for p in article.find_elements(
                            By.XPATH,
                            './/div[@data-testid=\'tweetText\']/span[text()]',
                        )
                    ).strip().replace('\n', ' ').replace('\t', ' '),
                )

                logging.info(f'\nTEXT: {article_text}')

                images = list(filter(
                    lambda s: 'profile_images' not in s and '/emoji/' not in s,
                    [e.get_attribute('src') for e in article.find_elements(
                        By.XPATH,
                        './/div[@data-testid=\'tweetPhoto\']/img'
                    )],
                ))
                
                if not images:
                    continue
                
                account_data += f'\n\t{article_datetime}: {article_text}\n'

                for index, source in enumerate(images, 1):                    
                    image_url = re.sub('name=(.+)$', 'name=orig', source)

                    try:
                        selector = source.endswith('.svg')

                        if selector:
                            image_format = source.split('.')[-1]
                            image_id = source.split('/')[-1][:source.rfind('.')]     
                        else:
                            image_format = re.findall('format=([^&]*)',  source)[-1]
                            image_id = re.findall('/([^/]*)\?',  source)[-1]
                    except IndexError:
                        logging.info(f'IndexError: {source}')
                        continue
                    
                    image_suffix = f'_{index}' if len(images) > 1 else ''
                    image_title = article_text[: 100] if article_text else image_id
                    image_filename = f"{clean_text(f'{image_title}{image_suffix}')}.{image_format}"
                    image_path = os.path.join(current_dir, image_filename)
                    
                    if os.path.isfile(image_path):
                        image_filename = f"{clean_text(f'{image_title}{image_suffix}_{image_id}')}.{image_format}"
                        image_path = os.path.join(current_dir, image_filename)
                    
                    account_data += f'\t\t{image_filename}\n'
                    
                    time.sleep(random.uniform(1.0, 2.0))
                    response = requests.get(image_url)
                    
                    if response.status_code != 200:
                        logging.info(f'{image_id}: Status {response.status_code}')
                        continue
                    
                    data = response.content

                    #if article_text:
                    #    data = comment_binary(data, article_text)

                    hash = get_hash(data)
                    
                    if hash in hashes:
                        logging.info(f'{image_id}: -')
                        continue
                    
                    hashes.add(hash)                      

                    with open(image_path, 'wb') as f:
                        f.write(data)

                    # if article_text:
                    #     comment_image(image_path, article_text)
                        
                    logging.info(f'{image_id}: {image_filename}')

            for _ in range(random.randint(*page_down_step)):
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                time.sleep(random.uniform(*page_down_interval))

        with open(os.path.join(current_dir, f'@{account}.txt'), 'w') as f:
            f.write(account_data)

    logging.info(f'ALL DONE in {time.perf_counter() - start:.0f}s.')
    time.sleep(60)
    driver.quit()
