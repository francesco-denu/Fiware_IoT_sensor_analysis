import json
from pymongo import MongoClient
 
 
# Making Connection
myclient = MongoClient("mongodb://localhost:27017/")
  
# database
db = myclient["orion"]   
  
# Created or Switched to collection
# names: GeeksForGeeks
collection = db["means"]
 
# Loading or Opening the json file
with open('./import_data/average_values.json') as file:
	file_data = json.load(file)

     
# Inserting the loaded data in the Collection
# if JSON contains data more than one entry
# insert_many is used else insert_one is used
if isinstance(file_data, list):
    collection.insert_many(file_data) 
else:
    collection.insert_one(file_data)
              
    