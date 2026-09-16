import os
import sys
import time
from huggingface_hub import HfApi

# Reads from GitHub Secrets / Environment
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_REPO_ID = os.environ.get("HF_REPO_ID")  # Format: "your-username/story-videos"

if not HF_TOKEN or not HF_REPO_ID:
    print("❌ Error: Missing HF_TOKEN or HF_REPO_ID environment variable.")
    sys.exit(1)

api = HfApi(token=HF_TOKEN)

def upload():
    timestamp = int(time.time())
    folder_name = f"video_{timestamp}"
    
    files_to_upload = {
        "temp_render.webm": f"{folder_name}/video.webm",
        "captions.sbv": f"{folder_name}/captions.sbv",
        "metadata.json": f"{folder_name}/metadata.json",
        "timed_story.json": f"{folder_name}/story.json"
    }

    print(f"☁️ Uploading batch to Hugging Face: {HF_REPO_ID}/{folder_name}...")
    
    for local_file, hf_path in files_to_upload.items():
        if os.path.exists(local_file):
            api.upload_file(
                path_or_fileobj=local_file,
                path_in_repo=hf_path,
                repo_id=HF_REPO_ID,
                repo_type="dataset"
            )
            print(f"✅ Uploaded: {hf_path}")

    # Output direct URL for latest build
    direct_url = f"https://huggingface.co/datasets/{HF_REPO_ID}/resolve/main/{folder_name}/video.webm"
    print(f"\n🎉 Public Video Direct URL:\n{direct_url}")

if __name__ == "__main__":
    upload()
