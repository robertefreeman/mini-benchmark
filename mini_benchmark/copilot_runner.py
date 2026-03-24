from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from .telemetry import parse_log_dir


class CopilotInvocationError(RuntimeError):
    pass


def extract_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise ValueError("No JSON object found in Copilot response")


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def parse_solution_response(text: str) -> dict[str, str]:
    try:
        payload = extract_json_object(text)
        if isinstance(payload.get("solution"), str):
            return {
                "solution": strip_code_fence(payload["solution"]).strip() + "\n",
                "notes": str(payload.get("notes", "")).strip(),
            }
    except ValueError:
        pass
    return {"solution": strip_code_fence(text).strip() + "\n", "notes": ""}


def parse_plan_response(text: str) -> dict[str, Any]:
    payload = extract_json_object(text)
    return {
        "algorithm": str(payload.get("algorithm", "")).strip(),
        "edge_cases": [str(item).strip() for item in payload.get("edge_cases", [])],
        "pitfalls": [str(item).strip() for item in payload.get("pitfalls", [])],
    }


def parse_review_response(text: str) -> dict[str, Any]:
    payload = extract_json_object(text)
    raw_will_pass = payload.get("will_pass", False)
    if isinstance(raw_will_pass, bool):
        will_pass = raw_will_pass
    else:
        will_pass = str(raw_will_pass).strip().lower() in {"true", "1", "yes"}
    return {
        "will_pass": will_pass,
        "reason": str(payload.get("reason", "")).strip(),
        "correctness_issues": [
            str(item).strip() for item in payload.get("correctness_issues", [])
        ],
    }


def run_copilot_prompt(
    *,
    copilot_bin: str,
    common_args: tuple[str, ...],
    model: str,
    reasoning_effort: str,
    prompt: str,
    working_dir: Path,
    artifact_dir: Path,
    stage_name: str,
    resume_session_id: str | None = None,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    log_dir = artifact_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = artifact_dir / "prompt.txt"
    stdout_path = artifact_dir / "stdout.jsonl"
    stderr_path = artifact_dir / "stderr.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    command = [
        str(Path(copilot_bin).expanduser()),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "-p",
        prompt,
        *common_args,
        "--log-dir",
        str(log_dir),
    ]
    if resume_session_id:
        command.insert(1, f"--resume={resume_session_id}")

    started_at = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=working_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_seconds = time.monotonic() - started_at

    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        raise CopilotInvocationError(
            f"Copilot stage '{stage_name}' failed with exit code {completed.returncode}. "
            f"See {stderr_path} and {stdout_path}."
        )

    final_text = ""
    latest_assistant_message = ""
    session_id = None
    session_duration_ms = None
    events = []

    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(event)
        if event.get("type") == "assistant.message":
            data = event.get("data", {})
            content = data.get("content")
            if isinstance(content, str) and content:
                latest_assistant_message = content
                if data.get("phase") == "final_answer":
                    final_text = content
        elif event.get("type") == "result":
            session_id = event.get("sessionId")
            usage = event.get("usage", {})
            session_duration_ms = usage.get("sessionDurationMs")

    if not final_text and latest_assistant_message:
        final_text = latest_assistant_message

    usage_by_model = parse_log_dir(log_dir)
    selected_usage = usage_by_model.get(model)
    if selected_usage is None and len(usage_by_model) == 1:
        selected_usage = next(iter(usage_by_model.values()))
    if selected_usage is None:
        selected_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "request_count": 0,
            "request_cost_units": 0,
        }

    return {
        "stage": stage_name,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "resume_session_id": resume_session_id,
        "prompt_path": str(prompt_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "log_dir": str(log_dir),
        "session_id": session_id,
        "session_duration_ms": session_duration_ms,
        "wall_time_seconds": round(elapsed_seconds, 6),
        "response_text": final_text.strip(),
        "token_usage": selected_usage,
        "token_usage_by_model": usage_by_model,
        "event_count": len(events),
    }
