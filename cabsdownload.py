#!/usr/bin/env python

import os
import re
import sys
import time
import requests


def download_file(url, filename):
    """Download a file from a given URL.

    :param url: The URL for the file to be downloaded.
    """
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()


def fetch_results(job_urls, base_dir):
    """Fetch the docking results for a list of jobs.

    :param job_urls: List of URLs for the jobs to be downloaded.

    :return: URLs for jobs whose downloads are still pending.
    """
    for url in job_urls[:]:
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            print 'Error fetching job %s. (%d)' % (
                url,
                response.status_code,
            )
            continue
        status = re.findall('Status:(.*)', response.text)[0]
        if 'running' in status:
            print url, 'still running.'
        elif 'error' in status:
            print url, 'finished with errors.'
            job_urls.remove(url)
        elif 'done' in status:
            print url, 'done, download started...'
            results_url = url.replace('/job/', '/job/CABSdock_')[:-1] + '.zip'
            filename = os.path.join(base_dir, os.path.basename(results_url))
            download_file(results_url, filename)
            job_urls.remove(url)
            print url, 'results download finished.'
    return job_urls


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print 'Syntax:\n cabsfetch.py job_urls_file'
    else:
        base_dir = os.path.dirname(sys.argv[1])
        with open(sys.argv[1]) as urls_file:
            job_urls = urls_file.read().splitlines()
            while len(job_urls) > 0:
                print '-' * 80
                print 'Retrieving results for %d jobs...' % len(job_urls)
                job_urls = fetch_results(job_urls, base_dir)
                # Sleep a while before polling again
                if len(job_urls) > 0:
                    time.sleep(60)
