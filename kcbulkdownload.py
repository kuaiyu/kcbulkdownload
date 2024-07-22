#!/usr/bin/python3

import pdb
import time
import os
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


class LinkCacheUser:

    VIDEO_LINKS = 'video_links'
    IMAGE_LINKS = 'image_links'

    def __init__(self, file_path):
        self.file_path = file_path
        self.cached_links_dict = self.load_json()
        self.existing_urls_dict = self.create_links_dict()

    def write_json(self):
        """
        Write combined_links to json
        """
        with open(self.file_path, 'w') as file:
            json.dump(self.combined_links, file, indent=4)

    def load_json(self):
        """ If you pass in the wrong file path crash and try again with the right one.
        """
        if not self.file_path:
            return {}

        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return data

    def create_links_dict(self):
        """ used for optimized searching if an image/video url exists
        """
        existing_urls = {}
        for _, urls in self.cached_links_dict.items():
            assert(type(urls) == list)
            for full_url in urls:
                # full_url: https://himama-kce.s3.amazonaws.com/uploads/activity_file/image/asdf/big_asdflks.jpeg?X-Amz-Expires=129600&X...
                # prefix:   https://himama-kce.s3.amazonaws.com/uploads/activity_file/image/asdf/big_asdflks.jpeg
                prefix = full_url.split('?')[0]
                existing_urls[prefix] = True

        return existing_urls

    def does_new_url_exist_in_cache(self, new_url:str):
        """ check if new_url exists in the cache
        """
        new_url_prefix = new_url.split('?')[0]
        if new_url_prefix in self.existing_urls_dict:
            return True

    def save_links(self, image_links:list, video_links:list):

        self.new_output = {
            self.IMAGE_LINKS: image_links,
            self.VIDEO_LINKS: video_links,
        }

        self.combined_links = {
            self.IMAGE_LINKS : self.cached_links_dict[self.IMAGE_LINKS] + image_links,
            self.VIDEO_LINKS : self.cached_links_dict[self.VIDEO_LINKS] + video_links,
        }

    def get_new_links(self, is_video:bool) -> list:
        key = self.VIDEO_LINKS if is_video else self.IMAGE_LINKS
        return self.new_output[key]


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

    def go_to_direct_url(self, url:str):
        """ Goes to the website
        """
        print(f'Going to direct URL: {url}')
        self.browser.get(url)

    def fill_out_credentials(self, args, do_wait:bool):

        if not args.user or not args.password:
            msg = "Please fillout user and password manually"
            action = input if do_wait else print
            action(msg)
            return

        self._find_elm_by_type(By.ID, "user_login").send_keys(args.user)
        self._find_elm_by_type(By.ID, "user_password").send_keys(args.password)
        self._find_elm_by_type(By.NAME, "commit").click()


    def scrape_all_images(self, links:LinkCacheUser):
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
            new_image_links = [x.get_attribute('href') for x in image_fields]
            self.image_links += new_image_links

            video_fields = self.browser.find_elements(By.CSS_SELECTOR, '[title="Download Video"]')
            new_video_links = [x.get_attribute('href') for x in video_fields]
            self.video_links += new_video_links

            print(f'scraping {len(image_fields)} images and {len(video_fields)} videos from {self.browser.current_url}')
            if not next_button:
                break

            for new_link in new_image_links + new_video_links:
                if links.does_new_url_exist_in_cache(new_link):
                    print(f'{new_link} already exists from passed in json, stop searching')
                    return

            next_button.click()

    def _find_elm_by_type(self, by_type:str, key_name:str, wait_time:int=5):
        return WebDriverWait(self.browser, wait_time).until(EC.presence_of_element_located((by_type, key_name)))


class DownloadHelper:
    def __init__(self, args):
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


    def _dl_from_list(self, input_list, is_video, links:LinkCacheUser):

        for url in input_list:

            if links.does_new_url_exist_in_cache(url):
                print(f'SKipping since url exists in cache {url}')
                continue

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

    def _download_internal(self, is_video, links:LinkCacheUser):

        link_list = links.get_new_links(is_video)

        if self.single_proc:
            self._dl_from_list(link_list, is_video, links)
            return

        num_procs = 4
        outer_list = self._split_list(link_list, num_procs)

        proc_list = []
        for inner_list in outer_list:
            proc = multiprocessing.Process(
                                target=self._dl_from_list,
                                args=(inner_list, is_video, links)
                                )
            proc_list.append(proc)
            proc.start()

        for proc in proc_list:
            proc.join()


    def download_all(self, links:LinkCacheUser):

        self._download_internal(True, links)
        self._download_internal(False, links)


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
                        help='cached file of links. This is used for incremental downloads',
                        type=str, default=None, required=False)

    parser.add_argument('--child_name', dest='child_name',
                        help='Name of the child. This is a string that will be appended to each image name',
                        type=str,
                        required=True)

    parser.add_argument('--single_proc', dest='single_proc', action='store_true',
                        help='Do not download with multiprocessing. Just use the main Process. This is slower but more debugable',
                        required=False)

    parser.add_argument('--password', dest='password',
                        help='Optional password. If not provided, you can enter it manually in the browser',
                        type=str, required=False)

    parser.add_argument('--user', dest='user',
                        help='Optional username. If not provided, you can enter it manually in the browser',
                        type=str, required=False)

    parser.add_argument('--direct_url', dest='direct_url',
                        help='Optional direct url to https://classroom.kindercare.com/accounts/XXX/activities. This will save some clicking',
                        type=str, required=False)

    return parser.parse_args()


def main():

    args = get_args()

    links = LinkCacheUser(args.json_file)
    clicker = WebClicker()

    if args.direct_url:
        clicker.go_to_direct_url(args.direct_url)
        clicker.fill_out_credentials(args, True)
    else:
        clicker.go_to_app_site()
        clicker.fill_out_credentials(args, False)
        clicker.wait_for_child_choice()

    clicker.scrape_all_images(links)
    clicker.browser.close()

    links.save_links(clicker.image_links, clicker.video_links)
    links.write_json()

    DownloadHelper(args).download_all(links)

    print(f'End Script')

if __name__ == "__main__":
    main()
