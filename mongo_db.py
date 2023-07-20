import pymongo

mongo_client = pymongo.MongoClient('mongodb://localhost:27017')
db = mongo_client['user']
try:
    db.create_collection('user_details')
    db.create_collection('templates')
except  Exception as e:
    print('Error creating')