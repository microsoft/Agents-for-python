# python >=3.10
import os, time, json, concurrent.futures, requests, random, string

DIRECT_LINE_SECRET = os.environ["DIRECT_LINE_SECRET"]  # from Direct Line channel
BASE = "https://directline.botframework.com/v3/directline"

def gen_token():
    r = requests.post(
        f"{BASE}/tokens/generate",
        headers={"Authorization": f"Bearer {DIRECT_LINE_SECRET}"},
        json={"user": {"id": "user-" + ''.join(random.choices(string.ascii_lowercase, k=6))}}
    )
    r.raise_for_status()
    return r.json()["token"]

def start_conversation(token):
    r = requests.post(
        f"{BASE}/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    return r.json()["conversationId"]

def post_message(token, conv_id, text):
    payload = {
        "type": "message",
        "from": {"id": "loader"},
        "text": text,
        "locale": "en-US"
    }
    r = requests.post(
        f"{BASE}/conversations/{conv_id}/activities",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def worker(_):
    token = gen_token()
    conv = start_conversation(token)
    results = []
    for i in range(25):  # messages per conversation
        t0 = time.perf_counter()
        post_message(token, conv, f"ping {i}")
        t1 = time.perf_counter()
        results.append(t1 - t0)
    return results
if __name__ == "__main__":
    USERS = 50   # concurrent conversations
    with concurrent.futures.ThreadPoolExecutor(max_workers=USERS) as ex:
        batches = list(ex.map(worker, range(USERS)))
    latencies = [x for b in batches for x in b]
    print(f"sent={len(latencies)}, p50={sorted(latencies)[len(latencies)//2]:.3f}s, "
          f"max={max(latencies):.3f}s")