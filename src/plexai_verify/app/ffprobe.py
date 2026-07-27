import json
import subprocess
from pathlib import Path

from plexai_verify.app.media_support import validate_media_source


def _as_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def analyze_video(filepath, ffprobe_path):
    validate_media_source(filepath)
    exe = Path(ffprobe_path)
    if not exe.exists():
        raise FileNotFoundError(f"FFprobe introuvable : {ffprobe_path}")

    command = [
        str(exe), "-v", "error",
        "-show_streams", "-show_format",
        "-of", "json", filepath
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Erreur FFprobe")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    fmt = data.get("format", {})

    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    subs = [s for s in streams if s.get("codec_type") == "subtitle"]

    transfer = str(video.get("color_transfer", "")).lower()
    side = json.dumps(video.get("side_data_list", [])).lower()
    if "dovi" in side or "dolby vision" in side:
        hdr = "Dolby Vision"
    elif transfer == "smpte2084":
        hdr = "HDR10"
    elif transfer == "arib-std-b67":
        hdr = "HLG"
    else:
        hdr = "SDR"

    def langs(items):
        return ", ".join(sorted({
            str(s.get("tags", {}).get("language", "und")).upper()
            for s in items
        }))

    try:
        duration = float(fmt.get("duration", 0))
    except Exception:
        duration = 0.0

    channels = max(
        (_as_int(s.get("channels")) or 0 for s in audios),
        default=0,
    ) or None

    video_bitrate = (
        _as_int(video.get("bit_rate"))
        or _as_int(fmt.get("bit_rate"))
    )

    return {
        "duration": duration,
        "width": video.get("width"),
        "height": video.get("height"),
        "video_codec": str(video.get("codec_name", "")).upper(),
        "video_bitrate": video_bitrate,
        "audio_codec": ", ".join(sorted({
            str(s.get("codec_name", "")).upper()
            for s in audios if s.get("codec_name")
        })),
        "audio_channels": channels,
        "audio_languages": langs(audios),
        "subtitle_languages": langs(subs),
        "hdr": hdr,
    }
