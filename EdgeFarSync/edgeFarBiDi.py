import pymongo
from bson.objectid import ObjectId
import _thread
from bson.json_util import dumps
from datetime import datetime
import os

##########
# Reference script to run at the edge sync with far cloud
##########

##########
# configure connection to mongodb
##########
zone_name = os.environ['ZONENAME']                              # name of edge zone this script is running in
watch_zones =  os.environ['WATCHZONES'].split(',')              # which keys this zone cares about to pull from far cloud
constr_edge =  os.environ['CONSTREDGE']                         # edge mongodb connection string
constr_far =  os.environ['CONSTRFAR']                           # far cloud connection string
db_name = "messages"                                            # db to watch
col_name = "messages"                                           # collection to watch

##########
# shouldn't need to modify below
##########
conn_edge = pymongo.MongoClient(constr_edge)
conn_far = pymongo.MongoClient(constr_far)
handle_edge = conn_edge[db_name][col_name]
handle_far = conn_far[db_name][col_name]

##########
# implement whatever business logic you want to process a change
##########
def processChange(token, change, sourceName, targetName, handle, addKey):
    try:
        # it was an insert
        if(change["operationType"] == "insert"):
            newDoc = change["fullDocument"]
            print("Inserting document into %s..."%(targetName))
            print("\t\tResume Token Ending " + token["_data"][-10:])
            
            # region doc cleanup
            if addKey:
                newDoc["_pk"] = zone_name
            # endregion

            handle.insert_one(newDoc)
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"insert"})

        # it was an update
        if(change["operationType"] == "update"):
            newDoc = change["fullDocument"]
            print("Updating document in %s..."%(targetName))
            print("\t\tResume Token Ending " + token["_data"][-10:])
            
            # region doc cleanup
            if addKey:
                newDoc["_pk"] = zone_name
            # endregion

            handle.replace_one({"_id":change["documentKey"]["_id"]}, newDoc)
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"update"})
        # it was an delete
        if(change["operationType"] == "delete"):
            print("Deleting document from %s..."%(targetName))
            print("\t\tResume Token Ending " + token["_data"][-10:])
            handle.delete_one({"_id":change["documentKey"]["_id"]})
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"delete"})
    except:
        pass

def watchCollection(name_src, h_src, name_dst, h_dst, pipeline, addKey):
    print("Ready " + name_src)
    try:
        resume_token = None
        with h_src.watch(pipeline, full_document="updateLookup") as stream:
            for change in stream:
                # store this for safe keeping somewhere
                resume_token = stream.resume_token
                processChange(resume_token, change, name_src, name_dst, h_dst, addKey)
                
    except pymongo.errors.PyMongoError as ex:
        # The ChangeStream encountered an unrecoverable error or the
        # resume attempt failed to recreate the cursor.
        if resume_token is None:
            # There is no usable resume token because there was a
            # failure during ChangeStream initialization.
            print('ERROR: ' + str(ex))
        else:
            # Use the interrupted ChangeStream's resume token to create
            # a new ChangeStream. The new stream will continue from the
            # last seen insert change without missing any events.
            with h_src.watch(pipeline, full_document="updateLookup", resume_after=resume_token) as stream:
                for insert_change in stream:
                    processChange(resume_token, insert_change, name_src, name_dst, h_dst, addKey)


###########
# Main loop
##########
if __name__ == "__main__":
    try:
        # create a local capped collection to store tokens
        # one for each far and near
        cols = conn_edge["_syncmetadata"].list_collection_names()
        if("Edge" not in cols):
            print("Making metadata collection...")
            conn_edge["_syncmetadata"].create_collection("Edge", capped=True, size=4096, max=100)
        if("Far" not in cols):
            print("Making metadata collection...")
            conn_edge["_syncmetadata"].create_collection("Far", capped=True, size=4096, max=100)

        # handle edge to far sync thread
        pipeline = []
        _thread.start_new_thread(watchCollection, ("Edge", handle_edge, "Far", handle_far, pipeline, True))

        # handle far to edge sync thread
        pipeline = [{"$match": {"$or":[{"fullDocument._pk":{"$in": watch_zones}}, {"operationType":"delete"}]}}]
        _thread.start_new_thread(watchCollection, ("Far", handle_far, "Edge", handle_edge, pipeline, False))
    except:
        print("Couldn't start thread")

    print("Ready...")
    while True:
        pass