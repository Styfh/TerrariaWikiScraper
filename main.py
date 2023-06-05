from agents.crawler import Crawler

while True:
    crawl_mode = False
    no_agents = 1
    page_limit = 0
    
    start_url = input("Enter url to crawl: ")
    crawl_mode_str = input("Crawl mode (y/n)?: ")
    if(crawl_mode_str == 'y'):
        crawl_mode = True
        no_agents = int(input("How many agents should be used? "))
    
    crawler = Crawler(start_url, no_agents, crawl_mode)
    crawler.start()