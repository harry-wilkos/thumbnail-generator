from pprint import pprint
import json
from sys import argv
try:
    import requests
except ImportError:
    import pip, site
    from importlib import reload
    pip.main(["install", "requests", "-q"])
    reload(site)

# Send and return data to api
def request(method, data):
    url = f"http://0.0.0.0:8000/{method}"
    if not data:
        resp = requests.get(url)
    else:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=data)
    return resp.json()

if __name__ == "__main__":
    args = {
        "input":input,
        "frame_cap": -1,
        "quality": 1,
        "farm_threads": 12,
        "farm": True
    }

    args = json.loads(argv[1])
    result = request("process", args)
    pprint(result)
