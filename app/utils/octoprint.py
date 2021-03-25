import requests
import logging as log
from typing import Tuple
from enum import IntEnum
from requests.compat import urljoin

class OctoprintResult(IntEnum):
    Invalid = 0
    Success = 1
    GenericError = 2
    InvalidConfig = 3
    ConnectionFailed = 4
    Unauthorized = 5
    InvalidResponse = 6

class Octoprint:

    @staticmethod
    def upload(config, filename, text) -> None:
        # Get url and key
        url = config.get_value('octoprint.url')
        key = config.get_value('octoprint.key')

        # Prepare data
        url = urljoin(self.url, '/api/files/local')
        files = {'file': (filename, text)}
        data = {'select': 'true','print': 'false' }
        headers = { 'X-Api-Key': self.key }

        # Upload
        response = requests.post(url, files=files, data=data, headers=headers)
        code = response.status_code
        if code == 201: log.info(f'File {filename} uploaded to Octoprint')
        else: log.error(f'Failed to upload file to octoprint. Response code: {code}')

    @staticmethod
    def server_version(config) -> Tuple[OctoprintResult, str]:
        # Get url and key
        url = config.get_value('octoprint.url')
        key = config.get_value('octoprint.key')

        if len(url) == 0 or len(key) == 0:
            return (OctoprintResult.InvalidConfig, '')

        # Request data
        url = urljoin(url, '/api/server')
        headers = { 'X-Api-Key': key }
        try:
            response = requests.get(url, headers=headers, timeout=3)
        except requests.exceptions.MissingSchema as e:
            return (OctoprintResult.InvalidConfig, str(e))
        except requests.exceptions.ConnectionError:
            return (OctoprintResult.ConnectionFailed, '')
        except Exception as e:
            print(e)
            return (OctoprintResult.GenericError, str(e))

        # Check HTTP status code
        if response.status_code != 200:
            return (OctoprintResult.Unauthorized, response.text)

        # Check data
        data = response.json()
        if 'version' not in data:
            return (OctoprintResult.InvalidResponse, str(data))

        # Return result
        return (OctoprintResult.Success, data['version'])

        
        