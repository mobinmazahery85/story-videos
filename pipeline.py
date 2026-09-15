import asyncio
import json
import os
import sys
import edge_tts
from pydub import AudioSegment, silence

def trim_audio_silence(file_path, silence_thresh=-45.0, min_silence_len=100):
    """Trims leading and trailing silence from an audio file."""
    audio = AudioSegment.from_file(file_path)
    # Trim leading & trailing silence
    non_silent = silence.detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if non_silent:
        start_trim = non_silent[0][0]
        end_trim = non_silent[-1][1]
        trimmed_audio = audio[start_trim:end_trim]
        trimmed_audio.export(file_path, format="mp3")
    return len(AudioSegment.from_file(file_path)) / 1000.0  # Duration in seconds

def format_sbv_timestamp(seconds):
    """Formats float seconds into YouTube .sbv timestamp (h:mm:ss.sss)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h}:{m:02d}:{s:02d}.{ms:03d}"

async def process_story(story_json_path, output_dir="tts_output"):
    os.makedirs(output_dir, exist_ok=True)
    with open(story_json_path, "r", encoding="utf-8") as f:
        story = json.load(f)

    char_profiles = story.get("characters", {
        "Me": {"voice": "en-US-AnaNeural", "rate": "+15%", "pitch": "+15Hz"},
        "Other": {"voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "-4Hz"}
    })

    timed_messages = []
    sbv_entries = []
    current_timeline = 0.0  # In seconds

    print("🎙️ 1. Synthesizing audio and computing dynamic durations...")
    for idx, msg in enumerate(story["messages"]):
        sender = msg["sender"]
        text = msg["text"]
        profile = char_profiles.get(sender, char_profiles.get("Other"))

        audio_filename = f"{idx:02d}_{sender}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)

        # Generate Audio
        communicate = edge_tts.Communicate(
            text=text,
            voice=profile["voice"],
            rate=profile.get("rate", "+0%"),
            pitch=profile.get("pitch", "+0Hz")
        )
        await communicate.save(audio_path)

        # Trim Silence & get exact spoken duration
        audio_duration = trim_audio_silence(audio_path)

        # Typing duration calculated dynamically (fast for UI animation)
        typing_dur = 0.6 if idx == 0 else min(1.2, max(0.4, len(text) * 0.025))
        typing_dur_ms = int(typing_dur * 1000)

        # Message start and end times on timeline
        msg_start_time = current_timeline + typing_dur
        msg_end_time = msg_start_time + audio_duration
        
        # Buffer after speaking before next message starts (in ms)
        next_delay = 0.8  # 800ms natural reading gap
        
        timed_messages.append({
            "sender": sender,
            "text": text,
            "audioFile": audio_filename,
            "typingDuration": typing_dur_ms,
            "audioDuration": audio_duration,
            "nextTimeDelta": int(next_delay * 1000)
        })

        # Generate SBV Subtitle Entry
        sbv_entries.append(
            f"{format_sbv_timestamp(msg_start_time)},{format_sbv_timestamp(msg_end_time)}\n{text}\n"
        )

        current_timeline = msg_end_time + next_delay

    # Save Timed Story for the Renderer
    story["messages"] = timed_messages
    story["totalDuration"] = current_timeline
    with open("timed_story.json", "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2)

    # Save .sbv Subtitle file
    with open("captions.sbv", "w", encoding="utf-8") as f:
        f.write("\n".join(sbv_entries))

    # Save Metadata JSON for Control Panel
    metadata = story.get("metadata", {
        "title": story.get("chatTitle", "Scary Text Story") + " 📱😨",
        "description": "Watch until the end! Subscribe for daily stories! #shorts #horror #scary #textstory",
        "tags": "scary text stories, horror shorts, 3am text stories, minecraft"
    })
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Audio processing complete! Total video runtime: {current_timeline:.2f}s")

if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "story.json"
    asyncio.run(process_story(json_path))
