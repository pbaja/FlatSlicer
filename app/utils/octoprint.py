import requests
import logging as log
from requests.compat import urljoin

class Octoprint:

    def __init__(self, config):
        self.url = config.get_value('octoprint.url')
        self.key = config.get_value('octoprint.key')

    def upload(self, filename, text):
        url = urljoin(self.url, '/api/files/local')
        files = {'file': (filename, text)}
        data = {'select': 'true','print': 'false' }
        headers = { 'X-Api-Key': self.key }

        response = requests.post(url, files=files, data=data, headers=headers)
        code = response.status_code
        if code == 201: log.info(f'File {filename} uploaded to Octoprint')
        else: log.error(f'Failed to upload file to octoprint. Response code: {code}')