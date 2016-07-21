"""
Tasks:
- All images downloaded to local folder
- Update all images path to /wp-content/uploads/2016/07/*
- All image extensions .jpeg --> .jpg
- Links "www.instituteofcute.com/*": update to "/product/*"
- Links "api.ning.com.../*" (images): update to /wp-content/uploads/2016/07/*
- Links "janedavenport.ning.com/*": update to /product/*

"""
import argparse
import json
import logging
import os

import requests
from bs4 import BeautifulSoup
import xlsxwriter
import requests_cache

_LOGIN_URL = 'http://janedavenport.ning.com/main/authorization/doSignIn?target=http%3A%2F%2Fjanedavenport.ning.com%2F'
_IMAGE_URL_DEST = '/wp-content/uploads/2016/07'
_IMG_DIRECTORY_PREFIX = 'images'
_IOC_TAG = 'instituteofcute.com'
_API_NING_TAG = 'api.ning.com:80/files'
_JD_NING_TAG = 'janedavenport.ning.com'

pages_set = {
    "DRAW HAPPY": [
        ("Overview", "http://janedavenport.ning.com/group/draw-happy/page/start-here-welcome"),

        ("Supplies List", "http://janedavenport.ning.com/group/draw-happy/page/supply-list"),

        ("1: Start an Art Journal!", "http://janedavenport.ning.com/group/draw-happy/page/art-journaling"),

        ("2: Finding your 'Draw Happy' Tools", "http://janedavenport.ning.com/group/draw-happy/page/5-draw-happy-tools"),

        ("3. If you can doodle, you can draw.",
         "http://janedavenport.ning.com/group/draw-happy/page/you-can-already-draw-doodling"),

        ("4. 'Draw Happy' Faces", "http://janedavenport.ning.com/group/draw-happy/page/3-draw-what-you-love"),

        ("5. Putting it all together!", "http://janedavenport.ning.com/group/draw-happy/page/putting-it-all-together"),
    ],

    "SUPPLIES ME": [
        ("Overview", "http://janedavenport.ning.com/group/supplies-me/page/welcome-start-here"),

        ("1. Journals", "http://janedavenport.ning.com/group/supplies-me/page/1-journals"),

        ("2. Gesso & Matte Medium", "http://janedavenport.ning.com/group/supplies-me/page/journals-gesso"),

        ("3. Pen & Pencil", "http://janedavenport.ning.com/group/supplies-me/page/3-pen-and-pencil"),

        ("4. Coloured Pencils", "http://janedavenport.ning.com/group/supplies-me/page/4pencils"),

        ("5. Pastels & Crayons", "http://janedavenport.ning.com/group/supplies-me/page/pastels-crayons"),

        ("6. Ink", "http://janedavenport.ning.com/group/supplies-me/page/6-ink"),

        ("7. Acrylic Paint", "http://janedavenport.ning.com/group/supplies-me/page/7-acrylicpaint"),

        ("8. Markers", "http://janedavenport.ning.com/group/supplies-me/page/7-markers"),

        ("9. Watercolours", "http://janedavenport.ning.com/group/supplies-me/page/9-watercolour"),

    ],

    "BEAUTIFUL FACES": [
        ("Overview", "http://janedavenport.ning.com/group/beautiful-faces/page/start-here-welcome"),

        ("Supplies list", "http://janedavenport.ning.com/group/beautiful-faces/page/supplies-list"),

        ("1: Starting Small", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-1-starting-small"),

        ("2 : Grand Scale", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-2-grand-scale"),

        ("3: Shading", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-3-shading"),

        ("4 : Hair", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-4-hair"),

        ("5: Layers", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-5-watercolour-layers"),

        ("6: Collage & colour", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-6-collage-colour"),

        ("7: Turned Faces & Adding Movement!",
         "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-7-turnedfaces"),

        ("8: Painterly & Burnished", "http://janedavenport.ning.com/group/beautiful-faces/page/lesson-8"),
    ],

    "EXPRESS YOURSELF": [

        ("Overview", "http://janedavenport.ning.com/group/express-yourself/page/1-welcome-emotion-map-and-warm-up"),

        ("Supplies List", "http://janedavenport.ning.com/group/express-yourself/page/supplies-list-express-yourself"),

        ("1: Expressions Gallery", "http://janedavenport.ning.com/group/express-yourself/page/2-expressions-gallery"),

        ("2: Pouts and Puckers", "http://janedavenport.ning.com/group/express-yourself/page/lesson-3-pouts-and-puckers"),

        ("3. Expressive Eyes", "http://janedavenport.ning.com/group/express-yourself/page/4-expressive-eyes"),

        ("4. Growing Up", "http://janedavenport.ning.com/group/express-yourself/page/4-expressive-eyes"),

        ("5. Tilted Down Expressions", "http://janedavenport.ning.com/group/express-yourself/page/5-growing-up"),

        ("6. Subtle Changes", "http://janedavenport.ning.com/group/express-yourself/page/7-subtle-changes"),

        ("7: Chin Up", "http://janedavenport.ning.com/group/express-yourself/page/8-chin-up"),

        ("8. Laughing", "http://janedavenport.ning.com/group/express-yourself/page/9-laughing"),
    ],

    "I HEART DRAWING": [

        ("Overview", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/welcome-start-here"),

        ("1: Faces", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-lesson-1-faces"),

        ("2 Unstumpification", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-lesson-2-unstumpify"),

        ("3 Sweet Hearts", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-lesson-3-sweet-hearts"),

        ("4 Heart Moves", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-4-heart-moves"),

        ("5: Dress You Up", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-lesson-5-dress-you-up"),

        ("6 Hands and Feet", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-6-hands-and-feet"),

        ("7:Legs & Eggs", "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-7-legs-eggs"),

        ("8: Backs and Bottoms!",
         "http://janedavenport.ning.com/group/i-heart-drawing-new/page/ihd-8-backs-and-bottoms"),

    ],

    "Joynal": [

        ("Overview", "http://janedavenport.ning.com/group/joynal"),

        ("Supplies", "http://janedavenport.ning.com/group/joynal/page/supplies-list"),

        ("1: Creating a JOYnal", "http://janedavenport.ning.com/group/joynal/page/1-creating-a-joynal"),

        ("2: Creating a Story Book", "http://janedavenport.ning.com/group/joynal/page/1-creating-a-story-book"),

        ("3: Warm Up Drawings", "http://janedavenport.ning.com/group/joynal/page/1c-warm-up-drawings"),

        ("4: Flower Fairies", "http://janedavenport.ning.com/group/joynal/page/2-flower-fairies"),

        ("5: Wingspiration", "http://janedavenport.ning.com/group/joynal/page/3-wingspiration"),

        ("6: Making A Muse", "http://janedavenport.ning.com/group/joynal/page/4-making-a-muse"),

        ("7. Elegant Elves", "http://janedavenport.ning.com/group/joynal/page/5-elegant-elves"),

        ("8. Fairytale Heroines", "http://janedavenport.ning.com/group/joynal/page/6-fairytale-heroines"),

        ("9. Naughty Pixies", "http://janedavenport.ning.com/group/joynal/page/7-naughty-pixies"),

    ],

    "Wonderland": [

        ("Overview", "http://janedavenport.ning.com/group/wonderland"),

        ("Wonderland Supplies", "http://janedavenport.ning.com/group/wonderland/page/wonderland-supplies"),

        ("Alice History & Resources", "http://janedavenport.ning.com/group/wonderland/page/synopsis-and-history"),

        ("1- Painting Roses", "http://janedavenport.ning.com/group/wonderland/page/1-painting-roses"),

        ("2. Tumbling Alice", "http://janedavenport.ning.com/group/wonderland/page/2-tumbling-alice"),

        ("3. The Small Hero", "http://janedavenport.ning.com/group/wonderland/page/3-the-small-hero"),

        ("4. Learn from the Flowers", "http://janedavenport.ning.com/group/wonderland/page/learn-from-flowers"),

        ("5. The Vanishing Cheshire Cat",
         "http://janedavenport.ning.com/group/wonderland/page/5-the-vanishing-cheshire-cat"),

        ("6. A Mad Tea-Party", "http://janedavenport.ning.com/group/wonderland/page/6-a-mad-tea-party"),

        ("7 . Large Alice", "http://janedavenport.ning.com/group/wonderland/page/7-large-alice"),

    ],

    "PRINT AND SCAN": [

        ("Overview", "http://janedavenport.ning.com/group/print-scan"),

        ("P&S : Supplies", "http://janedavenport.ning.com/group/print-scan/page/p-s-supplies"),

        ("P&S Reference", "http://janedavenport.ning.com/group/print-scan/page/p-s-definitions"),

        ("1. P&S Hello PhotoShop!", "http://janedavenport.ning.com/group/print-scan/page/p-s-getting-set-up"),

        ("2. Scan", "http://janedavenport.ning.com/group/print-scan/page/ps-module-1-scan-part-1"),

        ("3 Scan Challenges", "http://janedavenport.ning.com/group/print-scan/page/ps-1b-scan-challenges"),

        ("4 Photo", "http://janedavenport.ning.com/group/print-scan/page/ps-2-photo"),

        ("5 Enhance", "http://janedavenport.ning.com/group/print-scan/page/ps-3-enhance"),

        ("6 Print", "http://janedavenport.ning.com/group/print-scan/page/ps4-print"),

        ("7 Package", "http://janedavenport.ning.com/group/print-scan/page/ps5-package"),

    ],

    "MISQUOTE": [

        ("Overview", "http://janedavenport.ning.com/group/miss-quoted"),

        ("MQ Supplies", "http://janedavenport.ning.com/group/miss-quoted/page/mq-supplies"),

        ("1 Artphabet!", "http://janedavenport.ning.com/group/miss-quoted/page/mq-artphabet"),

        ("2 Think in Ink!", "http://janedavenport.ning.com/group/miss-quoted/page/mq-think-in-ink"),

        ("3 Art Speak", "http://janedavenport.ning.com/group/miss-quoted/page/mq-art-speak"),

        ("4 Chatty Letters", "http://janedavenport.ning.com/group/miss-quoted/page/mq-chatty-letters"),

    ],

}


def save_sheet(page_name, workbook, node_content):
    output = node_content.prettify()
    worksheet = workbook.add_worksheet(page_name[:31])  # worksheet name cannot exceed 31 characters
    for count, line in enumerate(output.split('\n')):
        worksheet.write(count, 0, line)


def save_images(image_urls, browsing):
    if not os.path.exists(_IMG_DIRECTORY_PREFIX):
        os.makedirs(_IMG_DIRECTORY_PREFIX)

    for image_name in image_urls:
        image_url = image_urls[image_name]
        image_file_name = os.path.sep.join([_IMG_DIRECTORY_PREFIX, image_name])
        target_image_file_name = image_file_name
        if image_file_name.upper().endswith('.JPEG'):
            target_image_file_name = image_file_name[:-4] + 'jpg'

        if not os.path.isfile(target_image_file_name):
            image = browsing.get(image_url, stream=True)
            if image.status_code == 200:
                with open(target_image_file_name, 'wb') as image_file:
                    for chunk in image:
                        image_file.write(chunk)


def update_jpg(image_name):
    if '.jpeg' in image_name:
        return image_name.replace('.jpeg', '.jpg')

    if '.JPEG' in image_name:
        return image_name.replace('.JPEG', '.jpg')
    return image_name


def cleanup_tab_name(name):
    clean_name = name.replace('!', '').replace(':', '').replace('!', '')
    return clean_name

def main(args):
    with open('sensitive.js') as sensitive_file:
        payload = json.load(sensitive_file)

    for page_title in pages_set:
        workbook = xlsxwriter.Workbook('%s.xlsx' % page_title)
        with requests.Session() as browsing:
            browsing.post(_LOGIN_URL, data=payload)
            pages = pages_set[page_title]
            for page_name, page_url in pages:
                logging.debug('browsing url: %s', page_url)
                page = browsing.get(page_url)
                html = BeautifulSoup(page.text, 'html.parser')
                node_content = html.find(id='page-content')
                if not node_content:
                    node_content = html.find(id='xg_body')

                if not node_content:
                    logging.error('no data found for url: %s', page_url)
                    continue
                    
                image_tags = node_content.find_all('img')
                image_urls = {image_tag['src'].split('/')[-1].split('?')[0]: image_tag['src'] for image_tag in image_tags}
                save_images(image_urls, browsing)

                for image_tag in image_tags:
                    image_name = image_tag['src'].split('/')[-1]
                    image_name = update_jpg(image_name)
                    target = _IMAGE_URL_DEST + '/' + image_name
                    image_tag['src'] = target

                address_tags = node_content.find_all('a')
                for address_tag in address_tags:
                    if not address_tag.has_attr('href'):
                        logging.warning('unable to process address: %s from %s', address_tag, page_url)
                        continue

                    if _IOC_TAG in address_tag['href']:
                        target = address_tag['href'].split(_IOC_TAG)[-1]
                        address_tag['href'] = '/product' + target

                    if _JD_NING_TAG in address_tag['href']:
                        target = address_tag['href'].split('/')[-1]
                        address_tag['href'] = '/product/' + target

                href_tags = node_content.find_all(lambda tag: tag.has_attr('href'))
                for href_tag in href_tags:
                    if _API_NING_TAG in href_tag['href']:
                        image_name = href_tag['href'].split('/')[-1]
                        image_name = update_jpg(image_name)
                        href_tag['href'] = _IMAGE_URL_DEST + '/' + image_name

                save_sheet(cleanup_tab_name(page_name), workbook, node_content)

        workbook.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    file_handler = logging.FileHandler('jdas.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    parser = argparse.ArgumentParser(description='Grabbing web pages.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    args = parser.parse_args()

    requests_cache.install_cache('jdas_cache')
    main(args)
