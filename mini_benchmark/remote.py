from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

from .config import REPO_ROOT, load_benchmark_config


def _repo_url() -> str:
    completed = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _remote_root_shell(path: str) -> str:
    return path.replace("$HOME", "${HOME}")


def _remote_root_scp(path: str) -> str:
    return path.replace("$HOME", "~")


def _run_ssh(host: str, script: str, dry_run: bool) -> None:
    command = ["ssh", host, f"bash -lc {shlex.quote(script)}"]
    if dry_run:
        print(" ".join(command))
        return
    subprocess.run(command, check=True)


def _selected_scenarios(scenario_ids: list[str] | None):
    config = load_benchmark_config()
    if not scenario_ids:
        return config.scenarios
    wanted = set(scenario_ids)
    selected = tuple(scenario for scenario in config.scenarios if scenario.id in wanted)
    found = {scenario.id for scenario in selected}
    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Unknown scenario ids: {', '.join(missing)}")
    return selected


def prepare_server(host: str, dry_run: bool = False) -> None:
    config = load_benchmark_config()
    repo_url = _repo_url()
    remote_root = _remote_root_shell(config.remote_root)
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    script = f"""
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REMOTE_ROOT={remote_root}
REPO_URL={shlex.quote(repo_url)}
BRANCH={shlex.quote(branch)}
mkdir -p "$(dirname "$REMOTE_ROOT")"
if [ -d "$REMOTE_ROOT/.git" ]; then
  git -C "$REMOTE_ROOT" fetch origin
  git -C "$REMOTE_ROOT" checkout "$BRANCH"
  git -C "$REMOTE_ROOT" pull --ff-only origin "$BRANCH"
else
  git clone "$REPO_URL" "$REMOTE_ROOT"
  git -C "$REMOTE_ROOT" checkout "$BRANCH"
fi
python3 -m venv "$REMOTE_ROOT/.venv"
"$REMOTE_ROOT/.venv/bin/pip" install --upgrade pip
"$REMOTE_ROOT/.venv/bin/pip" install -r "$REMOTE_ROOT/requirements.txt"
test -x "$HOME/.local/bin/copilot"
"""
    _run_ssh(host, script, dry_run)


def launch_remote(run_id: str, scenario_ids: list[str] | None = None, dry_run: bool = False) -> None:
    remote_root = _remote_root_shell(load_benchmark_config().remote_root)
    for scenario in _selected_scenarios(scenario_ids):
        script = f"""
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
REMOTE_ROOT={remote_root}
mkdir -p "$REMOTE_ROOT/runs/{run_id}"
cd "$REMOTE_ROOT"
nohup "$REMOTE_ROOT/.venv/bin/python" -m mini_benchmark run-scenario --scenario-id {shlex.quote(scenario.id)} --run-id {shlex.quote(run_id)} > "$REMOTE_ROOT/runs/{run_id}/{scenario.id}.stdout.log" 2>&1 < /dev/null &
echo $! > "$REMOTE_ROOT/runs/{run_id}/{scenario.id}.pid"
cat "$REMOTE_ROOT/runs/{run_id}/{scenario.id}.pid"
"""
        _run_ssh(scenario.server, script, dry_run)


def status_remote(run_id: str, scenario_ids: list[str] | None = None, dry_run: bool = False) -> None:
    remote_root = _remote_root_shell(load_benchmark_config().remote_root)
    for scenario in _selected_scenarios(scenario_ids):
        script = f"""
set -euo pipefail
REMOTE_ROOT={remote_root}
PID_FILE="$REMOTE_ROOT/runs/{run_id}/{scenario.id}.pid"
if [ ! -f "$PID_FILE" ]; then
  echo "{scenario.id}: no pid file"
  exit 0
fi
PID="$(cat "$PID_FILE")"
if ps -p "$PID" -o pid=,etime=,cmd=; then
  true
else
  echo "{scenario.id}: pid $PID not running"
fi
"""
        _run_ssh(scenario.server, script, dry_run)


def collect_results(run_id: str, scenario_ids: list[str] | None = None, dry_run: bool = False) -> None:
    config = load_benchmark_config()
    local_run_dir = REPO_ROOT / "runs" / run_id
    local_run_dir.mkdir(parents=True, exist_ok=True)
    for scenario in _selected_scenarios(scenario_ids):
        remote_root = _remote_root_scp(config.remote_root)
        remote_path = f"{scenario.server}:{remote_root}/runs/{run_id}/{scenario.id}"
        command = ["scp", "-r", remote_path, str(local_run_dir)]
        if dry_run:
            print(" ".join(command))
            continue
        subprocess.run(command, check=True)


def build_remote_parsers(subparsers) -> None:
    prepare_parser = subparsers.add_parser("prepare-server", help="Prepare one remote server")
    prepare_parser.add_argument("--host", required=True)
    prepare_parser.add_argument("--dry-run", action="store_true")
    prepare_parser.set_defaults(command="prepare-server")

    launch_parser = subparsers.add_parser("launch-remote", help="Launch selected or all configured scenarios remotely")
    launch_parser.add_argument("--run-id", required=True)
    launch_parser.add_argument("--scenario-id", action="append", dest="scenario_ids")
    launch_parser.add_argument("--dry-run", action="store_true")
    launch_parser.set_defaults(command="launch-remote")

    status_parser = subparsers.add_parser("status-remote", help="Check selected or all remote run statuses")
    status_parser.add_argument("--run-id", required=True)
    status_parser.add_argument("--scenario-id", action="append", dest="scenario_ids")
    status_parser.add_argument("--dry-run", action="store_true")
    status_parser.set_defaults(command="status-remote")

    collect_parser = subparsers.add_parser("collect-results", help="Copy selected or all remote run artifacts back locally")
    collect_parser.add_argument("--run-id", required=True)
    collect_parser.add_argument("--scenario-id", action="append", dest="scenario_ids")
    collect_parser.add_argument("--dry-run", action="store_true")
    collect_parser.set_defaults(command="collect-results")


def dispatch_remote_command(args: argparse.Namespace) -> int:
    if args.command == "prepare-server":
        prepare_server(args.host, dry_run=args.dry_run)
        return 0
    if args.command == "launch-remote":
        launch_remote(args.run_id, scenario_ids=args.scenario_ids, dry_run=args.dry_run)
        return 0
    if args.command == "status-remote":
        status_remote(args.run_id, scenario_ids=args.scenario_ids, dry_run=args.dry_run)
        return 0
    if args.command == "collect-results":
        collect_results(args.run_id, scenario_ids=args.scenario_ids, dry_run=args.dry_run)
        return 0
    raise ValueError(f"Unsupported remote command: {args.command}")
