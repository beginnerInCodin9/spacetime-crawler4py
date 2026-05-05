import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup
import PartA


# Global variables to store answers for report
unique_urls = set() # Q1: How many unique pages did you find? Uniqueness for the purposes of this assignment is ONLY established by the URL, but discarding the fragment part.
longest_page = {"url": "", "word_count": 0} # Q2: What is the longest page in terms of the number of words? (HTML markup doesn’t count as words)
word_frequencies = {} # Q3: What are the 50 most common words in the entire set of pages crawled under these domains ? (Ignore English stop words, which can be found, for example, hereLinks to an external site.) Submit the list of common words ordered by frequency.
subdomains = {} # Q4: How many subdomains did you find in the uci.edu domain? Submit the list of subdomains ordered alphabetically and the number of unique pages detected in each subdomain. The content of this list should be lines containing subdomain, number, for example: vision.ics.uci.edu, 10 (not the actual number here)


# Stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "beeing", "below", "between",
    "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", 
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", 
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}


def scraper(url, resp):
    links = extract_next_links(url, resp) # Extract the hyperlinks from the page and update global variables for the report
    return links # Return the list of hyperlinks extracted from the page to be added to the crawl frontier


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    global word_frequencies, longest_page, unique_urls, subdomains

    # Check if the response is valid and contains content
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return list() # Return an empty list if the response is not successful or content is missing
    
    if len(resp.raw_response.content) > 1000000:
        return list() # Return an empty list if the content is excessively large (greater than 1MB) to avoid processing very large pages that may be traps or not relevant
        
    # Remove the fragment from the URL and check if it has already been processed
    clean_url, _ = urldefrag(resp.url)
    if clean_url in unique_urls: # Check if the URL has already been processed
        return list() # Return an empty list if the URL has already been processed
    unique_urls.add(clean_url) # Add the clean URL to the set of unique URLs

    # Parse the HTML content and extract visible text
    soup = BeautifulSoup(resp.raw_response.content, "lxml") # Parse the HTML content using BeautifulSoup with the lxml parser
    visible_text = soup.get_text() # Extract the text content from the HTML

    # Define a helper function to tokenize the visible text using regular expressions following the same logic as PartA's tokenize function
    def tokenize_text(text):
        return re.findall(r'[a-zA-Z0-9]+', text.lower()) # Use regular expressions to find all alphanumeric tokens and convert them to lowercase for case-insensitivity
    
    tokens = tokenize_text(visible_text) # Tokenize the visible text

    meaningful_tokens = [token for token in tokens if token not in STOP_WORDS] # Filter out stop words from the list of tokens

    # Update longest page while ignoring stop words
    current_word_count = len(meaningful_tokens) # Count the number of tokens on the page
    if current_word_count > longest_page["word_count"]: # Check if the current page has more words than the longest page recorded so far
        longest_page = {"url": clean_url, "word_count": current_word_count} # Update the longest page with the current page's URL and word count

    # Update word frequencies while ignoring stop words
    if len(meaningful_tokens) >= 50: # Only consider pages with at least 50 meaningful tokens to avoid skewing the word frequencies with very short pages that may not be informative
        page_freqs = PartA.computeWordFrequencies(meaningful_tokens) # Compute the frequency of each meaningful token on the page using the computeWordFrequencies function from PartA
        for word, count in page_freqs.items(): # Update the global word frequencies dictionary with the counts from the current page, ignoring stop words
            word_frequencies[word] = word_frequencies.get(word, 0) + count # Increment the count for each word in the global word frequencies dictionary, initializing to 0 if the word hasn't been seen before

    parsed_url = urlparse(clean_url) # Parse the clean URL to extract components
    if parsed_url.netloc.endswith("uci.edu"): # Check if the URL belongs to the uci.edu domain
        subdomain = parsed_url.netloc # Extract the subdomain from the URL
        subdomains[subdomain] = subdomains.get(subdomain, 0) + 1 # Add the subdomain to the subdomains dictionary and increment the count of unique pages for that subdomain, initializing to 0 if the subdomain hasn't been seen before

    # Temporary debug prints; TO BE DELETED LATER
    print(f"Total Unique: {len(unique_urls)}")
    print(f"Current Longest: {longest_page['word_count']} words at {longest_page['url']}")
    print(f"Subdomains found: {len(subdomains)}")

    # Extract hyperlinks from the page
    extracted_links = set() # Use a set to store extracted links to avoid duplicates
    for link in soup.find_all('a', href=True): # Find all anchor tags with an href attribute
        href = link['href'] # Get the href value from the anchor tag

        # Skip links that are not valid for crawling, such as Javascript links, mailto links, or fragment-only links
        if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("#"):
            continue

        # Skip links that contain "YOUR_IP" (case-insensitive) or are IPv6 addresses (start with "[" or "http://[" or "https://[") to avoid crawling potentially invalid or trap URLs
        if "YOUR_IP" in href.upper() or href.startswith("[") or href.startswith("http://[") or href.startswith("https://["):
            continue

        try: 
            full_url = urljoin(clean_url, link['href']) # Construct the full URL by joining the clean URL with the href value
        except ValueError:
            continue # Skip malformed URLs that cannot be joined properly

        defragmented_url, _ = urldefrag(full_url) # Remove the fragment from the URL
        # Check if the defragmented URL is valid and has not been processed before, then add it to the set of extracted links
        if is_valid(defragmented_url) and defragmented_url not in unique_urls:
            extracted_links.add(defragmented_url)

    return extracted_links


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Only crawl URLs that belong to the specified domains
        allowed_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False
        
        # Exclude URLs that contain "calender" (case-insensitive) or "calendar" (case-insensitive) or are excessively long (greater than 200 characters)
        if "calender" in parsed.path.lower() or "calendar" in parsed.path.lower() or len(url) > 200:
            return False
        
        # Exclude URLs that contain certain keywords that are commonly associated with calendar or scheduling pages, such as "ical=1", "outlook-ical", "tribe-bar-date", or "eventdisplay" (case-insensitive)
        if any(pattern in url.lower() for pattern in ["ical=1", "outlook-ical", "tribe-bar-date", "eventdisplay"]):
            return False
        
        # Exclude URLs that are related to events and have specific sub-paths that are commonly associated with calendar or scheduling pages, such as "/category/", "/list/", "/day/" or "week-" (case-insensitive)
        if "/event/" in url.lower() or "/events/" in url.lower():
            if any(pattern in url.lower() for pattern in ["/category/", "/list/", "/day/", "week-"]):
                return False
            if re.search(r'/\d{4}-\d{2}(-\d{2})?/', url.lower()): # Exclude URLs that contain date patterns in the path, which are commonly associated with event pages (e.g., "/2023-12-31/" or "/2023-12/")
                return False
            
        # Exclude URLs that contain certain query parameters that are commonly associated with traps, such as "do=", "idx=", "tab_details=", "tab_files=", "share=", "replytocom=", "printable=", "export", or "pdf" (case-insensitive)
        if any(trap_patterns in url.lower() for trap_patterns in ["do=", "idx=", "tab_details=", "tab_files=", "share=", "replytocom=", "printable=", "export", "pdf"]):
            return False
        
        # Exclude URLs that contain certain patterns that are commonly associated with common redundant or low-information pages, such as "/page/", "version=", "rev=", "diff=", "action=", "/login/", or "/embed/" (case-insensitive)
        if any(useless_patterns in url.lower() for useless_patterns in ["/page/", "version=", "rev=", "diff=", "action=", "/login/", "/embed/"]):
            return False
        
        # Exclude URLs that have repeated path segments, which can indicate a trap (e.g., "/a/b/a/b/")
        if re.search(r'(/.+?)\1{2,}', parsed.path):
            return False
        
        # Exclude URLs that contain certain path segments that are commonly associated with traps, such as "/action/", "/login/", or "/embed/" (case-insensitive)
        if any(path_segment in parsed.path.lower() for path_segment in ["/action/", "/login/", "/embed/"]):
            return False
        
        # Exclude URLs that have an excessive number of path segments (e.g., more than 10), which can indicate a trap: Going too deep into the directory
        if parsed.path.count('/') > 10:
            return False

        return not re.match(
            r".*\.(css|js|apk|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", url.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def write_report():
    # Write the report to a file named "report.txt" in the current directory
    with open("report.txt", "w") as report_file:
        # Q1: Total unique pages found
        report_file.write(f"Q1: Total unique pages found: {len(unique_urls)}\n\n")
        
        # Q2: Longest page in terms of number of words
        report_file.write(f"Q2: Longest page: {longest_page['url']} ({longest_page['word_count']} words)\n\n")
        
        # Q3: 50 most common words and their frequencies
        sorted_word_freqs = sorted(word_frequencies.items(), key=lambda item: item[1], reverse=True)[:50] # Get the top 50 most common words sorted by frequency
        report_file.write("Q3: 50 most common words and their frequencies:\n")
        for word, freq in sorted_word_freqs:
            report_file.write(f"{word}: {freq}\n")
        report_file.write("\n")
        
        # Q4: Subdomains found in uci.edu domain and the number of unique pages detected in each subdomain
        sorted_subdomains = sorted(subdomains.items()) # Sort subdomains alphabetically
        report_file.write("Q4: Subdomains found in uci.edu domain and the number of unique pages detected in each subdomain:\n")
        for subdomain, count in sorted_subdomains:
            report_file.write(f"{subdomain}: {count}\n")