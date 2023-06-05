import time
from queue import *
from agents.extractor import ItemExtractor

class Crawler:
    
    def __init__(self, start_url, num_agents=1, crawl_mode = 1):
        self.visited = []
        self.recipe_counter = 0
        self.image_counter = 0
        self.stat_counter = 0
        self.visited_count = 0
        self.page_queue = Queue()
        self.start_url = start_url
        self.num_agents = num_agents
        self.crawl_mode = crawl_mode
        
        self.root_url = start_url.split('.com')[0] + '.com'
        
    def start(self):
        
        start_time = time.time()
        
        for i in range(self.num_agents):
            agent = ItemExtractor(i + 1, self)
            agent.daemon = True
            agent.start()
            
        self.page_queue.put(self.start_url)
        
        self.page_queue.join()
        
        print(f"fetched {self.recipe_counter} recipes, {self.image_counter} images, {self.stat_counter} item stats\nfrom {self.visited_count} links in {time.time() - start_time} seconds")
    
    def addLinksToQueue(self, links):
        # print(links)
        if(self.crawl_mode): 
            for link in links:
                if hasattr(link, 'has_attr') and link.has_attr('href'):
                    if link.get('href'):
                        if link.get('href').startswith('/wiki/') and link.get('href') not in self.visited:
                            link = link.get('href')
                            if('?' in link):
                                link = link.split('?')[0]
                            self.page_queue.put(self.root_url + link)
                                
        
        # print(list(self.page_queue.queue))
    
    def incrementRecipeCounter(self):
        self.recipe_counter += 1
    
    def incrementImageCounter(self):
        self.image_counter += 1
    
    def incrementStatCounter(self):
        self.stat_counter += 1
        
    def incrementVisitedCounter(self):
        self.visited_count += 1