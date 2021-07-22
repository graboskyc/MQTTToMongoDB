import pymongo
from bson.objectid import ObjectId
import threading
import os
from bson.json_util import dumps
from datetime import datetime

##########
# Reference script to run at the edge to push to far cloud
##########
# configure connection to mongodb
zone_name = "Boston"
partition_key = [zone_name]
conn_src = pymongo.MongoClient("")
conn_dst = pymongo.MongoClient("")
handle_src = conn_src["messages"]["messages"]
handle_dst = conn_dst["messages"]["messages"]

def processChange(token, change):
    if(change["operationType"] == "insert"):
        newDoc = change["fullDocument"]
        # ignore this if we just got sent from farcloud
        if(newDoc["syncback"] != False):
            print("Inserting...")
            print("\t\tResume Token Ending " + token["_data"][-10:])
            
            # region doc cleanup
            newDoc["_pk"] = partition_key
            newDoc["srcZone"] = zone_name
            newDoc["srcResumeToken"] = token
            newDoc["syncback"] = False
            # endregion
            handle_dst.insert_one(newDoc)
    if(change["operationType"] == "update"):
        newDoc = change["fullDocument"]
        if(newDoc["syncback"] != False):
            print("Updating...")
            print("\t\tResume Token Ending " + token["_data"][-10:])
            
            # region doc cleanup
            newDoc["srcResumeToken"] = token
            newDoc["syncback"] = False
            # endregion
            handle_dst.replace_one({"_id":change["documentKey"]["_id"]}, newDoc)
    if(change["operationType"] == "delete"):
        newDoc = change["fullDocument"]
            print("Deleting...")
            print("\t\tResume Token Ending " + token["_data"][-10:])
            handle_dst.deleteOne({"_id":change["documentKey"]["_id"]})


###########
# Main loop
##########
if __name__ == "__main__":
    try:
        resume_token = None
        pipeline = [{"$match": {"syncback": {"$ne":False}, "_pk":{"$in": partition_key}}}]
        with handle_src.watch(pipeline) as stream:
            for change in stream:
                # store this for safe keeping somewhere
                resume_token = stream.resume_token
                processChange(resume_token, change)
                
    except pymongo.errors.PyMongoError:
        # The ChangeStream encountered an unrecoverable error or the
        # resume attempt failed to recreate the cursor.
        if resume_token is None:
            # There is no usable resume token because there was a
            # failure during ChangeStream initialization.
            logging.error('...')
        else:
            # Use the interrupted ChangeStream's resume token to create
            # a new ChangeStream. The new stream will continue from the
            # last seen insert change without missing any events.
            with db.collection.watch(pipeline, resume_after=resume_token) as stream:
                for insert_change in stream:
                    processChange(resume_token, change)