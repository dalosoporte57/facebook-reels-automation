import os
import requests

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v26.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TOKEN = os.environ["META_PAGE_ACCESS_TOKEN"]
PAGE_ID = "131757838109373"
VIDEO_URL = os.environ["VIDEO_URL"]
TITLE = os.getenv("REEL_TITLE", "")
DESCRIPTION = os.getenv("REEL_DESCRIPTION", "")

def fail(message, response=None):
    print(message)
    if response is not None:
        try:
            print(response.text)
        except Exception:
            pass
    raise SystemExit(1)

def graph_get(path, token, **params):
    return requests.get(
        f"{GRAPH_BASE}/{path.lstrip('/')}",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )

def graph_post(path, token, **params):
    return requests.post(
        f"{GRAPH_BASE}/{path.lstrip('/')}",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )

print("0) Detecting Meta token type and Page access...")
r = graph_get("/me", TOKEN, fields="id,name")
if not r.ok:
    fail("Meta rejected META_PAGE_ACCESS_TOKEN. The GitHub secret is expired/invalid.", r)

me = r.json()
context_id = me.get("id")
context_name = me.get("name")
print(f"   Token context: id={context_id} name={context_name}")

page_token = TOKEN

if context_id != PAGE_ID:
    print("   User token detected. Getting the Page access token automatically...")
    r = graph_get(
        "/me/accounts",
        TOKEN,
        fields="id,name,access_token",
        limit=100,
    )
    if not r.ok:
        fail(
            "The token is valid, but it does not have the Page permissions needed to access "
            "Finanzas con Propósito Eterno. Regenerate the User token with pages_show_list, "
            "pages_read_engagement and pages_manage_posts, with the Page selected, then update "
            "the GitHub secret.",
            r,
        )

    pages = r.json().get("data", [])
    page = next((p for p in pages if p.get("id") == PAGE_ID), None)
    if not page or not page.get("access_token"):
        fail(
            "Meta did not return a Page access token for Finanzas con Propósito Eterno. "
            "Check that Dalo Lopez has Facebook access/full access to the Page and that the "
            "User token includes pages_show_list and pages_read_engagement.",
            r,
        )

    page_token = page["access_token"]
    print(f"   Page found: {page.get('name')} ({page.get('id')})")
else:
    print("   Page access token detected directly.")

print("1) Creating Reel upload session...")
r = graph_post(
    f"/{PAGE_ID}/video_reels",
    page_token,
    upload_phase="start",
)
if not r.ok:
    fail("Could not create the Reel upload session. Check the Page access token and Reel permissions.", r)

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
        "Authorization": f"OAuth {page_token}",
        "file_url": VIDEO_URL,
    },
    timeout=300,
)
if not r.ok:
    fail("Video upload request failed.", r)

upload_result = r.json()
print(f"   upload response: {upload_result}")
if not upload_result.get("success"):
    fail("Meta did not confirm the upload.", r)

print("3) Finishing and publishing the Reel...")
params = {
    "upload_phase": "finish",
    "video_id": video_id,
    "video_state": "PUBLISHED",
}
if TITLE:
    params["title"] = TITLE
if DESCRIPTION:
    params["description"] = DESCRIPTION

r = graph_post(f"/{PAGE_ID}/video_reels", page_token, **params)
if not r.ok:
    fail("Could not publish the Reel. Meta rejected the final publish request.", r)

publish_result = r.json()
print(f"   publish response: {publish_result}")
if not publish_result.get("success"):
    fail("Meta did not acknowledge the publish request.", r)

print("SUCCESS: Meta accepted the Reel for publication.")
