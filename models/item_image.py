class ItemImage:
    
    def __init__(self, itemName, imageUrl):
        self.itemName = itemName
        self.imageUrl = imageUrl
    
    def getName(self):
        return self.itemName
    
    def getUrl(self):
        return self.imageUrl
    
    def toDict(self):
        return {
            "name": self.itemName,
            "url": self.imageUrl
        }