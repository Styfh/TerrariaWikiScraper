from pymongo.mongo_client import MongoClient

class Database(object):
    
    uri = "mongodb://localhost:27017"
    db = None
    
    @staticmethod
    def initialize():
        client = MongoClient(Database.uri)
        Database.db = client['terraria_items']
        
    @staticmethod
    def insert(collection, data):
        # print(Database.db[collection])
        Database.db[collection].insert_one(data)
        # print("item added successfully")
    
    @staticmethod
    def findItemRecipes(itemName):
        
        query = {"name": { "$regex": ".*" + itemName + ".*" }}
    
        return Database.db["item_recipes"].find(query)
    
    @staticmethod
    def findItemImage(itemName):
        
        query = {"name": { "$regex": ".*" + itemName + ".*"}}
        
        return Database.db["item_images"].find_one(query)
    
    @staticmethod
    def findItemStat(itemName):
        
        query = {"name": { "$regex": ".*" + itemName + ".*"}}
        
        return Database.db["item_stats"].find_one(query)