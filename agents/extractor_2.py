import requests
import shutil
import re
from threading import *
from bs4 import BeautifulSoup
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

from models.conn import Database
from models.item_recipe import ItemRecipe
from models.item_image import ItemImage
from models.item_stat import ItemStat

class ItemExtractor(Thread):
    
    def __init__(self, agent_no, crawler):
        Thread.__init__(self)
        self.agent_no = agent_no
        self.crawler = crawler
        self.parser = 'html.parser'
        self.busy = False
        self.lemmatizer = WordNetLemmatizer()
        Database.initialize()
    
    def recipeExists(self, currItem):
        otherRecipes = Database.findItemRecipes(currItem.getName())
        # print(otherRecipes)
        
        for recipe in otherRecipes:
            if(currItem.compareCrafting(recipe)):
                return True
            
        return False
    
    def checkMissingRows(self, currMissingHeaders):
        if(len(currMissingHeaders) > 0):
            for header in currMissingHeaders:
                if(not header[2] and header[1] > 0):
                    return True
            
        return False
    
    def getSynonyms(self, string):
        # print(string)
        words = string.split()
        
        synonyms = []
        for word in words:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    synonyms.append(lemma.name())
        
        synonyms = list(set(synonyms))
        
        # print(string, synonyms)
        
        return synonyms
    
    def findItemImages(self, section):
        images = section.find_all('img')
        
        # print(images)

        for image in images:
            if image['alt'].find('version') == -1:
                
                # Verify image does not exist yet in the database
                imageData = Database.findItemImage(image['alt'])

                # print(f"IMAGE EXIST: {imageData}")
                if(not imageData):
                    # Push new image data
                    # print(image)
                    
                    if(image.get('data-src') != None):
                        imageData = ItemImage(image['alt'], image['data-src'])
                    else:
                        imageData = ItemImage(image['alt'], image['src'])
                    
                    Database.insert("item_images", imageData.toDict())
                    # print(imageData.getUrl())
                    
                    # Save image to local machine
                    imageSrc = requests.get(imageData.getUrl(), stream=True)
                    
                    if imageSrc.status_code == 200:
                        with open("images/" + imageData.getName() + '.png', 'wb') as f:
                            shutil.copyfileobj(imageSrc.raw, f)
                            self.crawler.incrementImageCounter()
                        # print('Image retrieval success')
                    else:
                        print('Image retrieval error')
    
    def findItemStats(self, section):
        # Item statistics
        infobox = section.find('div', class_='infobox')
        
        if(infobox != None):
            itemName = infobox.find('div', class_="title")
            itemStats = infobox.find('div', class_="statistics")
            
            statTable = {}
            
            # print(itemStats)
            if itemStats:
                
                if(itemName):
                    itemName = itemName.text.strip()
                
                table = itemStats.find('table', class_="stat")
                # print(table)
                
                for stat in table.find('tbody').find_all('tr'):
                            
                    # print(stat.th.text)
                    header = stat.th.text.strip().lower()                  
                    header_words = self.getSynonyms(header)
                    header_words.append(header)
                    
                    for word in header_words:
                        if(word == "type"):
                            statTable["Tags"] = []
                            
                            tags = stat.td.find('div', class_="tags")
                            
                            if(tags):
                                tags = tags.find('span')
                                for tag in tags:
                                    # print(tag.text)
                                    statTable["Tags"].append(tag.text)
                            
                            else:
                                tags = stat.td.text.strip()
                                
                                statTable["Tags"].append(tags)
                            
                        elif(word == "damage"):
                            
                            tdValue = stat.td.text
                            # print(tdValue)

                            dmgValue = re.search(r'\d+', tdValue)
                            dmgType = re.search(r'\((.*?)\)', tdValue)
                            
                            if(dmgValue != None):
                                statTable[stat.th.text] = int(dmgValue.group())
                            if(dmgType != None):
                                statTable["Damage_Type"] = dmgType.group(1)
                                    
                        elif(word in ("knockback", "critical chance", "use time", "velocity")):
                            
                            tdValue = stat.td.text
                            
                            statTable[stat.th.text] = int(re.search(r'\d+', tdValue).group())
                            
                        else:
                            
                            if(stat.th.text != ""):
                                statTable[stat.th.text] = stat.td.text
                        
                    
                            
                # print(itemName)
                # print(statTable)
                
                if(Database.findItemStat(itemName) == None):
                    item_stat = ItemStat(itemName, statTable)
                    Database.insert("item_stats", item_stat.getStats())
                    self.crawler.incrementStatCounter()
                    
                
                # print(item_stat.getName(), item_stat.getStats())
    
    def getInfoFromPage(self, response):
        
        soup = BeautifulSoup(response.text, self.parser)
        
        self.crawler.incrementVisitedCounter()
        
        craftsTables = soup.find_all('table')
        # craftables = craftables.find('table', class_="")
        
        # for table in craftsTables:
            # print(table)
        
        for table in craftsTables: 
            headers = []
            header_cells = table.find_all('th')
            
            amount_col = False
            
            count = 0
            
            # print(header_cells)
            
            # Detect whether table contains crafting recipes or not
            if header_cells:
                for cell in header_cells:
                    text = cell.text.lower()
                                        
                    text_words = self.getSynonyms(text)
                    text_words.append(text)
                    
                    for word in text_words:
                        if ("station" in text or "ingredient" in text or "result" in text):
                            count += 1
                                        
                        # Also check if amount is embedded within ingredients or is its own column
                        if "amount" in word:
                            amount_col = True
                        
                        headers.append(text)
                
                
                # If it does contain crafting recipes process the table
                if count > 1:
                    
                    prevItem = None
                    currItem = ItemRecipe(None)
                    
                    # Detect table structure
                    inner_table = table.find('table')
                    
                    if(inner_table):
                        table = inner_table
                    
                    rows = table.find_all('tr')
                    
                    # print(rows)
                    
                    currHeaders = []
                    
                    for i in range(0, len(rows)):
                        
                        headers = rows[i].find_all('th')
                        datas = rows[i].find_all('td') 
                        
                        newIngredient = {
                            'name': '',
                            'amount': 0,
                        }
                        
                        if headers:
                            # print("NEW HEADERS")
                            currHeaders.clear()
                            for header in headers:
                                colspan = 1
                                if(header.has_attr('colspan')):
                                    colspan = int(header['colspan'])
                                currHeaders.append((header.text.strip().lower(), colspan))
                            # print("CURRENT HEADERS: ", currHeaders)
                        
                        elif datas:
                            result_rowspan = 1
                            total = 0
                            
                            currCol = None
                            total = 0
                            
                            for j in range(0, len(datas)):
                                
                                # print("I: ", i)
                                
                                self.findItemImages(datas[j])
                                
                                if(datas[j].text.strip().lower() != 'or'):
                                    
                                    print("CURRENT COLUMN: ", currCol)
                                    print(f"LEN DATAS: {len(datas)}, LEN HEADERS: {len(currHeaders)}")
                                    # print(f"DATAS\n{datas}\n")
                                    if(len(datas) >= len(currHeaders)):
                                        total = 0
                                        idx = j
                                        for k in range(0, len(currHeaders)):
                                            # print(f"TOTAL: {total}, IDX: {idx}, k: {k}")
                                            total += currHeaders[k][1]
                                            if(total >= idx + 1):
                                                # print("This is curr header", total, currHeaders[j][0])
                                                currCol = currHeaders[k]
                                                break
                                    else:
                                        # print("HI")
                                        for header in currHeaders:
                                            header_name = self.lemmatizer.lemmatize(header[0])
                                            header_words = self.getSynonyms(header_name)
                                            header_words.append(header)
                                            
                                            for word in header_words:
                                                if("ingredient" in word):
                                                    currCol = header
                                                    break
                                    
                                    print(currCol)
                                    header_syn = self.getSynonyms(currCol[0])
                                    header_syn.append(currCol[0])
                                    
                                    for word in header_syn:
                                        if "result" in word:
                                            
                                            name = datas[j]
                                            link = name.find('a')
                                            
                                            if(result_rowspan > 1):
                                                name = name.text

                                                for k in range(1, currCol[1]):
                                                    # print(i, j)
                                                    name = name + datas[j + k].text
                                                    if(not link):
                                                        link = datas[j + k].find('a')
                                                
                                                name = name.strip()                    
                                                # print("HIIII " + name)
                                            else:
                                                name = name.text.strip()
                                            
                                            currItem.setName(name)
                                            
                                            if(link and link.has_attr('href')):
                                                currItem.setLink(self.crawler.root_url + link['href'])
                                            else:
                                                currItem.setLink(response.url)
                                            
                                            # if(currCol[1] > 1):
                                            #     break
                                            
                                            break
                                            # print(name)
                                            # print(link['href'])
                                                                            
                                        elif "station" in word:
                                            stations = datas[j].find_all('span', class_='i')
                                
                                            if not stations:
                                                # print("not stations", datas[i].text.strip())
                                                currItem.addStation(datas[j].text.strip())
                                            else:
                                                for station in stations:
                                                    # print("stations ", station)
                                                    currItem.addStation(station.text)  

                                            break
                                        elif "amount" in word:
                                            
                                            amount = int(datas[j].text.strip())
                                            newIngredient['amount'] = amount

                                            break
                                            
                                        elif "ingredient" in word or "made" in word:
                                            
                                            ingredients =  datas[j].find('ul')
                                            # print(ingredients)
                                            
                                            if(ingredients):
                                                ingredients = ingredients.find_all('li')
                                                
                                                for ingredient in ingredients:
                                                    
                                                    name = ingredient.text.strip()
                                                    if(not amount_col):
                                                        amount_str = re.search(r"\((\d+)\)", name)
                                                        if(not amount_str):
                                                            amount = 1
                                                        else:
                                                            amount = int(amount_str.group(1))
                                                            name = name.replace(amount_str.group(0), "")
                                                    else:
                                                        amount = 1
                                                        
                                                    currItem.addIngredient({
                                                        'name': name,
                                                        'amount': amount
                                                    })
                                            else:
                                                ingredients = datas[j].text.strip()  
                                                
                                                if(not amount_col):
                                                    amount_str = re.search(r"\((\d+)\)", ingredients)
                                                    if(not amount_str):
                                                        amount = 1
                                                    else:
                                                        amount = int(amount_str.group(1))
                                                        name = name.replace(amount_str.group(0), "")
                                                    newIngredient["amount"] = amount
                                                newIngredient["name"] = ingredients

                                            break
                                    if(newIngredient['amount'] != 0 and newIngredient['name'] != ''):
                                        currItem.addIngredient(newIngredient)
                                        newIngredient = {
                                            'name': '',
                                            'amount': 0,
                                        }
                                    
                                    
                        # print(currItem.toDict())
                                    
                        if(prevItem):
                            # print(prevItem.toDict())
                            if(currItem.getName() == None):
                                currItem.setName(prevItem.getName())
                            if(len(currItem.getIngredients()) == 0):
                                currItem.setIngredients(prevItem.getIngredients())
                            if(len(currItem.getStation()) == 0):
                                currItem.setStation(prevItem.getStation())
                        
                        if(currItem.getName() and len(currItem.getIngredients()) != 0 and len(currItem.getStation()) != 0):
                            
                            if(i + 1 < len(rows)):
                                next_data = rows[i+1].find_all('td')
                                headers = rows[i+1].find_all('th')
                                
                                # print(f"LEN NEXT DATA: {len(next_data)}, LEN CURR HEADERS: {len(currHeaders)}")
                                
                                if(next_data and len(next_data) <= len(currHeaders)):
                                    continue

                            is_recipe_exist = self.recipeExists(currItem)
                            
                            # print(is_recipe_exist)
                            
                            if(not is_recipe_exist):
                                Database.insert("item_recipes", currItem.toDict()) 
                                self.crawler.incrementRecipeCounter()
                                
                            prevItem = currItem
                            currItem = ItemRecipe(None)
                                    
                            
                                  
        self.findItemStats(soup)

        links = soup.find_all('a')
        self.crawler.addLinksToQueue(links)
                     
    def run(self):
        while True:
            link = self.crawler.page_queue.get()
            self.busy = True
            
            try:
                print(f"Agent {self.agent_no} visiting {link}")
                page = requests.get(link)
            except requests.exceptions.RequestException as e:
                print(e)
                return None
            else:
                self.getInfoFromPage(page)
            finally:
                self.busy = False
                self.crawler.page_queue.task_done()
            
