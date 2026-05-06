"""Call Gemini 2.5 Pro on Vertex AI to extract moments from a video segment."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from google import genai
from google.genai import types

from .config import Config

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "OFF"},
]


class MomentExtractor:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.client = genai.Client(
            project=cfg.project_id, location=cfg.location, vertexai=True
        )
        prompts_dir = cfg.project_root / "prompts" / "moments"
        self.system_instruction = (prompts_dir / "system_instruction.txt").read_text(
            encoding="utf-8"
        )
        self.prompt_template = (prompts_dir / "prompt.txt").read_text(encoding="utf-8")
        schema_path = cfg.project_root / "schemas" / "moments.json"
        self.response_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def _generate_with_retry(
        self,
        contents,
        config,
        max_retries: int = 5,
        initial_delay: float = 2.0,
        backoff: float = 2.0,
        max_delay: float = 60.0,
    ):
        delay = initial_delay
        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return self.client.models.generate_content(
                    model=self.cfg.gemini_model,
                    contents=contents,
                    config=config,
                )
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                rate_limited = (
                    "429" in msg
                    or "RESOURCE_EXHAUSTED" in msg
                    or "rate limit" in msg.lower()
                    or "quota" in msg.lower()
                )
                if not rate_limited or attempt == max_retries:
                    raise
                wait = min(delay, max_delay)
                print(f"[extractor] 429 on attempt {attempt + 1}, sleeping {wait:.1f}s")
                time.sleep(wait)
                delay *= backoff
        raise RuntimeError(f"extractor exhausted retries: {last_err}")

    def extract_segment(
        self,
        gcs_uri: str,
        segment_start: int,
        segment_end: int,
    ) -> List[Dict[str, Any]]:
        """Run Gemini on one segment and return moments with ABSOLUTE timestamps."""
        seg_duration = segment_end - segment_start
        prompt_text = self.prompt_template.format(
            segment_start_seconds=segment_start,
            segment_end_seconds=segment_end,
            segment_duration_seconds=seg_duration,
        )
        video_part = types.Part(
            file_data=types.FileData(file_uri=gcs_uri, mime_type="video/mp4"),
            video_metadata=types.VideoMetadata(
                start_offset=f"{segment_start}s",
                end_offset=f"{segment_end}s",
            ),
        )
        contents = [
            types.Content(
                role="user",
                parts=[video_part, types.Part.from_text(text=prompt_text)],
            )
        ]
        gen_config = types.GenerateContentConfig(
            temperature=0,
            top_p=0.95,
            system_instruction=self.system_instruction,
            response_modalities=["TEXT"],
            safety_settings=SAFETY_SETTINGS,
            response_mime_type="application/json",
            response_schema=self.response_schema,
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
            audio_timestamp=True,
        )
        resp = self._generate_with_retry(contents, gen_config)
        data = json.loads(resp.text)
        moments = data.get("response", {}).get("moments", [])

        # Offset segment-relative timestamps back to source-video timestamps.
        absolute: List[Dict[str, Any]] = []
        for m in moments:
            m = dict(m)
            m["start_seconds"] = int(m.get("start_seconds", 0)) + segment_start
            m["end_seconds"] = int(m.get("end_seconds", 0)) + segment_start
            absolute.append(m)
        return absolute

    def extract_video(
        self,
        gcs_uri: str,
        segments: List[Tuple[int, int]],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for i, (s, e) in enumerate(segments):
            print(f"[extractor] segment {i + 1}/{len(segments)}: {s}-{e}s")
            out.extend(self.extract_segment(gcs_uri, s, e))
        return out
