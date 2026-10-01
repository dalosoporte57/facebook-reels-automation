import os
import time

import requests

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v26.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
PAGE_TOKEN = os.environ["META_PAGE_ACCESS_TOKEN"]
VIDEO_URL = os.environ["VIDEO_URL"]
TITLE = os.getenv("REEL_TITLE", "")
DESCRIPTION = os.getenv("REEL_DESCRIPTION", "")

def fail(message, response=None):
    if response is not None:
        try:
            print(response.text)
        except Exception:
            pass
    raise SystemExit(message)

print("0) Verifying Meta token and page context...")
r = requests.get(
    f"{GRAPH_BASE}/me",
    params={"fields": "id,name"},
    headers={"Authorization": f"Bearer {PAGE_TOKEN}"},
    timeout=60,
)
if not r.ok:
    fail("Meta rejected the access token. Verify that META_PAGE_ACCESS_TOKEN contains the Page Access Token.", r)

me = r.json()
print(f"   Meta context: id={me.get('id')} name={me.get('name')}")
if me.get("id") != "131757838109373":
    fail(
        "The token is valid, but it is not the Page Access Token for Finanzas con Propósito Eterno (page 131757838109373)."
    )

print("1) Creating Reel upload session...")
r = requests.post(
    f"{GRAPH_BASE}/me/video_reels",
    params={"upload_phase": "start"},
    headers={"Authorization": f"Bearer {PAGE_TOKEN}"},
    timeout=60,
)
if not r.ok:
    fail("Could not create the Reel upload session.", r)

data = r.json()
video_id = data.get("video_id")
upload_url = data.get("upload_url")
if not video_id or not upload_url:
    fail(f"Meta did not return video_id/upload_url: {data}")

print(f"   video_id={video_id}")

print("2) Sending the video to Meta...")
r = requests.post(
    upload_url,
    headers={
        "Authorization": f"OAuth {PAGE_TOKEN}",
        "file_url": VIDEO_URL,
    },
    timeout=300,
)
if not r.ok:
    fail("Video upload request failed.", r)

upload_result = r.json()
print(f"   upload response: {upload_result}")
if not upload_result.get("success"):
    fail("Meta did not confirm the upload.")

print("3) Waiting for Meta to process the video...")
for attempt in range(1, 31):
    time.sleep(5)
    r = requests.get(
        f"{GRAPH_BASE}/{video_id}",
        params={"fields": "status"},
        headers={"Authorization": f"Bearer {PAGE_TOKEN}"},
        timeout=60,
    )
    if not r.ok:
        fail("Could not read Reel processing status.", r)

    status = r.json().get("status", {})
    print(f"   check {attempt}: {status}")

    video_status = status.get("video_status")
    if video_status in {"ready", "published"}:
        break
    if video_status == "error":
        fail(f"Meta reported a processing error: {status}")
else:
    fail("Timed out waiting for Meta to finish processing.")

print("4) Publishing the Reel...")
params = {
    "upload_phase": "finish",
    "video_id": video_id,
    "video_state": "PUBLISHED",
}
if TITLE:
    params["title"] = TITLE
if DESCRIPTION:
    params["description"] = DESCRIPTION

r = requests.post(
    f"{GRAPH_BASE}/me/video_reels",
    params=params,
    headers={"Authorization": f"Bearer {PAGE_TOKEN}"},
    timeout=60,
)
if not r.ok:
    fail("Could not publish the Reel.", r)

publish_result = r.json()
print(f"   publish response: {publish_result}")
if not publish_result.get("success"):
    fail("Meta did not acknowledge the publish request.")

print("SUCCESS: Meta accepted the Reel for publication.")
