#!/usr/bin/env python3
"""
⚠️ GÜVENLİK SINIRI DEĞİL — BEST-EFFORT TESPİT KATMANI:
Bu araç, Hermes'in kendi ürettiği log metnini analiz eden bir
post-execution audit/tespit mekanizmasıdır. GERÇEK bir
güvenlik sınırı DEĞİLDİR. Eğer Hermes'in log formatı değişirse,
bir eylem loglanmadan gerçekleşirse, veya bir regex pattern'i
bir durumu kaçırırsa, bu araç SESSİZCE yanlış "CONTAINED"
sonucu verebilir (fail-open, fail-closed DEĞİL).

Gerçek containment için TEK güvenilir yöntem OS/container
seviyesi izolasyondur (bkz. APE-SECURITY-OBS-001, TASK-007,
Hermes SECURITY.md §2.2: "The only security boundary against
an adversarial LLM is the operating system"). Bu araç yalnızca
Docker/OS izolasyonu mevcut olmadığında GEÇİCİ, İKİNCİL bir
tespit katmanı olarak kullanılmalı, birincil savunma olarak
ASLA güvenilmemelidir.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape sequences (colors, styles, cursor movements)."""
    if not text:
        return ""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)


def normalize_root(allowed_root: str) -> str:
    """Normalize and resolve allowed root directory path."""
    return os.path.realpath(os.path.abspath(os.path.normpath(allowed_root)))


def is_path_contained(allowed_root: str, target_path: str, base_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if target_path is strictly within allowed_root.
    Resolves relative paths against base_dir (or allowed_root if base_dir is None).
    Handles Windows drive letters and case insensitivity robustly.
    Returns (is_contained, normalized_target_path).
    """
    norm_root = normalize_root(allowed_root)
    effective_base = normalize_root(base_dir) if base_dir else norm_root

    # Handle relative path resolution
    if not os.path.isabs(target_path):
        resolved_path = os.path.realpath(os.path.abspath(os.path.normpath(os.path.join(effective_base, target_path))))
    else:
        resolved_path = os.path.realpath(os.path.abspath(os.path.normpath(target_path)))

    # Pathlib hierarchy check
    try:
        if os.name == 'nt':
            norm_root_path = Path(norm_root.lower()).resolve()
            target_path_obj = Path(resolved_path.lower()).resolve()
        else:
            norm_root_path = Path(norm_root).resolve()
            target_path_obj = Path(resolved_path).resolve()

        target_path_obj.relative_to(norm_root_path)
        return True, resolved_path
    except ValueError:
        pass

    # Fallback / double-check with os.path.commonpath
    try:
        if os.name == 'nt':
            common = os.path.commonpath([norm_root.lower(), resolved_path.lower()])
            if common == norm_root.lower():
                return True, resolved_path
        else:
            common = os.path.commonpath([norm_root, resolved_path])
            if common == norm_root:
                return True, resolved_path
    except (ValueError, Exception):
        pass

    return False, resolved_path


def parse_tool_calls_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse tool calls and their arguments from Hermes stdout or stderr logs.
    Handles real-world Hermes formatting:
      - ANSI code stripping
      - Emoji prefixes (e.g. '📞 Tool 1: read_file(...)')
      - Multi-line indented JSON args blocks (e.g. 'Args: {\\n  "path": "..."\\n}')
      - Stderr 'Tool call: <tool> with args: {...}'
      - Standard tool call syntax
    """
    tool_calls = []
    if not text:
        return tool_calls

    clean_text = strip_ansi_codes(text)

    # Pattern 1: Tool N: tool_name(...) followed by Args: { ... }
    # Flexible for emoji prefixes (e.g. 📞) and multi-line indented JSON
    p1 = re.compile(
        r"(?:[📞\s]*)?Tool\s+\d+:\s*([a-zA-Z0-9_\-]+)[^\n\r]*[\r\n]+"
        r"\s*Args:\s*(\{[\s\S]*?\n\s*\})",
        re.MULTILINE
    )
    for m in p1.finditer(clean_text):
        tool_name = m.group(1).strip()
        args_raw = m.group(2).strip()
        parsed_args = _safe_load_json_dict(args_raw)
        tool_calls.append({
            "tool": tool_name,
            "raw_args": args_raw,
            "args": parsed_args
        })

    # Pattern 2: Single-line Args variant: Tool N: tool_name(...) \n Args: { ... }
    p1_single = re.compile(
        r"(?:[📞\s]*)?Tool\s+\d+:\s*([a-zA-Z0-9_\-]+)[^\n\r]*[\r\n]+"
        r"\s*Args:\s*(\{[^\r\n]+\})",
        re.MULTILINE
    )
    for m in p1_single.finditer(clean_text):
        tool_name = m.group(1).strip()
        args_raw = m.group(2).strip()
        parsed_args = _safe_load_json_dict(args_raw)
        tool_calls.append({
            "tool": tool_name,
            "raw_args": args_raw,
            "args": parsed_args
        })

    # Pattern 3: Tool call: <tool_name> with args: { ... } (stderr logs)
    p2 = re.compile(
        r"(?i)Tool\s+call:\s*([a-zA-Z0-9_\-]+)\s+with\s+args:\s*(\{[\s\S]*?\n\s*\}|\{[^\r\n]+\})",
        re.MULTILINE
    )
    for m in p2.finditer(clean_text):
        tool_name = m.group(1).strip()
        args_raw = m.group(2).strip()
        parsed_args = _safe_load_json_dict(args_raw)
        tool_calls.append({
            "tool": tool_name,
            "raw_args": args_raw,
            "args": parsed_args
        })

    # Pattern 4: Explicit function invocation: read_file(path="...") or write_file(path="...")
    p3 = re.compile(
        r"(?i)\b(read_file|write_file|file_read|file_write)\s*\(\s*(?:path\s*=\s*)?['\"]([^'\"]+)['\"]"
    )
    for m in p3.finditer(clean_text):
        tool_name = m.group(1).strip()
        path_val = m.group(2).strip()
        tool_calls.append({
            "tool": tool_name,
            "raw_args": f'{{"path": "{path_val}"}}',
            "args": {"path": path_val}
        })

    # Deduplicate while preserving order
    seen = set()
    unique_calls = []
    for tc in tool_calls:
        key = (tc.get("tool"), tc.get("raw_args"))
        if key not in seen:
            seen.add(key)
            unique_calls.append(tc)

    return unique_calls


def _safe_load_json_dict(raw: str) -> Dict[str, Any]:
    """Safely decode JSON dictionary or fallback to regex key extraction."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    extracted = {}
    path_match = re.search(r'["\']?(?:path|file_path|workdir|dir)["\']?\s*:\s*["\']([^"\']+)["\']', raw)
    if path_match:
        extracted["path"] = path_match.group(1)

    cmd_match = re.search(r'["\']?command["\']?\s*:\s*["\']([^"\']+)["\']', raw)
    if cmd_match:
        extracted["command"] = cmd_match.group(1)

    return extracted


def extract_candidate_paths(tool_call: Dict[str, Any]) -> List[Tuple[str, str, Optional[str]]]:
    """
    Extract candidate file system paths from a parsed tool call.
    Returns list of (path_string, source_field_name, base_dir_context).

    Path Handling Note (Requirement 3.b):
    - Tırnak içi path'ler (quoted paths) öncelikli olarak ayrıştırılır; böylece
      boşluk içeren dosya yolları (örn. 'C:\\Users\\Thea-Aria\\ .gemini\\...')
      parçalanmadan bütün olarak korunur.
    - Terminal komutlarında sadece bariz path göstergeleri (sürücü harfi 'C:\\...'
      veya göreli üst dizin traversal '..\\', '../') yakalanır. Standart Linux
      redirection token'ları (/dev/null) ve komut içi göreli alt dizin yolları
      (tests/unit/pipeline/) yanlış pozitif üretmemesi için elenir.
    - Komut içindeki göreli yollar, tool call içinde belirtilen 'workdir' parametresi
      varsa ona göre değerlendirilir.
    """
    candidates = []
    args = tool_call.get("args", {})
    workdir = args.get("workdir") if isinstance(args.get("workdir"), str) else None

    # 1. Doğrudan path alanları
    for field in ["path", "file_path", "target", "source", "destination", "filepath"]:
        val = args.get(field)
        if isinstance(val, str) and val.strip():
            candidates.append((val.strip(), field, workdir))

    # 2. Çalışma dizini (workdir)
    if workdir and workdir.strip():
        candidates.append((workdir.strip(), "workdir", None))

    # 3. Terminal komutu analizi
    command = args.get("command")
    if isinstance(command, str) and command.strip():
        # (i) Önce tırnak içi dizgileri yakala (boşluk içeren path'leri korur)
        quoted_tokens = re.findall(r'["\']([^"\']+)["\']', command)
        for q in quoted_tokens:
            q_clean = q.strip()
            # Sürücü harfli mutlak yol veya göreli traversal içeriyorsa
            if re.match(r'^[a-zA-Z]:[\\/]', q_clean) or re.match(r'^(?:\.\.[\\/])', q_clean):
                candidates.append((q_clean, "command_quoted_path", workdir))

        # (ii) Tırnaksız mutlak Windows yolları
        unquoted_abs = re.findall(r'(?<!\S)[a-zA-Z]:[\\/][^\s"\'<>|]+', command)
        for u in unquoted_abs:
            candidates.append((u.strip(), "command_unquoted_abs", workdir))

        # (iii) Tırnaksız göreli traversal (../ veya ..\)
        traversals = re.findall(r'(?<!\S)(?:\.\.[\\/])[^\s"\'<>|]*', command)
        for tr in traversals:
            candidates.append((tr.strip(), "command_traversal", workdir))

    return candidates


def evaluate_path_containment(
    allowed_root: str,
    stdout_content: str = "",
    stderr_content: str = ""
) -> Dict[str, Any]:
    """
    Core evaluation function.
    Scans stdout and stderr content, extracts tool calls and paths,
    and determines containment verdict.
    """
    combined_tool_calls = []
    if stdout_content:
        combined_tool_calls.extend(parse_tool_calls_from_text(stdout_content))
    if stderr_content:
        combined_tool_calls.extend(parse_tool_calls_from_text(stderr_content))

    # Deduplicate tool calls while maintaining order
    seen_calls = set()
    unique_calls = []
    for tc in combined_tool_calls:
        key = (tc.get("tool"), tc.get("raw_args"))
        if key not in seen_calls:
            seen_calls.add(key)
            unique_calls.append(tc)

    total_calls = len(unique_calls)

    if total_calls == 0:
        return {
            "verdict": "NO_TOOL_CALLS",
            "allowed_root": normalize_root(allowed_root),
            "total_tool_calls_found": 0,
            "paths_checked": [],
            "violations": []
        }

    paths_checked = []
    violations = []

    for tc in unique_calls:
        tool_name = tc.get("tool", "unknown")
        raw_args = tc.get("raw_args", "")
        candidates = extract_candidate_paths(tc)

        for raw_path, field, base_ctx in candidates:
            contained, norm_path = is_path_contained(allowed_root, raw_path, base_dir=base_ctx)
            
            check_entry = {
                "raw_path": raw_path,
                "normalized_path": norm_path,
                "tool": tool_name,
                "arg_field": field,
                "is_contained": contained
            }
            paths_checked.append(check_entry)

            if not contained:
                violations.append({
                    "path": raw_path,
                    "normalized_path": norm_path,
                    "tool": tool_name,
                    "raw_arg": raw_args
                })

    if violations:
        verdict = "VIOLATION_DETECTED"
    else:
        verdict = "CONTAINED"

    return {
        "verdict": verdict,
        "allowed_root": normalize_root(allowed_root),
        "total_tool_calls_found": total_calls,
        "paths_checked": paths_checked,
        "violations": violations
    }


def main():
    parser = argparse.ArgumentParser(
        description="APE Wrapper-Level Path Containment Detector for Hermes tool-call logs."
    )
    parser.add_argument(
        "--allowed-root",
        required=True,
        help="Path to the allowed root directory (e.g. worktree root)."
    )
    parser.add_argument(
        "--stdout-file",
        help="Path to file containing Hermes stdout."
    )
    parser.add_argument(
        "--stderr-file",
        help="Path to file containing Hermes stderr."
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation (default: 2)."
    )

    args = parser.parse_args()

    stdout_text = ""
    stderr_text = ""

    if args.stdout_file:
        if os.path.exists(args.stdout_file):
            with open(args.stdout_file, "r", encoding="utf-8", errors="ignore") as f:
                stdout_text = f.read()
        else:
            print(f"Error: stdout-file not found: {args.stdout_file}", file=sys.stderr)
            sys.exit(2)

    if args.stderr_file:
        if os.path.exists(args.stderr_file):
            with open(args.stderr_file, "r", encoding="utf-8", errors="ignore") as f:
                stderr_text = f.read()
        else:
            print(f"Error: stderr-file not found: {args.stderr_file}", file=sys.stderr)
            sys.exit(2)

    # If neither file provided, read stdin
    if not args.stdout_file and not args.stderr_file:
        if not sys.stdin.isatty():
            stdout_text = sys.stdin.read()

    result = evaluate_path_containment(
        allowed_root=args.allowed_root,
        stdout_content=stdout_text,
        stderr_content=stderr_text
    )

    print(json.dumps(result, indent=args.indent, ensure_ascii=False))

    if result["verdict"] == "VIOLATION_DETECTED":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
