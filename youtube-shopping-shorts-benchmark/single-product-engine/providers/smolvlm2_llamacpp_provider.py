#!/usr/bin/env python3
"""Local SmolVLM2/llama.cpp provider for Shopping Shorts scene semantics.

Reads one bound ``shopping_shorts_vision_observation_request`` JSON object from stdin and
writes provider observations JSON to stdout. The script uses llama.cpp's OpenAI-compatible
multimodal ``/v1/chat/completions`` endpoint and sends every requested keyframe for a
segment in early/mid/late order.

Evidence discipline:
- exact frame-file identity is handled by the outer run_vision_provider_adapter.py;
- model-derived scene semantics are never promoted to ``confirmed`` here;
- usable model observations are emitted as ``estimated``;
- ambiguous/unusable observations remain ``unknown``;
- audio/BGM/SFX/Foley/spoken-word claims remain ``unknown`` because this provider only
  submits still keyframes.

The default deployment target is ggml-org/SmolVLM2-500M-Video-Instruct-GGUF served by
llama.cpp, but the provider is protocol-compatible with other local multimodal models.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = os.environ.get("SHORTS_VLM_BASE_URL", "http://127.0.0.1:8080/v1")
DEFAULT_TIMEOUT_SEC = 120.0
DEFAULT_MAX_TOKENS = 320
DEFAULT_MAX_FRAME_BYTES = 5 * 1024 * 1024


def read_request() -> dict[str, Any]:
    value = json.load(sys.stdin)
    if not isinstance(value, dict):
        raise ValueError("stdin request must be a JSON object")
    if value.get("format") != "shopping_shorts_vision_observation_request":
        raise ValueError("unsupported request format")
    segments = value.get("segment_requests")
    if not isinstance(segments, list) or not segments:
        raise ValueError("segment_requests missing")
    return value


def http_json(url: str, *, payload: dict[str, Any] | None, timeout_sec: float) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[-1200:]
        raise RuntimeError(f"llama.cpp HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"llama.cpp transport error: {exc.reason}") from exc
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("llama.cpp response must be a JSON object")
    return value


def discover_model(base_url: str, timeout_sec: float) -> str:
    response = http_json(base_url.rstrip("/") + "/models", payload=None, timeout_sec=timeout_sec)
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("llama.cpp /models returned no models")
    model_id = str(data[0].get("id", "")).strip() if isinstance(data[0], dict) else ""
    if not model_id:
        raise RuntimeError("llama.cpp /models first entry has no id")
    return model_id


def image_data_url(path: Path, max_frame_bytes: int) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size <= 0:
        raise ValueError(f"empty image: {path}")
    if size > max_frame_bytes:
        raise ValueError(f"image exceeds max-frame-bytes ({size}>{max_frame_bytes}): {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError(f"unsupported keyframe MIME type {mime!r}: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def segment_schema(allowed_tags: list[str], sample_names: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "observable": {"type": "boolean"},
            "description": {"type": "string"},
            "content_keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            "semantic_tags": {"type": "array", "items": {"type": "string", "enum": allowed_tags}, "maxItems": 8},
            "quality_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "preferred_visual_sample": {"type": "string", "enum": sample_names + [""]},
        },
        "required": ["observable", "description", "content_keywords", "semantic_tags", "quality_score", "preferred_visual_sample"],
        "additionalProperties": False,
    }


def prompt_for_segment(request: dict[str, Any], segment: dict[str, Any], sample_names: list[str]) -> str:
    locale = str(request.get("locale", "ko-KR"))
    product = str(request.get("product_name", "")).strip()
    claims = request.get("claims_context", {})
    allowed = [str(x) for x in request.get("allowed_semantic_tags", [])]
    return (
        "Inspect every attached image as ordered visual evidence for ONE segment of a single-product shopping Short. "
        "Describe only directly visible facts. Do not infer audio, speech, BGM, SFX, Foley, price, popularity, hidden "
        "features, efficacy, durability, or events not visible in these frames. The caller product name is context only, "
        "not proof that the exact product identity is visible. If the scene is ambiguous or no controlled semantic tag "
        "is visually supported, set observable=false and return empty description/keywords/tags. "
        f"Write the description/keywords in locale {locale}. Use semantic_tags ONLY from this exact list: {allowed}. "
        f"Images are ordered by samples {sample_names}. preferred_visual_sample must be one of those names or an empty string. "
        "quality_score is visual usability for editing (clarity/framing/action visibility), not product quality. "
        f"Product context: {product!r}. Caller claims context (not visual proof): {json.dumps(claims, ensure_ascii=False)}. "
        f"Segment: {segment.get('source_clip_id')}/{segment.get('segment_id')} "
        f"from {segment.get('segment_start_sec')}s to {segment.get('segment_end_sec')}s."
    )


def parse_model_content(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RuntimeError("llama.cpp response missing choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError("llama.cpp response missing message")
    content = message.get("content")
    if isinstance(content, dict):
        value = content
    elif isinstance(content, str):
        value = json.loads(content)
    else:
        raise RuntimeError("llama.cpp message content is not JSON text/object")
    if not isinstance(value, dict):
        raise RuntimeError("model segment response must be an object")
    return value


def normalize_string_list(value: Any, *, allowed: set[str] | None = None, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in out:
            continue
        if allowed is not None and text not in allowed:
            continue
        out.append(text)
        if len(out) >= limit:
            break
    return out


def analyze_segment(request: dict[str, Any], segment: dict[str, Any], *, base_url: str, model: str, timeout_sec: float, max_tokens: int, temperature: float, max_frame_bytes: int) -> dict[str, Any]:
    frames = segment.get("visual_evidence")
    if not isinstance(frames, list) or not frames:
        raise ValueError("segment visual_evidence missing")
    sample_names = [str(frame.get("sample", "frame")).strip() or "frame" for frame in frames]
    paths = [str(frame.get("path", "")).strip() for frame in frames]
    if any(not path for path in paths):
        raise ValueError("segment contains blank visual evidence path")
    if len(set(sample_names)) != len(sample_names):
        raise ValueError("segment visual evidence sample names must be unique")
    allowed_tags = sorted({str(x) for x in request.get("allowed_semantic_tags", []) if str(x).strip()})
    if not allowed_tags:
        raise ValueError("allowed_semantic_tags missing")
    user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt_for_segment(request, segment, sample_names)}]
    for path in paths:
        user_content.append({"type": "image_url", "image_url": {"url": image_data_url(Path(path), max_frame_bytes)}})
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "messages": [
            {"role": "system", "content": "You are a conservative visual evidence annotator. Output only schema-valid JSON and never upgrade uncertain evidence."},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_schema", "schema": segment_schema(allowed_tags, sample_names)},
    }
    raw = http_json(base_url.rstrip("/") + "/chat/completions", payload=payload, timeout_sec=timeout_sec)
    observed = parse_model_content(raw)
    tags = normalize_string_list(observed.get("semantic_tags"), allowed=set(allowed_tags))
    keywords = normalize_string_list(observed.get("content_keywords"))
    description = str(observed.get("description", "")).strip()
    observable = observed.get("observable") is True
    try:
        quality = float(observed.get("quality_score", 0.0))
    except (TypeError, ValueError):
        quality = 0.0
    quality = max(0.0, min(1.0, quality))
    preferred = str(observed.get("preferred_visual_sample", "")).strip()
    if preferred not in sample_names:
        preferred = ""
    evidence_label = "estimated" if observable and description and tags else "unknown"
    if evidence_label == "unknown":
        description = ""
        keywords = []
        tags = []
        preferred = ""
    return {
        "source_clip_id": str(segment.get("source_clip_id", "")),
        "segment_id": str(segment.get("segment_id", "")),
        "description": description,
        "content_keywords": keywords,
        "semantic_tags": tags,
        "quality_score": round(quality, 4),
        "evidence_label": evidence_label,
        "observation_basis": "visual_frames_inspected" if evidence_label == "estimated" else "unresolved",
        "inspected_visual_evidence": paths,
        "preferred_visual_sample": preferred or None,
        "audio_evidence_label": "unknown",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--model", default=os.environ.get("SHORTS_VLM_MODEL", "auto"))
    p.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-frame-bytes", type=int, default=DEFAULT_MAX_FRAME_BYTES)
    args = p.parse_args()
    if args.timeout_sec <= 0 or args.max_tokens <= 0 or args.max_frame_bytes <= 0:
        raise SystemExit("timeout/max-tokens/max-frame-bytes must be positive")
    if not 0.0 <= args.temperature <= 2.0:
        raise SystemExit("temperature must be between 0 and 2")
    try:
        request = read_request()
        model = discover_model(args.base_url, args.timeout_sec) if args.model == "auto" else args.model
        segments = [
            analyze_segment(request, segment, base_url=args.base_url, model=model, timeout_sec=args.timeout_sec, max_tokens=args.max_tokens, temperature=args.temperature, max_frame_bytes=args.max_frame_bytes)
            for segment in request["segment_requests"]
        ]
        output = {
            "product_identity": str(request.get("product_name", "")).strip() or "unknown",
            "product_identity_evidence_label": "unknown",
            "segments": segments,
            "provider_semantic_evidence_policy": "model_semantics_are_estimated_or_unknown_never_confirmed",
            "audio_evidence_label": "unknown",
        }
        print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    except Exception as exc:
        print(f"smolvlm2 provider error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
