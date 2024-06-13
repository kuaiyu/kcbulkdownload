#!/usr/bin/python3

import pdb
import time
from datetime import datetime
from pathlib import Path

from selenium.webdriver import Firefox
from selenium.webdriver import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#from selenium.webdriver.chrome.service import Service as ChromeService
#from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

import requests
import multiprocessing
import json
import argparse


class WebClicker:

    def __init__(self):
        self.browser = Firefox(service=FirefoxService(GeckoDriverManager().install()))
        self.action = ActionChains(self.browser)

        self.image_links = []
        self.video_links = []

    def go_to_app_site(self):
        """ Goes to the website
        """
        print(f'Going to KC website')
        self.browser.get("https://classroom.kindercare.com/")

    def x_out_mobile_app_popup(self):
        """
        """
        self._find_elm_by_type(By.CLASS_NAME, "contacts-close-button").click()

    def wait_for_child_choice(self):
        """ This manual step will support multiple children
            it also simplifies this script
        """
        print("manually click on your CHILD's NAME at the top.")
        print('Then click ENTRIES.')
        input('Once you see the url == https://classroom.kindercare.com/accounts/XXX/activities, press enter on this terminal')

    def scrape_all_images(self):
        """ Loops through each entry and saves a list of images
        """

        def get_next_button():
            next_button = None
            try:
                next_button = self._find_elm_by_type(By.CLASS_NAME, "fa-angle-right")
            except:
                pass # We've reached the end. No more next_button's
            return next_button

        while True:

            # This will inherently wait for the next button to be clickable
            # and give us the side effect of loading all the image urls while we wait
            next_button = get_next_button()
            time.sleep(0.1)

            image_fields = self.browser.find_elements(By.CSS_SELECTOR, '[title="Download Image"]')
            self.image_links += [x.get_attribute('href') for x in image_fields]

            video_fields = self.browser.find_elements(By.CSS_SELECTOR, '[title="Download Video"]')
            self.video_links += [x.get_attribute('href') for x in video_fields]

            print(f'scraping {len(image_fields)} images and {len(video_fields)} videos from {self.browser.current_url}')
            if not next_button:
                break

            next_button.click()


    def get_url_output(self):
        """ output the list of urls
        """
        output = {
            'image_links': self.image_links,
            'video_links': self.video_links,
        }

        return output

    def _find_elm_by_type(self, by_type:str, key_name:str, wait_time:int=5):
        return WebDriverWait(self.browser, wait_time).until(EC.presence_of_element_located((by_type, key_name)))


class DownloadHelper:
    def __init__(self, json_data, args):
        self.json_data = json_data
        self.child_name = args.child_name
        self.single_proc = False
        self.single_proc = args.single_proc

        self.IMAGE_DIR = f'{self.child_name}_images/'
        self.VIDEO_DIR = f'{self.child_name}_videos/'

        Path(self.IMAGE_DIR).mkdir(exist_ok=True)
        Path(self.VIDEO_DIR).mkdir(exist_ok=True)


    def _get_file_name(self, dt: datetime, is_video:bool, tag_hash):
        file_date_time = dt.strftime("%Y_%m_%d")

        out_dir = self.IMAGE_DIR
        file_type = '.png'
        if is_video:
            out_dir = self.VIDEO_DIR
            file_type = '.mp4'

        child_str = f'{self.child_name}_' if self.child_name else ''
        file_name = f'{out_dir}{child_str}{file_date_time}_{tag_hash}{file_type}'

        return file_name

    def _split_list(self, my_list, num_parts):
        """
        my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        num_parts = 3
        return -> [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]]
        """
        return [my_list[i * len(my_list) // num_parts: (i + 1) * len(my_list) // num_parts] for i in range(num_parts)]


    def _dl_from_list(self, input_list, is_video):

        for url in input_list:
            response = requests.get(url)

            try:
                dt = datetime.strptime(response.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                print(f'ERROR TRYING TO WRITE {url}. SKipping...')
                continue

            hash_last = response.headers['x-amz-request-id'][-4:]
            file_name = self._get_file_name(dt, is_video, hash_last)

            print(f'writing file to {file_name}')
            with open(file_name, 'wb+') as f:
                f.write(response.content)

    def _download_internal(self, is_video):

        links = 'image_links'
        if is_video:
            links = 'video_links'

        link_list = self.json_data.get(links, [])

        if self.single_proc:
            self._dl_from_list(link_list, is_video)
            return

        num_procs = 4
        outer_list = self._split_list(link_list, num_procs)

        proc_list = []
        for inner_list in outer_list:
            proc = multiprocessing.Process(
                                target=self._dl_from_list,
                                args=(inner_list, is_video)
                                )
            proc_list.append(proc)
            proc.start()

        for proc in proc_list:
            proc.join()


    def download_all(self):
        self._download_internal(is_video=True)
        self._download_internal(is_video=False)


class JsonUser:

    @staticmethod
    def save(output, file_path):
        with open(file_path, 'w') as file:
            json.dump(output, file, indent=4)

    @staticmethod
    def load(file_path):
        """ If you pass in the wrong file path crash and try again with the right one.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data



def get_args():
    parser = argparse.ArgumentParser(
            description="""
    Use a Selenium bot to click all of your child's images/videos ~1000 per year and then scrape
    all image links to a file usually `links.json`. Then download all of these images.
    TODO: tag them with time and gps coordinates.
""",
            formatter_class=argparse.RawTextHelpFormatter
            )

    parser.add_argument('--json_file', dest='json_file',
                        help='cached file of links. This saves 2 minutes of browser clicking',
                        type=str, default=None, required=False)

    parser.add_argument('--child_name', dest='child_name',
                        help='Name of the child. This is a string that will be appended to each image name',
                        type=str, default='',
                        required=True)

    parser.add_argument('--single_proc', dest='single_proc', action='store_true',
                        help='Do not download with multiprocessing. Just use the main Process. This is slower but more debugable',
                        required=False)

    return parser.parse_args()


def main():

    args = get_args()

    if args.json_file:
        links = JsonUser.load(args.json_file)
    else:
        clicker = WebClicker()
        clicker.go_to_app_site()
        clicker.wait_for_child_choice()
        clicker.scrape_all_images()
        links = clicker.get_url_output()
        clicker.browser.close()
        JsonUser.save(links, "links.json")

    DownloadHelper(links, args).download_all()
    print(f'End Script')

if __name__ == "__main__":
    main()
