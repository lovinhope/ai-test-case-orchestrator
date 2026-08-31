#!/usr/bin/env python
import argparse
import configparser
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote, urlparse

import requests
from requests.auth import HTTPBasicAuth

DEFAULT_JIRA_BASE = "https://jira.example.invalid"
DEFAULT_CONFLUENCE_BASE = "https://confluence.example.invalid"
DEFAULT_GITLAB_BASE = "https://git.example.invalid"
DEFAULT_PROJECTS = ["CHATGPT", "PRODUCT", "HR", "TIDS", "RISK"]


def _find_config() -> Optional[Path]:
    env = os.getenv("TASKFLOW_CONFIG_PATH", "").strip()
    if env and Path(env).exists():
        return Path(env)
    cwd = Path.cwd()
    for p in [cwd, *cwd.parents]:
        c = p / "config.ini"
        if c.exists():
            return c
    return None


def _read_config(path: Optional[Path]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path:
        return out
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    if parser.has_section("jira"):
        out["jira_base_url"] = parser.get("jira", "base_url", fallback="")
        out["jira_username"] = parser.get("jira", "jira_username", fallback="")
        out["jira_password"] = parser.get("jira", "jira_password", fallback="")
        out["jira_token"] = parser.get("jira", "jira_token", fallback="")
        out["default_user"] = parser.get("jira", "default_user", fallback="")
    if parser.has_section("confluence"):
        out["confluence_base_url"] = parser.get("confluence", "base_url", fallback="")
        out["confluence_token"] = parser.get("confluence", "token", fallback="")
    if parser.has_section("gitlab"):
        out["gitlab_base_url"] = parser.get("gitlab", "base_url", fallback="")
        out["gitlab_token"] = parser.get("gitlab", "token", fallback="")
        out["gitlab_project"] = parser.get("gitlab", "project", fallback="")
    return out


def _cfg() -> Dict[str, str]:
    return _read_config(_find_config())


def _env_or_cfg(env_key: str, cfg_key: str) -> str:
    return os.getenv(env_key, "").strip() or _cfg().get(cfg_key, "").strip()


def _jira_auth() -> Tuple[str, Dict[str, str], Optional[HTTPBasicAuth]]:
    base = _env_or_cfg("JIRA_BASE_URL", "jira_base_url") or DEFAULT_JIRA_BASE
    token = _env_or_cfg("JIRA_TOKEN", "jira_token")
    user = _env_or_cfg("JIRA_USERNAME", "jira_username")
    pwd = _env_or_cfg("JIRA_PASSWORD", "jira_password")

    headers: Dict[str, str] = {"Accept": "application/json"}
    auth: Optional[HTTPBasicAuth] = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif user and pwd:
        auth = HTTPBasicAuth(user, pwd)
    else:
        raise RuntimeError("Missing Jira credentials. Set JIRA_TOKEN or JIRA_USERNAME/JIRA_PASSWORD.")
    return base.rstrip("/"), headers, auth


def _confluence_auth() -> Tuple[str, Dict[str, str]]:
    base = _env_or_cfg("CONFLUENCE_BASE_URL", "confluence_base_url") or DEFAULT_CONFLUENCE_BASE
    token = _env_or_cfg("CONFLUENCE_TOKEN", "confluence_token")
    if not token:
        raise RuntimeError("Missing Confluence token. Set CONFLUENCE_TOKEN.")
    return base.rstrip("/"), {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _resolve_user(user: str) -> str:
    if user:
        return user
    value = os.getenv("TASKFLOW_DEFAULT_USER", "").strip() or _cfg().get("default_user", "").strip() or _env_or_cfg("JIRA_USERNAME", "jira_username")
    if not value:
        raise RuntimeError("Cannot resolve user. Set --user or TASKFLOW_DEFAULT_USER/JIRA_USERNAME.")
    return value


def _parse_projects(projects: str) -> List[str]:
    raw = projects.strip()
    if not raw or raw == ",":
        return DEFAULT_PROJECTS
    return [x.strip() for x in raw.split(",") if x.strip()]


def _normalize_date(raw: str) -> str:
    v = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2}|一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)/(\d{2,4})", v)
    if m:
        d = int(m.group(1))
        mo_raw = m.group(2)
        y = int(m.group(3))
        if y < 100:
            y += 2000
        map_cn = {"一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6, "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12}
        mo = map_cn.get(mo_raw) if mo_raw in map_cn else int(mo_raw)
        return f"{y:04d}-{mo:02d}-{d:02d}"
    raise RuntimeError(f"Unsupported date format: {raw}")


def _jira_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    base, headers, auth = _jira_auth()
    req_headers = dict(headers)
    if "json" in kwargs or "data" in kwargs:
        req_headers.setdefault("Content-Type", "application/json")
    return requests.request(method, f"{base}{path}", headers=req_headers, auth=auth, timeout=60, **kwargs)


def _gitlab_auth() -> Tuple[str, Dict[str, str]]:
    base = _env_or_cfg("GITLAB_BASE_URL", "gitlab_base_url") or DEFAULT_GITLAB_BASE
    token = _env_or_cfg("GITLAB_TOKEN", "gitlab_token")
    if not token:
        raise RuntimeError("Missing GitLab token. Set GITLAB_TOKEN or [gitlab] token in config.ini.")
    base = base.rstrip("/")
    api_base = base if base.endswith("/api/v4") else f"{base}/api/v4"
    return api_base, {"PRIVATE-TOKEN": token, "Accept": "application/json"}


def _gitlab_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    base, headers = _gitlab_auth()
    req_headers = dict(headers)
    if "json" in kwargs or "data" in kwargs:
        req_headers.setdefault("Content-Type", "application/json")
    return requests.request(method, f"{base}{path}", headers=req_headers, timeout=60, **kwargs)


def _text_values(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            out.extend(_text_values(item))
        return out
    if isinstance(value, dict):
        out = []
        for key in ("body", "title", "url", "displayUrl", "summary", "description"):
            out.extend(_text_values(value.get(key)))
        return out
    return []


def _gitlab_ref_from_url(raw_url: str, source: str) -> Optional[Dict[str, Any]]:
    candidate = raw_url.strip().rstrip(".,;)>]")
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = unquote(parsed.path).strip("/")
    marker = re.search(r"/(?:-/)?(merge_requests|commit|commits)/([^/]+)", "/" + path)
    if not marker:
        return None
    kind, value = marker.group(1), marker.group(2)
    project_path = path[: marker.start()].strip("/")
    if not project_path or not ("gitlab" in parsed.netloc.lower() or "/-/" in parsed.path):
        return None
    ref: Dict[str, Any] = {
        "url": candidate,
        "source": source,
        "host": parsed.netloc,
        "project": project_path,
    }
    if kind == "merge_requests" and value.isdigit():
        ref.update({"type": "merge_request", "iid": int(value)})
    elif kind in {"commit", "commits"} and re.fullmatch(r"[0-9a-fA-F]{7,64}", value):
        ref.update({"type": "commit", "sha": value})
    else:
        return None
    return ref


def _extract_gitlab_refs(values: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    refs: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    url_pattern = re.compile(r"https?://[^\s<>\"']+")
    for source, text in values:
        for raw_url in url_pattern.findall(text or ""):
            ref = _gitlab_ref_from_url(raw_url, source)
            if ref:
                key = (ref["type"], ref["project"], str(ref.get("iid") or ref.get("sha")))
                refs.setdefault(key, ref)
    return list(refs.values())


def _jira_code_sources(issue: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Tuple[str, str]]]:
    issue_resp = _jira_request(
        "GET",
        f"/rest/api/2/issue/{issue}",
        params={"fields": "summary,description,comment,issuelinks,status", "expand": "renderedFields"},
    )
    issue_resp.raise_for_status()
    issue_obj = issue_resp.json()
    fields = issue_obj.get("fields", {})
    values: List[Tuple[str, str]] = [("jira.description", str(fields.get("description") or ""))]
    for comment in (fields.get("comment") or {}).get("comments", []):
        values.append(("jira.comment", str(comment.get("body") or "")))

    remote_links: List[Dict[str, Any]] = []
    links_resp = _jira_request("GET", f"/rest/api/2/issue/{issue}/remotelink")
    if links_resp.status_code == 200:
        links_obj = links_resp.json()
        remote_links = links_obj if isinstance(links_obj, list) else []
        for link in remote_links:
            obj = link.get("object") or {}
            values.append(("jira.remote_link", " ".join(_text_values(obj))))

    for link in fields.get("issuelinks") or []:
        linked = link.get("outwardIssue") or link.get("inwardIssue") or {}
        if linked.get("key"):
            values.append(("jira.linked_issue", str(linked["key"])))
    return issue_obj, remote_links, values


def _gitlab_project(project_path: str) -> Dict[str, Any]:
    response = _gitlab_request("GET", f"/projects/{quote(project_path, safe='')}")
    if response.status_code == 200:
        return response.json()
    if response.status_code != 404:
        response.raise_for_status()

    # Some self-hosted GitLab reverse proxies reject the encoded namespace
    # route even though the project-search API works. Resolve the exact path
    # through search as a compatibility fallback.
    leaf = project_path.rsplit("/", 1)[-1]
    search = _gitlab_request("GET", "/projects", params={"search": leaf, "per_page": 100})
    search.raise_for_status()
    expected = project_path.casefold()
    for item in search.json() or []:
        path_with_namespace = str(item.get("path_with_namespace") or "")
        if path_with_namespace.casefold() == expected:
            return item
    raise RuntimeError(f"GitLab project not found or not visible: {project_path}")


def _gitlab_change_summary(changes: Any) -> List[Dict[str, Any]]:
    result = []
    for change in changes or []:
        result.append({
            "old_path": change.get("old_path"),
            "new_path": change.get("new_path"),
            "new_file": bool(change.get("new_file")),
            "renamed_file": bool(change.get("renamed_file")),
            "deleted_file": bool(change.get("deleted_file")),
            "diff": change.get("diff", ""),
        })
    return result


def _resolve_gitlab_ref(ref: Dict[str, Any]) -> Dict[str, Any]:
    project = _gitlab_project(ref["project"])
    project_id = project["id"]
    result = {**ref, "project_id": project_id, "project_web_url": project.get("web_url"), "verified": False}
    if ref["type"] == "merge_request":
        mr_resp = _gitlab_request("GET", f"/projects/{project_id}/merge_requests/{ref['iid']}")
        mr_resp.raise_for_status()
        mr = mr_resp.json()
        changes_resp = _gitlab_request("GET", f"/projects/{project_id}/merge_requests/{ref['iid']}/changes")
        if changes_resp.status_code == 404:
            changes_resp = _gitlab_request("GET", f"/projects/{project_id}/merge_requests/{ref['iid']}/diffs")
        changes_resp.raise_for_status()
        changes_obj = changes_resp.json()
        result.update({
            "verified": True,
            "title": mr.get("title"),
            "state": mr.get("state"),
            "author": (mr.get("author") or {}).get("username"),
            "source_branch": mr.get("source_branch"),
            "target_branch": mr.get("target_branch"),
            "merged_at": mr.get("merged_at"),
            "commit_sha": mr.get("merge_commit_sha") or mr.get("sha"),
            "changes": _gitlab_change_summary(changes_obj.get("changes") or changes_obj.get("diffs")),
        })
    else:
        commit_resp = _gitlab_request("GET", f"/projects/{project_id}/repository/commits/{quote(ref['sha'], safe='')}")
        commit_resp.raise_for_status()
        commit = commit_resp.json()
        diff_resp = _gitlab_request("GET", f"/projects/{project_id}/repository/commits/{quote(ref['sha'], safe='')}/diff")
        diff_resp.raise_for_status()
        result.update({
            "verified": True,
            "title": commit.get("title"),
            "author": commit.get("author_name"),
            "committed_date": commit.get("committed_date"),
            "message": commit.get("message"),
            "changes": _gitlab_change_summary(diff_resp.json()),
        })
    result["changed_files"] = [x.get("new_path") or x.get("old_path") for x in result.get("changes", [])]
    return result


def cmd_jira_code_read(args: argparse.Namespace) -> int:
    issue_obj, remote_links, values = _jira_code_sources(args.issue)
    refs = _extract_gitlab_refs(values)
    resolved: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for ref in refs:
        try:
            resolved.append(_resolve_gitlab_ref(ref))
        except Exception as exc:
            errors.append({"url": ref.get("url", ""), "error": str(exc)})

    payload = {
        "issue": issue_obj.get("key", args.issue),
        "summary": (issue_obj.get("fields") or {}).get("summary", ""),
        "jira_remote_link_count": len(remote_links),
        "gitlab_refs": refs,
        "gitlab_commits": resolved,
        "errors": errors,
        "note": "gitlab_commits contains only API-verified GitLab metadata and diffs; classification still requires association review.",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"issue: {payload['issue']}")
    print(f"summary: {payload['summary']}")
    print(f"jira_remote_link_count: {len(remote_links)}")
    print(f"gitlab_refs: {len(refs)}")
    for item in resolved:
        print(f"- {item['type']} {item.get('project')} {item.get('iid') or item.get('sha')} verified=true")
        print(f"  title: {item.get('title', '')}")
        print(f"  changed_files: {', '.join(item.get('changed_files') or [])}")
    for item in errors:
        print(f"- unresolved: {item['url']} ({item['error']})")
    if not refs:
        print("No explicit GitLab MR/commit URL was found in Jira description, comments, remote links, or linked-issue references.")
    return 0

def _search_issues(user: str, days: int, projects: List[str], unresolved_only: bool, high_only: bool, types: List[str], max_results: int) -> Dict[str, Any]:
    clauses = [f'project in ({", ".join(projects)})', f'assignee = "{user}"', f"updated >= -{days}d"]
    if unresolved_only:
        clauses.append("resolution = Unresolved")
    if high_only:
        clauses.append('priority in ("Highest", "High")')
    if types:
        escaped = [f'"{t}"' for t in types if t.strip()]
        clauses.append(f"issuetype in ({', '.join(escaped)})")
    jql = " AND ".join(clauses) + " ORDER BY priority DESC, updated DESC"

    params = {
        "jql": jql,
        "fields": "summary,status,assignee,updated,priority,issuetype",
        "maxResults": max_results,
    }
    resp = _jira_request("GET", "/rest/api/2/search", params=params)
    if resp.status_code >= 400 and types:
        # Some Jira projects reject unknown issue type names in JQL.
        # Retry without the issue type clause for compatibility.
        clauses = [f'project in ({", ".join(projects)})', f'assignee = "{user}"', f"updated >= -{days}d"]
        if unresolved_only:
            clauses.append("resolution = Unresolved")
        if high_only:
            clauses.append('priority in ("Highest", "High")')
        params["jql"] = " AND ".join(clauses) + " ORDER BY priority DESC, updated DESC"
        resp = _jira_request("GET", "/rest/api/2/search", params=params)
    resp.raise_for_status()
    return resp.json()


def cmd_jira_query(args: argparse.Namespace) -> int:
    user = _resolve_user(args.user)
    data = _search_issues(
        user=user,
        days=args.days,
        projects=_parse_projects(args.projects),
        unresolved_only=not args.include_resolved,
        high_only=args.high_priority,
        types=[x.strip() for x in args.types.split(",") if x.strip()],
        max_results=args.max_results,
    )
    issues = data.get("issues", [])
    print(f"query_user: {user}")
    print(f"result_count: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        f = issue.get("fields", {})
        print(
            f"{i}. {issue.get('key')} | {((f.get('priority') or {}).get('name', ''))} | "
            f"{((f.get('issuetype') or {}).get('name', ''))} | {((f.get('status') or {}).get('name', ''))} | {f.get('summary', '')}"
        )
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_jira_high_priority(args: argparse.Namespace) -> int:
    user = _resolve_user(args.user)
    data = _search_issues(
        user=user,
        days=args.days,
        projects=_parse_projects(args.projects),
        unresolved_only=True,
        high_only=True,
        types=["任务", "需求", "缺陷", "故障", "Task", "Story", "Bug"],
        max_results=args.max_results,
    )
    issues = data.get("issues", [])
    print(f"query_user: {user}")
    print(f"range_days: {args.days}")
    print(f"result_count: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        f = issue.get("fields", {})
        print(
            f"{i}. {issue.get('key')} | {((f.get('priority') or {}).get('name', ''))} | "
            f"{((f.get('issuetype') or {}).get('name', ''))} | {((f.get('status') or {}).get('name', ''))} | {f.get('summary', '')}"
        )
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _match_allowed(meta: Dict[str, Any], value: str) -> Optional[Dict[str, Any]]:
    target = value.strip().lower()
    for item in meta.get("allowedValues", []) or []:
        vals = {
            str(item.get("id", "")).strip().lower(),
            str(item.get("name", "")).strip().lower(),
            str(item.get("value", "")).strip().lower(),
        }
        if target in vals:
            if item.get("id"):
                return {"id": str(item.get("id"))}
            if item.get("name"):
                return {"name": item.get("name")}
            if item.get("value"):
                return {"value": item.get("value")}
    return None


def _get_create_fields(project: str, issuetype: str) -> Tuple[str, Dict[str, Any]]:
    resp = _jira_request("GET", "/rest/api/2/issue/createmeta", params={"projectKeys": project, "expand": "projects.issuetypes.fields"})
    resp.raise_for_status()
    projects = (resp.json() or {}).get("projects", [])
    if not projects:
        raise RuntimeError(f"Project not found: {project}")
    issue_types = projects[0].get("issuetypes", [])
    picked = None
    for it in issue_types:
        if str(it.get("id", "")) == issuetype or str(it.get("name", "")).lower() == issuetype.lower():
            picked = it
            break
    if not picked:
        choices = ", ".join([f"{x.get('name')}({x.get('id')})" for x in issue_types])
        raise RuntimeError(f"Issue type not found: {issuetype}. Available: {choices}")
    return str(picked.get("id")), picked.get("fields", {})


def cmd_jira_create(args: argparse.Namespace) -> int:
    base, _, _ = _jira_auth()
    issuetype_id, fields_meta = _get_create_fields(args.project, args.issuetype)

    fields: Dict[str, Any] = {
        "project": {"key": args.project},
        "issuetype": {"id": issuetype_id},
        "summary": args.summary,
    }
    if args.description:
        fields["description"] = args.description
    if args.assignee:
        fields["assignee"] = {"name": args.assignee}

    if "components" in fields_meta and args.module:
        opt = _match_allowed(fields_meta["components"], args.module)
        if opt and opt.get("id"):
            fields["components"] = [{"id": opt["id"]}]
        elif opt and opt.get("name"):
            fields["components"] = [{"name": opt["name"]}]
        else:
            fields["components"] = [{"name": args.module}]

    if "priority" in fields_meta and args.priority:
        fields["priority"] = _match_allowed(fields_meta["priority"], args.priority) or {"name": args.priority}

    if "customfield_12603" in fields_meta and args.task_type:
        task_opt = _match_allowed(fields_meta["customfield_12603"], args.task_type)
        if not task_opt:
            raise RuntimeError(f"Invalid task type: {args.task_type}")
        fields["customfield_12603"] = task_opt

    if "customfield_11700" in fields_meta:
        branch = args.branch_type or "没有分支"
        branch_opt = _match_allowed(fields_meta["customfield_11700"], branch)
        if branch_opt:
            fields["customfield_11700"] = branch_opt

    if "customfield_10500" in fields_meta and args.expected_dev_date:
        fields["customfield_10500"] = _normalize_date(args.expected_dev_date)

    if args.extra_json:
        payload = json.loads(Path(args.extra_json).read_text(encoding="utf-8")) if Path(args.extra_json).exists() else json.loads(args.extra_json)
        if not isinstance(payload, dict):
            raise RuntimeError("--extra-json must be an object")
        fields.update(payload)

    missing = []
    for fid, meta in fields_meta.items():
        if meta.get("required") and fid not in fields and fid not in {"reporter"}:
            missing.append(f"{fid}({meta.get('name','')})")
    if missing:
        raise RuntimeError("Missing required fields: " + ", ".join(missing))

    if args.dry_run:
        print(json.dumps({"fields": fields}, ensure_ascii=False, indent=2))
        return 0

    resp = _jira_request("POST", "/rest/api/2/issue", json={"fields": fields})
    if resp.status_code >= 400:
        raise RuntimeError(f"Create failed: {resp.text}")
    obj = resp.json()
    print(f"created_issue: {obj.get('key')}")
    print(f"issue_url: {base}/browse/{obj.get('key')}")
    return 0

def _issue_fields(issue: str, fields: str) -> Dict[str, Any]:
    resp = _jira_request("GET", f"/rest/api/2/issue/{issue}", params={"fields": fields})
    resp.raise_for_status()
    return (resp.json() or {}).get("fields", {})


def cmd_jira_resolve(args: argparse.Namespace) -> int:
    resp = _jira_request("GET", f"/rest/api/2/issue/{args.issue}/transitions", params={"expand": "transitions.fields"})
    resp.raise_for_status()
    transitions = (resp.json() or {}).get("transitions", [])

    target = None
    for t in transitions:
        name = str(t.get("name", "")).lower()
        to_name = str((t.get("to") or {}).get("name", "")).lower()
        if args.to.lower() in name or args.to.lower() in to_name:
            target = t
            break
    if not target:
        raise RuntimeError("Transition not found for resolve")

    required = target.get("fields", {}) or {}
    payload_fields: Dict[str, Any] = {}
    payload_update: Dict[str, Any] = {}

    for fid, meta in required.items():
        if not meta.get("required"):
            continue
        if fid == "resolution":
            opt = _match_allowed(meta, args.resolution)
            if not opt:
                raise RuntimeError(f"Invalid resolution: {args.resolution}")
            payload_fields[fid] = opt
        elif fid == "customfield_11700":
            opt = _match_allowed(meta, args.branch_type)
            if not opt:
                raise RuntimeError(f"Invalid branch type: {args.branch_type}")
            payload_fields[fid] = opt
        elif fid == "customfield_10500":
            dt = args.expected_dev_date
            if not dt:
                dt = _issue_fields(args.issue, "customfield_10500").get("customfield_10500")
            if not dt:
                raise RuntimeError("Missing expected dev date. Set --expected-dev-date")
            payload_fields[fid] = _normalize_date(dt)
        elif fid == "worklog":
            payload_update["worklog"] = [{"add": {"timeSpent": args.worklog, "comment": args.comment}}]
        else:
            raise RuntimeError(f"Unsupported required transition field: {fid}({meta.get('name','')})")

    body: Dict[str, Any] = {"transition": {"id": str(target.get("id"))}}
    if payload_fields:
        body["fields"] = payload_fields
    if payload_update:
        body["update"] = payload_update

    tr = _jira_request("POST", f"/rest/api/2/issue/{args.issue}/transitions", json=body)
    if tr.status_code >= 400:
        raise RuntimeError(f"Transition failed: {tr.text}")

    vf = _issue_fields(args.issue, "status,resolution")
    print(f"issue: {args.issue}")
    print(f"status: {(vf.get('status') or {}).get('name','')}")
    print(f"resolution: {((vf.get('resolution') or {}).get('name',''))}")
    return 0


def _extract_desc_image_names(desc: str) -> List[str]:
    return [m.group(1).strip() for m in re.finditer(r"!([^!|]+?)(?:\|[^!]+)?!", desc or "") if m.group(1).strip()]


def _looks_like_image(resp: requests.Response) -> bool:
    ct = (resp.headers.get("Content-Type") or "").lower()
    if ct.startswith("image/"):
        return True
    head = resp.content[:12]
    return head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff")


def _browser_candidates(browser: str) -> List[Tuple[str, str]]:
    local = os.getenv("LOCALAPPDATA", "")
    candidates = [
        (r"C:\Program Files\Google\Chrome\Application\chrome.exe", os.path.join(local, "Google", "Chrome", "User Data")),
        (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", os.path.join(local, "Microsoft", "Edge", "User Data")),
        (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", os.path.join(local, "Microsoft", "Edge", "User Data")),
    ]
    if browser == "chrome":
        return [candidates[0]]
    if browser == "edge":
        return candidates[1:]
    return candidates


def _capture_with_browser(url: str, output_file: Path, browser: str, profile: str) -> bool:
    for exe, user_data in _browser_candidates(browser):
        if not Path(exe).exists() or not Path(user_data).exists():
            continue
        dump = subprocess.run(
            [exe, "--headless", "--disable-gpu", f"--profile-directory={profile}", f"--user-data-dir={user_data}", "--dump-dom", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=120,
        ).stdout or ""
        if "cas/login" in dump or "乐瑞内部管理系统-登录" in dump:
            continue
        subprocess.run(
            [exe, "--headless", "--disable-gpu", "--window-size=2200,1400", f"--profile-directory={profile}", f"--user-data-dir={user_data}", f"--screenshot={str(output_file)}", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=120,
        )
        if output_file.exists() and output_file.stat().st_size > 0:
            return True
    return False


def cmd_jira_read(args: argparse.Namespace) -> int:
    resp = _jira_request(
        "GET",
        f"/rest/api/2/issue/{args.issue}",
        params={"fields": "summary,description,attachment,status,priority,issuetype,assignee", "expand": "renderedFields"},
    )
    resp.raise_for_status()
    obj = resp.json()
    f = obj.get("fields", {})

    print(f"issue: {obj.get('key')}")
    print(f"summary: {f.get('summary','')}")
    print(f"status: {((f.get('status') or {}).get('name',''))}")
    print("description_raw:")
    print(f.get("description") or "")

    if not args.download_images:
        return 0

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    desc_names = _extract_desc_image_names(f.get("description") or "")
    attachments = f.get("attachment") or []
    image_attachments = [x for x in attachments if str(x.get("mimeType", "")).lower().startswith("image/")]

    by_name = {str(x.get("filename")): x for x in image_attachments}
    ordered = [by_name[name] for name in desc_names if name in by_name]
    for x in image_attachments:
        if x not in ordered:
            ordered.append(x)

    print(f"image_attachments: {len(ordered)}")

    for att in ordered:
        name = str(att.get("filename") or f"att-{att.get('id')}")
        safe = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fa5]", "_", name)
        out = output_dir / safe
        content_url = att.get("content")

        ok = False
        mode = ""
        try:
            dr = requests.get(content_url, headers=_jira_auth()[1], auth=_jira_auth()[2], timeout=90, allow_redirects=True)
            if dr.status_code == 200 and _looks_like_image(dr):
                out.write_bytes(dr.content)
                ok = True
                mode = "direct"
        except Exception:
            pass

        if not ok:
            shot = output_dir / f"capture-{safe}.png"
            if _capture_with_browser(content_url, shot, args.browser, args.profile):
                ok = True
                mode = "browser_screenshot"
                out = shot

        print(f"- {name} => {'ok' if ok else 'failed'} ({mode or 'none'}) -> {out}")

    return 0


def _extract_page_id(raw: str) -> str:
    text = raw.strip()
    m = re.search(r"pageId=(\d+)", text)
    if m:
        return m.group(1)
    if text.isdigit():
        return text
    raise RuntimeError("Cannot parse pageId from input.")


def cmd_confluence_search(args: argparse.Namespace) -> int:
    base, headers = _confluence_auth()
    term = args.term.strip().replace('"', '\\"')
    clauses = ["type=page", f'text ~ "{term}"']
    if args.space:
        clauses.append(f'space = "{args.space.strip().replace(chr(34), chr(92) + chr(34))}"')
    if args.parent:
        clauses.append(f"ancestor = { _extract_page_id(args.parent) }")
    cql = " AND ".join(clauses) + " ORDER BY lastModified DESC"
    resp = requests.get(
        f"{base}/rest/api/content/search",
        params={"cql": cql, "limit": args.limit, "expand": "space,version,ancestors"},
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json() or {}
    results = data.get("results", [])
    print(f"query: {args.term}")
    print(f"cql: {cql}")
    print(f"result_count: {len(results)}")
    for i, page in enumerate(results, 1):
        version = page.get("version") or {}
        space = page.get("space") or {}
        print(f"{i}. {page.get('id')} | {page.get('title', '')} | {space.get('key', '')} | {version.get('when', '')}")
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_confluence_read(args: argparse.Namespace) -> int:
    base, headers = _confluence_auth()
    page_id = _extract_page_id(args.page)
    resp = requests.get(f"{base}/rest/api/content/{page_id}?expand=space,version,ancestors,body.view", headers=headers, timeout=60)
    resp.raise_for_status()
    d = resp.json()
    html = ((d.get("body") or {}).get("view") or {}).get("value", "")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > args.max_chars:
        text = text[: args.max_chars] + " ..."
    print(f"title: {d.get('title','')}")
    print(f"space: {((d.get('space') or {}).get('key',''))}")
    print(f"updated_by: {(((d.get('version') or {}).get('by') or {}).get('displayName',''))}")
    print(f"content_summary:\n{text}")
    return 0

def _resolve_parent(base: str, headers: Dict[str, str], parent: str) -> Tuple[str, str, str]:
    raw = parent.strip()
    if re.search(r"pageId=\d+", raw) or raw.isdigit():
        page_id = _extract_page_id(raw)
        r = requests.get(f"{base}/rest/api/content/{page_id}?expand=space", headers=headers, timeout=60)
        r.raise_for_status()
        d = r.json()
        return page_id, ((d.get("space") or {}).get("key") or ""), d.get("title", "")

    r = requests.get(f"{base}/rest/api/content", params={"title": raw, "type": "page", "expand": "space,version"}, headers=headers, timeout=60)
    r.raise_for_status()
    rs = r.json().get("results", [])
    if not rs:
        raise RuntimeError(f"Parent page not found by title: {raw}")
    rs = sorted(rs, key=lambda x: ((x.get("version") or {}).get("number") or 0), reverse=True)
    d = rs[0]
    return str(d.get("id")), ((d.get("space") or {}).get("key") or ""), d.get("title", "")


def cmd_confluence_create_child(args: argparse.Namespace) -> int:
    base, headers = _confluence_auth()
    parent_id, space_key, parent_title = _resolve_parent(base, headers, args.parent)

    if not args.allow_duplicate:
        cql = f'type=page and ancestor={parent_id} and title="{args.title}"'
        q = requests.get(f"{base}/rest/api/content/search", params={"cql": cql, "limit": 5}, headers=headers, timeout=30)
        if q.status_code == 200 and (q.json().get("results") or []):
            e = q.json()["results"][0]
            raise RuntimeError(f"Duplicate title under parent. Existing page id: {e.get('id')}")

    mention = ""
    if args.mention:
        u = requests.get(f"{base}/rest/api/user", params={"username": args.mention}, headers=headers, timeout=30)
        if u.status_code == 200:
            uk = (u.json() or {}).get("userKey") or (u.json() or {}).get("key")
            if uk:
                mention = f' <ac:link><ri:user ri:userkey="{uk}" /></ac:link>'
        if not mention:
            mention = f" @{args.mention}"

    payload = {
        "type": "page",
        "title": args.title,
        "ancestors": [{"id": parent_id}],
        "space": {"key": space_key},
        "body": {"storage": {"value": f"<p>{args.body}{mention}</p>", "representation": "storage"}},
    }

    c = requests.post(f"{base}/rest/api/content", headers={**headers, "Content-Type": "application/json"}, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=60)
    if c.status_code >= 400:
        raise RuntimeError(f"Create confluence page failed: {c.text}")
    d = c.json()
    links = d.get("_links") or {}
    url = (links.get("base", base).rstrip("/") + links.get("webui", "")) if links.get("webui") else f"{base}/pages/viewpage.action?pageId={d.get('id')}"
    print(f"parent: {parent_title} ({parent_id})")
    print(f"created_page_id: {d.get('id')}")
    print(f"created_url: {url}")
    return 0


def cmd_legacy_jira(args: argparse.Namespace) -> int:
    user = _resolve_user(args.user)
    unresolved = _detect_mine_unresolved(args.query)
    data = _search_issues(user, args.days, _parse_projects(args.projects), unresolved, False, [], 200)
    issues = data.get("issues", [])
    print(f"query_user: {user}")
    print(f"result_count: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        f = issue.get("fields", {})
        print(f"{i}. {issue.get('key')} | {f.get('summary','')} | {((f.get('status') or {}).get('name',''))}")
    return 0


def cmd_legacy_confluence(args: argparse.Namespace) -> int:
    return cmd_confluence_read(argparse.Namespace(page=args.page, max_chars=2500))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="lowrisk-it-jiraConfluence: Jira + Confluence helper for Codex/OpenClaw")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("jira-query", help="Query Jira issues")
    q.add_argument("--user", default="")
    q.add_argument("--days", type=int, default=30)
    q.add_argument("--projects", default=",".join(DEFAULT_PROJECTS))
    q.add_argument("--high-priority", action="store_true")
    q.add_argument("--include-resolved", action="store_true")
    q.add_argument("--types", default="")
    q.add_argument("--max-results", type=int, default=200)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_jira_query)

    h = sub.add_parser("jira-high-priority", help="Query unresolved high-priority tasks/requirements/bugs")
    h.add_argument("--user", default="")
    h.add_argument("--days", type=int, default=30)
    h.add_argument("--projects", default=",".join(DEFAULT_PROJECTS))
    h.add_argument("--max-results", type=int, default=200)
    h.add_argument("--json", action="store_true")
    h.set_defaults(func=cmd_jira_high_priority)

    c = sub.add_parser("jira-create", help="Create Jira issue with required fields")
    c.add_argument("--project", required=True)
    c.add_argument("--summary", required=True)
    c.add_argument("--issuetype", default="任务")
    c.add_argument("--description", default="")
    c.add_argument("--module", default="")
    c.add_argument("--task-type", default="")
    c.add_argument("--expected-dev-date", default="")
    c.add_argument("--branch-type", default="没有分支")
    c.add_argument("--priority", default="Highest")
    c.add_argument("--assignee", default="")
    c.add_argument("--extra-json", default="")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(func=cmd_jira_create)

    rs = sub.add_parser("jira-resolve", help="Move Jira issue to resolved")
    rs.add_argument("--issue", required=True)
    rs.add_argument("--to", default="解决问题")
    rs.add_argument("--resolution", default="完成")
    rs.add_argument("--worklog", default="1m")
    rs.add_argument("--comment", default="Resolved by jira_confluence_use")
    rs.add_argument("--expected-dev-date", default="")
    rs.add_argument("--branch-type", default="没有分支")
    rs.set_defaults(func=cmd_jira_resolve)

    rd = sub.add_parser("jira-read", help="Read Jira description and fetch description images")
    rd.add_argument("--issue", required=True)
    rd.add_argument("--download-images", action="store_true")
    rd.add_argument("--output-dir", default="./jira_images")
    rd.add_argument("--browser", choices=["auto", "chrome", "edge"], default="auto")
    rd.add_argument("--profile", default="Default")
    rd.set_defaults(func=cmd_jira_read)

    jc = sub.add_parser("jira-code-read", help="Read Jira-linked GitLab merge requests and commits")
    jc.add_argument("--issue", required=True)
    jc.add_argument("--json", action="store_true")
    jc.set_defaults(func=cmd_jira_code_read)

    cf = sub.add_parser("confluence-read", help="Read Confluence page by URL/pageId")
    cf.add_argument("--page", required=True)
    cf.add_argument("--max-chars", type=int, default=2500)
    cf.set_defaults(func=cmd_confluence_read)

    cs = sub.add_parser("confluence-search", help="Search Confluence pages by text")
    cs.add_argument("--term", required=True)
    cs.add_argument("--space", default="")
    cs.add_argument("--parent", default="")
    cs.add_argument("--limit", type=int, default=25)
    cs.add_argument("--json", action="store_true")
    cs.set_defaults(func=cmd_confluence_search)

    cc = sub.add_parser("confluence-create-child", help="Create child page under a parent page")
    cc.add_argument("--parent", required=True)
    cc.add_argument("--title", required=True)
    cc.add_argument("--body", required=True)
    cc.add_argument("--mention", default="")
    cc.add_argument("--allow-duplicate", action="store_true")
    cc.set_defaults(func=cmd_confluence_create_child)

    lj = sub.add_parser("jira", help="[legacy] natural language Jira query")
    lj.add_argument("--query", required=True)
    lj.add_argument("--days", type=int, default=90)
    lj.add_argument("--projects", default=",")
    lj.add_argument("--user", default="")
    lj.set_defaults(func=cmd_legacy_jira)

    lc = sub.add_parser("confluence", help="[legacy] read confluence page")
    lc.add_argument("--page", required=True)
    lc.set_defaults(func=cmd_legacy_confluence)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("[lowrisk-it-jiraConfluence] interrupted")
        return 130
    except Exception as exc:
        print(f"[lowrisk-it-jiraConfluence] failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
