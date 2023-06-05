class ItemStat:
    
    def __init__(self, name, stats):
        self.stats = stats
        
        self.stats["name"] = name
    
    def getStats(self):
        return self.stats