#!/usr/bin/env python3
"""Login to the Dev4 service and download one team weekly report."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://gw-ai-bot.online"
DEFAULT_PASSWORD_ENV = "WK_REPORT_PASSWORD"
DEFAULT_TIMEOUT_SECONDS = 30.0


class ApiError(RuntimeError):
    """Represent a backend or transport error without exposing credentials."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="登录开发四部系统并下载指定自然周的团队周报 Markdown。"
    )
    parser.add_argument(
        "--api-base",
        default=os.environ.get("WK_REPORT_API_BASE", DEFAULT_API_BASE),
        help=f"API 基址，默认读取 WK_REPORT_API_BASE 或 {DEFAULT_API_BASE}",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("WK_REPORT_USERNAME"),
        help="登录账号，默认读取 WK_REPORT_USERNAME",
    )
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help=f"保存密码的环境变量名，默认 {DEFAULT_PASSWORD_ENV}",
    )
    parser.add_argument(
        "--week-date",
        help="目标自然周内任意一天，格式 YYYY-MM-DD；不传表示服务端当前周",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="输出文件或目录；默认使用服务端附件文件名写入当前目录",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"单次请求超时秒数，默认 {DEFAULT_TIMEOUT_SECONDS:g}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="允许覆盖已存在的输出文件",
    )
    parser.add_argument(
        "--ack-login-side-effects",
        action="store_true",
        help="确认登录会确保本周草稿并可能自动导入上周计划",
    )
    return parser.parse_args()


def api_url(api_base: str, path: str) -> str:
    normalized_base = api_base.strip().rstrip("/")
    if not normalized_base:
        raise ApiError("API 基址不能为空")
    context_base = (
        normalized_base
        if normalized_base.endswith("/api/dev4")
        else f"{normalized_base}/api/dev4"
    )
    return f"{context_base}{path}"


def validate_week_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ApiError("--week-date 必须使用 YYYY-MM-DD 格式") from error


def read_password(environment_name: str) -> str:
    password = os.environ.get(environment_name)
    if password:
        return password
    if sys.stdin.isatty():
        password = getpass.getpass("登录密码: ")
        if password:
            return password
    raise ApiError(
        f"未提供密码；请设置环境变量 {environment_name}，或在交互终端运行脚本"
    )


def decode_json(payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApiError("服务端返回了无法解析的 JSON") from error
    if not isinstance(value, dict):
        raise ApiError("服务端返回的 JSON 结构不正确")
    return value


def error_message(status: int | None, payload: bytes) -> str:
    prefix = f"HTTP {status}" if status is not None else "请求失败"
    try:
        value = decode_json(payload)
    except ApiError:
        text = payload.decode("utf-8", errors="replace").strip()
        return f"{prefix}: {text[:200]}" if text else prefix
    code = value.get("code")
    message = value.get("msg") or value.get("message") or value.get("detail")
    details = " / ".join(str(part) for part in (code, message) if part)
    return f"{prefix}: {details}" if details else prefix


def perform_request(
    request: Request,
    timeout: float,
) -> tuple[bytes, dict[str, str]]:
    try:
        with urlopen(request, timeout=timeout) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.read(), headers
    except HTTPError as error:
        payload = error.read()
        raise ApiError(error_message(error.code, payload)) from error
    except URLError as error:
        raise ApiError(f"无法连接服务端: {error.reason}") from error


def request_json(
    method: str,
    url: str,
    timeout: float,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=UTF-8"
    if token:
        headers["satoken"] = token
    response_body, _ = perform_request(
        Request(url, data=body, headers=headers, method=method), timeout
    )
    response = decode_json(response_body)
    if response.get("success") is not True:
        raise ApiError(error_message(None, response_body))
    return response.get("data")


def login(api_base: str, username: str, password: str, timeout: float) -> dict[str, Any]:
    data = request_json(
        "POST",
        api_url(api_base, "/v1/auth/login"),
        timeout,
        payload={"username": username, "password": password, "rememberMe": False},
    )
    if not isinstance(data, dict) or not data.get("accessToken"):
        raise ApiError("登录成功响应中缺少 accessToken")
    return data


def download_report(
    api_base: str,
    token: str,
    week_date: str | None,
    timeout: float,
) -> tuple[bytes, str | None]:
    query = f"?{urlencode({'week_date': week_date})}" if week_date else ""
    request = Request(
        api_url(api_base, f"/v1/weekly-reports/team/export{query}"),
        headers={"Accept": "text/markdown", "satoken": token},
        method="GET",
    )
    payload, headers = perform_request(request, timeout)
    content_type = headers.get("content-type", "")
    if "json" in content_type.lower():
        raise ApiError(error_message(None, payload))
    return payload, attachment_filename(headers.get("content-disposition"))


def attachment_filename(content_disposition: str | None) -> str | None:
    if not content_disposition:
        return None
    match = re.search(r'filename="?([^";]+)"?', content_disposition, re.IGNORECASE)
    if not match:
        return None
    filename = Path(match.group(1).strip()).name
    return filename or None


def output_path(requested: Path | None, server_filename: str | None) -> Path:
    filename = server_filename or "team-weekly-meeting.md"
    if requested is None:
        return Path.cwd() / filename
    if requested.exists() and requested.is_dir():
        return requested / filename
    if str(requested).endswith(("/", "\\")):
        return requested / filename
    return requested


def logout(api_base: str, token: str, timeout: float) -> None:
    try:
        request_json(
            "POST", api_url(api_base, "/v1/auth/logout"), timeout, token=token
        )
    except ApiError:
        pass


def main() -> int:
    args = parse_args()
    if not args.ack_login_side_effects:
        raise ApiError(
            "在线登录会确保本周周报草稿并可能自动导入上周计划；"
            "确认后请添加 --ack-login-side-effects"
        )
    if not args.username:
        raise ApiError("未提供账号；请使用 --username 或设置 WK_REPORT_USERNAME")
    week_date = validate_week_date(args.week_date)
    password = read_password(args.password_env)
    token: str | None = None
    try:
        login_data = login(args.api_base, args.username, password, args.timeout)
        token = str(login_data["accessToken"])
        if login_data.get("mustChangePassword") is True:
            raise ApiError("当前账号必须先在系统页面完成首次密码修改")
        content, server_filename = download_report(
            args.api_base, token, week_date, args.timeout
        )
        destination = output_path(args.output, server_filename)
        if destination.exists() and not args.force:
            raise ApiError(f"输出文件已存在: {destination}；使用 --force 覆盖")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        print(destination.resolve())
        return 0
    finally:
        password = ""
        if token:
            logout(args.api_base, token, args.timeout)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as error:
        print(f"错误: {error}", file=sys.stderr)
        raise SystemExit(1)
