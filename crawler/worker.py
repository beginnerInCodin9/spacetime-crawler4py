from threading import RLock, Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from urllib.parse import urlparse


class Worker(Thread):
    # The worker is responsible for downloading a url, and processing the response with the scraper.
    # It also adds any new urls discovered by the scraper to the frontier, and marks the url as
    # completed in the frontier. Each worker runs in its own thread, and continuously gets urls to
    # be downloaded from the frontier until there are no more urls to be downloaded.

    # last_visit_times is a dictionary that maps domain names to the last time they were visited 
    # by any worker. This is used to enforce the politeness policy, which requires that we wait 
    # a certain amount of time between requests to the same domain. The domain_lock is a lock 
    # that is used to synchronize access to the last_visit_times dictionary, since it is shared
    # across all worker threads.
    last_visit_times = {}
    domain_lock = RLock() # Lock for synchronizing access to the last_visit_times dictionary, which is shared across threads.
    
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            # Get a url to be downloaded from the frontier. If there are no urls to be downloaded, stop the worker.
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
                
            # Enforce politeness policy: Wait for the required time delay between requests 
            # to the same domain.
            domain = urlparse(tbd_url).netloc
            with self.domain_lock:
                last_visit = self.last_visit_times.get(domain, 0)
                # Calculate how much time to sleep to enforce the time delay, and sleep 
                # if necessary.
                sleep_time = self.config.time_delay - (time.time() - last_visit)
                if sleep_time > 0: # Sleep only if we need to wait more time to satisfy the time delay requirement
                    time.sleep(sleep_time)
                self.last_visit_times[domain] = time.time()

            # Download the url, and process the response with the scraper. Add any new urls discovered by the
            # scraper to the frontier, and mark the url as completed in the frontier.
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
