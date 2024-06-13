### Quickstart

```
usage: kcbulkdownload.py [-h] [--json_file JSON_FILE] --child_name CHILD_NAME [--single_proc]

    Use a Selenium bot to click all of your child's images/videos ~1000 per year and then scrape
    all image links to a file usually `links.json`. Then download all of these images.
    TODO: tag them with time and gps coordinates.

optional arguments:
  -h, --help            show this help message and exit
  --json_file JSON_FILE
                        cached file of links. This saves 2 minutes of browser clicking
  --child_name CHILD_NAME
                        Name of the child. This is a string that will be appended to each image name
  --single_proc         Do not download with multiprocessing. Just use the main Process. This is slower but more debugable
```


### Manual Steps

There are some manual steps required
1. Entering username/password
2. Clicking to the `Entries` tab. When in doubt, look for the url that matches https://classroom.kindercare.com/accounts/XXX/activities


### Requirements

- python3
- `pip3 install selenium`
- `pip install webdriver-manager`
- `pip install geckodriver-autoinstaller` (firefox)
- `pip install chromedriver-binary` (chrome, you'll need to change the src code to run this)


### Errors

- Some of the scrapped URL's lead to an access denied request. I did not find it worth my time to handle these errors. I've logged the URL. You can look at the script output and manually try to find the image.
