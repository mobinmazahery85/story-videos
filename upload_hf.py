import os
import sys
import time
from huggingface_hub import HfApi

HF_TOKEN = os.environ.get("HF_TOKEN")
HF_REPO_ID = os.environ.get("HF_REPO_ID")
TARGET_FOLDER = os.environ.get("TARGET_FOLDER") or f"video_{int(time.time())}"

if not HF_TOKEN or not HF_REPO_ID:
    print("❌ Error: Missing HF_TOKEN or HF_REPO_ID environment variable.")
    sys.exit(1)

api = HfApi(token=HF_TOKEN)

def upload():
    files_to_upload = {
        "final_output.mp4": f"{TARGET_FOLDER}/video.mp4",
        "captions.sbv": f"{TARGET_FOLDER}/captions.sbv",
        "metadata.json": f"{TARGET_FOLDER}/metadata.json",
        "timed_story.json": f"{TARGET_FOLDER}/story.json"
    }

    print(f"☁️ Uploading batch to Hugging Face: {HF_REPO_ID}/{TARGET_FOLDER}...")
    for local_file, hf_path in files_to_upload.items():
        if os.path.exists(local_file):
            api.upload_file(
                path_or_fileobj=local_file,
                path_in_repo=hf_path,
                repo_id=HF_REPO_ID,
                repo_type="dataset"
            )
            print(f"✅ Uploaded: {hf_path}")

if __name__ == "__main__":
    upload()
