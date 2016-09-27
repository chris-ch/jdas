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
    "VITAMIN SEA": [
        ('Start here ', 'http://janedavenport.ning.com/group/vitamin-sea '),
        ('Workshop supplies ', 'http://janedavenport.ning.com/group/vitamin-sea/page/vitamin-sea-supplies '),
        ('1 - Tide lInes ', 'http://janedavenport.ning.com/group/vitamin-sea/page/1-tide-lines '),
        ('2 - Sea Spray ', 'http://janedavenport.ning.com/group/vitamin-sea/page/2-sea-spray '),
        ('3 - Taming the wild ocean ', 'http://janedavenport.ning.com/group/vitamin-sea/page/3-taming-the-wild-ocean '),
        ('4  Marie Planktonette ', 'http://janedavenport.ning.com/group/vitamin-sea/page/4-marie-planktonette '),
        ('5. Body of water ', 'http://janedavenport.ning.com/group/vitamin-sea/page/5-body-of-water '),
        ('6. Keep urchin ', 'http://janedavenport.ning.com/group/vitamin-sea/page/6-keep-urchin-up '),
        ('7. Seal of approval ', 'http://janedavenport.ning.com/group/vitamin-sea/page/7-seal-of-approval '),
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
                    logging.info('specific format for url: %s', page_url)
                    node_content = html.find('div', {'class': 'xg_span-12 xg_column'})

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
