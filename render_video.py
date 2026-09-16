import os
import sys
import base64
import http.server
import socketserver
import threading
import subprocess
from playwright.sync_api import sync_playwright

PORT = 8080

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

def render():
    # Start local static server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    print("🚀 Launching Headless Chromium via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        
        page.goto(f"http://localhost:{PORT}/recorder.html")
        print("⏳ Recording animation & syncing audio...")

        # Wait for render completion flag
        page.wait_for_function("window.renderComplete === true", timeout=120000)
        print("JS Console Output: " + page.evaluate("window.outputlog"))
        # Retrieve rendered Base64 WebM
        base64_data = page.evaluate("window.renderedBase64").split(",")[1]
        raw_webm = "temp_render.webm"
        with open(raw_webm, "wb") as f:
            f.write(base64.b64decode(base64_data))
            
        browser.close()

    # print("🎬 Converting WebM to high-quality 1080x1920 MP4 via FFmpeg...")
    # final_mp4 = "final_output.mp4"
    # subprocess.run([
    #     "ffmpeg", "-y", "-i", raw_webm,
    #     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
    #     "-b:v", "4500k", "-b:a", "192k", final_mp4
    # ], check=True)
    # 
    # if os.path.exists(raw_webm):
    #     os.remove(raw_webm)

    print(f"🎉 Rendering finished successfully: {raw_webm}")

if __name__ == "__main__":
    render()
