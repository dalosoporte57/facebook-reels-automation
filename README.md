# Facebook Reels Automation

This repository automates the Facebook Reels Publishing API flow:

1. Create an upload session.
2. Send the video to Meta's upload endpoint.
3. Poll the processing status.
4. Publish the Reel.

The workflow is manual for now. Scheduling will be added only after the first end-to-end test succeeds.

## Required GitHub Secret

Create this repository secret:

- `META_PAGE_ACCESS_TOKEN` — your Page Access Token. Never put the token in source code.

## Running

GitHub Actions → Publish Facebook Reel → Run workflow.

The `video_url` must be a direct HTTPS URL that Meta can fetch.

Meta's current official Reels sample is available at:
https://github.com/fbsamples/reels_publishing_apis
