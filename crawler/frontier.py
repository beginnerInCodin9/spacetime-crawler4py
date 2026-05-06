import os
import shelve

from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    # The frontier is responsible for keeping track of urls to be downloaded, and which urls have already been downloaded. It also handles saving and loading
    # this state to a file, so that the crawler can be stopped and restarted without losing progress.
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        self.lock = RLock() # Lock for synchronizing access to the frontier state, which is shared across threads.
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save) # Total urls discovered, including completed and to-be-downloaded.
        tbd_count = 0 # Count of total urls to be downloaded, excluding completed.
        # Iterate through save file, and add urls that are not marked as completed to the to_be_downloaded list.
        # Also count total urls discovered and to-be-downloaded urls for logging.
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        # Get a url from the frontier to be downloaded. This should only be 
        # called by the downloader threads, and should return None if there 
        # are no urls to be downloaded.
        with self.lock:
            try:
                return self.to_be_downloaded.pop()
            except IndexError:
                return None

    def add_url(self, url):
        # Add a url to the frontier to be downloaded, if it has not already been
        # discovered. This should only be called by the scraper threads, after 
        # they have extracted urls from a downloaded page.
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self.lock:
            if urlhash not in self.save:
                self.save[urlhash] = (url, False)
                self.save.sync()
                self.to_be_downloaded.append(url)
    
    def mark_url_complete(self, url):
        # Mark a url as completed, so that it will not be downloaded again.
        # This should only be called after a url has been successfully downloaded and processed.
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()
