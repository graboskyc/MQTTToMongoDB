import pymongo
from bson.objectid import ObjectId
import threading
import os
from bson.json_util import dumps
from datetime import datetime

# configure connection to mongodb
conn_src = pymongo.MongoClient("mongodb://root:root123@localhost:27100,localhost:27101,localhost:27102")
conn_dst = pymongo.MongoClient("mongodb+srv://user:password@example.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
handle_src = conn_src["messages"]["messages"]
handle_dst = conn_dst["realmvr"]["IOTDataPoint"]

###########
# Main loop
##########
if __name__ == "__main__":
    # connect to a change stream
    change_stream = handle_src.watch()
    # every change in the db
    for change in change_stream:
        # can be insert, update, replace (Compass)
        if change["operationType"] == "insert":
            print("Inserting...")
            # make sure it had a URL attribute
            newDoc = change["fullDocument"]
            # region doc cleanup
            newDoc["+pk"] = "user=609e790074dbe8c9bdfc9ad5"
            newDoc["src"] = "edge"
            # endregion
            handle_dst.insert_one(newDoc)