class ItemRecipe:
    def __init__(self, name):
        self.name = name
        self.ingredients = []
        self.station = []
        self.link = ""
    
    def getName(self):
        return self.name
    
    def setName(self, name):
        self.name = name
        
    def getIngredients(self):
        return self.ingredients
    
    def setIngredients(self, ingredients):
        self.ingredients = ingredients
    
    def addIngredient(self, ingredient):
        self.ingredients.append(ingredient)
        
    def getStation(self):
        return self.station
    
    def setStation(self, stations):
        self.station = stations
    
    def addStation(self, station):
        self.station.append(station)
    
    def getLink(self):
        return self.link
    
    def setLink(self, link):
        self.link = link
     
    def toDict(self):
        
        return {
            "name": self.name,
            "ingredients": self.ingredients,
            "station": self.station,
            "link": self.link
        }
    
    def compareCrafting(self, toCompare):
        
        return (self.name == toCompare["name"] and 
                self.ingredients == toCompare["ingredients"] and 
                self.station == toCompare["station"])
        