import pymongo
from bson.objectid import ObjectId
import _thread
from bson.json_util import dumps
from datetime import datetime
import os
import time

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
logMessages = []

##########
# implement whatever business logic you want to process a change
# the reason of the writeLog and asyncLogger is to update the CLI output when events happen but if we wrote direct to CLI each time, it would slow things down and be too slow. Instead write changes to an array and print one status update every 5 seconds
##########
def writeLog(msg):
    global logMessages
    logMessages.append(msg)

def asyncLogger():
    global logMessages
    try:
        waitTime = 5
        time.sleep(waitTime)
        print("Had " + str(len(logMessages)) + " messages over last "+str(waitTime)+", the last of which is:")
        print("\t"+logMessages[-1])
        logMessages = []
    except:
        print("No log messages")
        pass
    finally:
        _thread.start_new_thread(asyncLogger, ())

def processChange(token, change, sourceName, targetName, handle, h_src, addKey):
    try:
        # it was an insert
        if(change["operationType"] == "insert"):
            newDoc = change["fullDocument"]
            writeLog("Inserting document into %s...\n\t\tResume Token Ending %s"%(targetName, token["_data"][10]+token["_data"][-10:]))
            
            # region doc cleanup
            if addKey:
                if("_pk" not in newDoc):
                    newDoc["_pk"] = zone_name
                    h_src.update_one({"_id":newDoc["_id"]}, {"$set":{"_pk":zone_name}})
            # endregion

            handle.insert_one(newDoc)
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"insert"})

        # it was an update
        if(change["operationType"] == "update"):
            newDoc = change["fullDocument"]
            writeLog("Updating document in %s...\n\t\tResume Token Ending %s"%(targetName, token["_data"][10]+token["_data"][-10:]))

            # naive approach
            #handle.replace_one({"_id":change["documentKey"]["_id"]}, newDoc)
            #conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"update"})

            # process what was updated
            updateStatement = {}
            if "updatedFields" in change["updateDescription"]:
                updateStatement["$set"] = {}
                updateStatement["$set"] = change["updateDescription"]["updatedFields"]
            if "removedFields" in change["updateDescription"]:
                updateStatement["$unset"] = {}
                for removed in change["updateDescription"]["removedFields"]:
                    updateStatement["$unset"][removed] = ""
            handle.update_one({"_id":change["documentKey"]["_id"]}, updateStatement)
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"update"})

        # it was a replace
        if(change["operationType"] == "replace"):
            newDoc = change["fullDocument"]
            writeLog("Replacing document in %s...\n\t\tResume Token Ending %s"%(targetName, token["_data"][10]+token["_data"][-10:]))

            handle.replace_one({"_id":change["documentKey"]["_id"]}, newDoc)
            conn_edge["_syncmetadata"][sourceName].insert_one({"srcResumeToken":token, "was":"update"})
        # it was an delete
        if(change["operationType"] == "delete"):
            writeLog("Deleting document from %s...\n\t\tResume Token Ending %s"%(targetName, token["_data"][10]+token["_data"][-10:]))
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
                processChange(resume_token, change, name_src, name_dst, h_dst, h_src, addKey)
                
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
                    processChange(resume_token, insert_change, name_src, name_dst, h_dst, h_src, addKey)


###########
# Main loop
##########
if __name__ == "__main__":
    # this will cause a recursive loop. however mongodb will detect
    # a NOP on the recursive replace and thus "cancel" the recursion thereafter
    watch_zones.append(zone_name)
    logMessages=[]
    
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

        # logging thread
        _thread.start_new_thread(asyncLogger, ())

        # handle edge to far sync thread
        pipeline = [{"$match": {"operationType":{"$ne":"replace"}}}]
        _thread.start_new_thread(watchCollection, ("Edge", handle_edge, "Far", handle_far, pipeline, True))

        # handle far to edge sync thread
        pipeline = [{"$match": {"$or":[{"fullDocument._pk":{"$in": watch_zones}}, {"operationType":"delete"}]}}]
        _thread.start_new_thread(watchCollection, ("Far", handle_far, "Edge", handle_edge, pipeline, False))
    except:
        print("Couldn't start thread")

    print("Ready...")
    while True:
        pass
