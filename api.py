import os
from frame_analysis import main, get_quality
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import inspect
from pathlib import PurePath
import glob
import json
from bson.objectid import ObjectId
try:
    from fastapi import FastAPI, Request
    import uvicorn
    from pymongo import MongoClient
    import clique
    import requests
except ImportError:
    import pip, site
    from importlib import reload
    pip.main(["install", "fastapi", "-q"])
    pip.main(["install", "uvicorn", "-q"])
    pip.main(["install", "requests", "-q"])
    pip.main(["install", "clique", "-q"])
    reload(site)
    from fastapi import FastAPI, Request
    from pymongo import MongoClient
    import uvicorn
    import clique
    import requests

def index(input, address):

    # Get Mongo Database
    client = MongoClient(address[0])
    db_name = address[1]
    collection_name = address[2]
    if db_name in client.list_database_names():
        db = client.get_database(db_name)
    else:
        db = client[db_name]
    if collection_name in db.list_collection_names():
        collection = db.get_collection(collection_name)
    else:
        collection = db[collection_name]

    # Check for existing doc
    doc = collection.find_one({"path":input})
    if doc is None:
        return [collection]
    else:
        return collection, doc["_id"], doc["quality"], doc["thumbnail"], doc["num_frames"], doc["processing"]

def request(CUE_API_URL, API_VERSION, method, data=None):
    url = f"http://{CUE_API_URL}/api/{API_VERSION}/{method}"
    if not data:
        resp = requests.get(url)
    else:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=data)
    return resp.json()


def process (input, frame_cap = 100, quality = 0.5, color_weight = -1, focus_weight = -1, farm = True, threads = 4, 
             db_address = ["ws-vm02:27117","frame_analysis","thumbnail_gen"], cue_address = [os.environ.get("CUE_API_URL"), "v1"]):
    
    tag = input
    path = PurePath(input)
    if len(path.suffixes) != 1:
        pattern = path.name.split(".")[0] + "*" + path.suffix 
        files = glob.glob(str(PurePath(path.parent / pattern)))
        assembly = clique.assemble(files)[0][0]
        tag = assembly.head + str(assembly.indexes) + assembly.tail

    id_dic = index(tag, db_address)
    collection = id_dic[0]

    id = None
    num_frames = None
    store_quality = [frame_cap, quality, None]
    if len(id_dic) != 1:
        if id_dic[5] is True:
            return id_dic[3], id
        store_quality = get_quality(frame_cap, quality, id_dic[4])
        if store_quality[1] <= id_dic[2]:
            return id_dic[3], id
        else:
            id = str(id_dic[1])

    if id is None:
        doc = collection.insert_one({
            "thumbnail": None,
            "quality": store_quality[1],
            "path": tag,
            "num_frames": num_frames,
            "processing": True
        })
        id = str(doc.inserted_id)
    else:
        collection.update_one({"_id": ObjectId(id)},{
            "$set":{
                "quality": store_quality[1],
                "processing": True
            }
        })
    
    if farm is False:
        result = main(input, store_quality, color_weight, focus_weight, db_address, id)

    else:           
        args = {
            "input": input, 
            "store_quality": store_quality, 
            "color_weight": color_weight, 
            "focus_weight": focus_weight,
            "db_address": db_address,
            "id": id
        }
        
        layers ={
                "type": "base",
                "service": "postprocess",
                "kwargs": {
                    "name": f"target_{path.__hash__()}",
                    "command": f"python {os.path.abspath(inspect.getmodule(main).__file__)} '{json.dumps(args)}'"
                },
                "settings": {
                    "start": 1001,
                    "end": 1001,
                    "step": 1,
                    "chunk_size": 1,
                    "cores": threads
                }
            }
        return layers, id

    return result, id
        

def parallel (input, frame_cap = 100, quality = 0.5, color_weight = -1, focus_weight = -1, farm = True, priority = 100, farm_threads = 4, 
             db_address = ["ws-vm02:27117","frame_analysis","thumbnail_gen"], cue_address = [os.environ.get("CUE_API_URL"), "v1"], submission_threads = None):
    
    outline = {
        "name": f"thumnail_gen_{datetime.now().strftime('%H-%M-%S_%d-%m-%y')}",
        "priority": priority,
    }
    single = False
    if type(input) is str:
        results_tuple = [process(input, frame_cap, quality, color_weight, focus_weight, farm, farm_threads, db_address, cue_address)]
        results = [results_tuple[0][0]]
        single = True
    else:
        with ProcessPoolExecutor(submission_threads) as exe:
            futures = [exe.submit(process, i, frame_cap, quality, color_weight, focus_weight, farm, farm_threads, db_address, cue_address ) for i in input]
            results_tuple = [f.result() for f in futures]
            results = [r[0] for r in results_tuple]
        
    if farm is True:
        collection = MongoClient(db_address[0]).get_database(db_address[1]).get_collection(db_address[2])
        layers = []
        strip = []
        for count, r in enumerate(results):
            if type(r) is dict:
                layers.append(r)
                strip.append(count)

        if len(layers) != 0:
            data = {
                "outline": outline,
                "layers": layers,
                "env": dict(os.environ)
            }

            cue_api, cue_version = cue_address
            if cue_api is None:
                cue_api = "ws-vm02:8087"

            result = request(cue_api, cue_version, "create_job", data)["data"][0]

            for s in strip:
                results[s] = result

                collection.update_one({"_id": ObjectId(results_tuple[s][1])},{
                    "$set":{
                        "thumbnail": result
                    }
                })        
    if single:
        results = results[0]

    return results
                
# Add process to api
app = FastAPI()
@app.post("/process")
async def run(request: Request):
    request = await request.json()
    #result = process(**request)
    result = parallel(**request)
    return result

# Start api
if __name__ == "__main__":
    uvicorn.run(
        f"{__name__}:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        workers=1,
        reload = True
    )

    