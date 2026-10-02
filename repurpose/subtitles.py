import os
import math
from typing import List, Dict, Any

def format_timestamp(seconds: float) -> str:
    """Converts seconds into SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_ass_timestamp(seconds: float) -> str:
    """Converts seconds into ASS timestamp: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int(round((seconds - int(seconds)) * 100))
    if centisecs >= 100:
        centisecs = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def generate_srt_from_audio(audio_path: str, output_srt_path: str) -> str:
    """
    Uses local Whisper to transcribe audio with word/segment timestamps
    and generate an optimized, high-readability SRT subtitle file.
    """
    os.makedirs(os.path.dirname(output_srt_path), exist_ok=True)
    
    try:
        import whisper
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_path, word_timestamps=True, language="en")
        
        segments = result.get("segments", [])
        srt_lines = []
        counter = 1
        
        for seg in segments:
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "").strip()
            
            if not text:
                continue
                
            # If segment is too long, break words into short punchy 4-5 word phrases (viral short style)
            words = seg.get("words", [])
            if len(words) > 5:
                chunk_size = 4
                for i in range(0, len(words), chunk_size):
                    chunk = words[i:i + chunk_size]
                    c_start = chunk[0]["start"]
                    c_end = chunk[-1]["end"]
                    c_text = " ".join([w["word"].strip() for w in chunk])
                    
                    srt_lines.append(f"{counter}")
                    srt_lines.append(f"{format_timestamp(c_start)} --> {format_timestamp(c_end)}")
                    srt_lines.append(c_text)
                    srt_lines.append("")
                    counter += 1
            else:
                srt_lines.append(f"{counter}")
                srt_lines.append(f"{format_timestamp(start)} --> {format_timestamp(end)}")
                srt_lines.append(text)
                srt_lines.append("")
                counter += 1
                
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
            
        return output_srt_path
    except Exception as e:
        print(f"[Subtitles] Whisper SRT generation failed: {e}")
        # Write blank fallback
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("")
        return output_srt_path

def generate_ass_from_audio(
    audio_path: str,
    output_ass_path: str,
    format_mode: str = "shorts_9_16",
    caption_color: str = "yellow"
) -> str:
    """
    Transcribes audio with Whisper and generates authentic CapCut kinetic ASS subtitles
    with word-by-word karaoke bounce and active highlight pop.
    """
    os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)

    # Color palette (ASS &HAABBGGRR)
    color_map = {
        "yellow": "&H0000FFFF&",
        "cyan": "&H00FFFF00&",
        "emerald": "&H0050FA7B&",
        "white": "&H00FFFFFF&"
    }
    highlight_ass = color_map.get(caption_color.lower(), "&H0000FFFF&")

    is_vertical = (format_mode == "shorts_9_16")
    res_x = 720 if is_vertical else 1280
    res_y = 1280 if is_vertical else 720
    font_size = 46 if is_vertical else 34
    margin_v = 240 if is_vertical else 60

    header = f"""[Script Info]
Title: CapCut Kinetic Repurpose Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCutBurst,Impact,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,4.0,2.0,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    try:
        import whisper
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_path, word_timestamps=True, language="en")
        segments = result.get("segments", [])

        for seg in segments:
            words = seg.get("words", [])
            if not words:
                text = seg.get("text", "").strip().upper()
                if not text:
                    continue
                start_str = format_ass_timestamp(seg.get("start", 0.0))
                end_str = format_ass_timestamp(seg.get("end", 0.0))
                events.append(f"Dialogue: 0,{start_str},{end_str},CapCutBurst,,0,0,0,,{text}")
                continue

            # Group into 3-word kinetic bursts
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                if not chunk:
                    continue

                for j, target_w in enumerate(chunk):
                    w_start = format_ass_timestamp(target_w["start"])
                    w_end = format_ass_timestamp(target_w["end"])

                    # Build kinetic line: current word is highlighted & zoomed, other words white
                    tokens = []
                    for k, item in enumerate(chunk):
                        word_str = item["word"].strip().upper().replace("{", "").replace("}", "")
                        if k == j:
                            tokens.append(f"{{\\c{highlight_ass}\\fscx112\\fscy112}}{word_str}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                        else:
                            tokens.append(f"{{\\c&H00FFFFFF&}}{word_str}")

                    line_text = " ".join(tokens)
                    events.append(f"Dialogue: 0,{w_start},{w_end},CapCutBurst,,0,0,0,,{line_text}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events) + "\n")
        return output_ass_path

    except Exception as e:
        print(f"[Subtitles] ASS generation failed: {e}")
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n")
        return output_ass_path
