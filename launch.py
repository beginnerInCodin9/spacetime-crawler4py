from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
from scraper import write_report


def main(config_file, restart):
    # ConfigParser is used to read the config file and create a Config object, 
    # which is then passed to the Crawler. The get_cache_server function is 
    # used to determine which cache server to use based on the config and 
    # whether we are restarting or not.
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    try:
        crawler.start()
    except KeyboardInterrupt:
        print("Crawling interrupted by user. Writing report...")
    finally:
        write_report() # Write the report regardless of how the crawling process ends (either normally or via interruption).

if __name__ == "__main__":
    # ArgumentParser is used to parse command-line arguments for the config file 
    # and whether to restart. The main function is then called with these arguments.
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
