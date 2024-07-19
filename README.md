### Quickstart

```
usage: kcbulkdownload.py [-h] [--json_file JSON_FILE] --child_name CHILD_NAME [--single_proc] [--password PASSWORD] [--user USER] [--direct_url DIRECT_URL]

    Use a Selenium bot to click all of your child's images/videos ~1000 per year and then scrape
    all image links to a file usually `links.json`. Then download all of these images.
    TODO: tag them with time and gps coordinates.

optional arguments:
  -h, --help            show this help message and exit
  --json_file JSON_FILE
                        cached file of links. This is used for incremental downloads
  --child_name CHILD_NAME
                        Name of the child. This is a string that will be appended to each image name
  --single_proc         Do not download with multiprocessing. Just use the main Process. This is slower but more debugable
  --password PASSWORD   Optional password. If not provided, you can enter it manually in the browser
  --user USER           Optional username. If not provided, you can enter it manually in the browser
  --direct_url DIRECT_URL
                        Optional direct url to https://classroom.kindercare.com/accounts/XXX/activities. This will save some clicking
```


### Manual Steps

There are some manual steps required
1. Entering username/password
2. Clicking to the `Entries` tab. When in doubt, look for the url that matches https://classroom.kindercare.com/accounts/XXX/activities

### Skipping Manual Steps
- Use `--direct_url`
- Provide `user` and `password`. FYI, you'll see this in plaintext on you screen.

### Expected Runtimes
- 150 images/videos per minute when using 4 processes. Multiprocessing is on by default.
- When you provide a `--json_file`, the script will filter out previous urls that you have downloaded.


### Requirements
- python3
- see [requirements.txt](./requirements.txt)

### Errors
- Some of the scrapped URL's lead to an access denied request. I did not find it worth my time to handle these errors. I've logged the URL. You can look at the script output and manually try to find the image.
