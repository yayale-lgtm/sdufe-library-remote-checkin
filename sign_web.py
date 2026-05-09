import os
from urllib.parse import quote

import requests
from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

TIME_API_URL = "https://libst.sdufe.edu.cn/api.php/v3qrtime"
SESSION_FILE = os.getenv("SESSION_FILE", "phpsessid.txt")
DEFAULT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.49(0x1800312c) NetType/WIFI Language/zh_CN"
)
CURRENT_PHPSESSID = None


def _load_phpsessid() -> str:
    global CURRENT_PHPSESSID
    if CURRENT_PHPSESSID:
        return CURRENT_PHPSESSID

    env_value = os.getenv("PHPSESSID", "").strip()
    if env_value:
        CURRENT_PHPSESSID = env_value
        return env_value

    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            file_value = f.read().strip()
        if file_value:
            CURRENT_PHPSESSID = file_value
            return file_value
    return ""


def _save_phpsessid(value: str) -> None:
    global CURRENT_PHPSESSID
    clean = value.strip()
    if not clean:
        raise RuntimeError("empty PHPSESSID")
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        f.write(clean)
    CURRENT_PHPSESSID = clean
    os.environ["PHPSESSID"] = clean


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def build_session() -> requests.Session:
    phpsessid = _load_phpsessid()
    if not phpsessid:
        raise RuntimeError("missing PHPSESSID")

    session = requests.Session()
    session.trust_env = False
    session.headers.update(
        {
            "User-Agent": os.getenv("USER_AGENT", DEFAULT_UA),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
        }
    )
    session.cookies.set("PHPSESSID", phpsessid, domain="libst.sdufe.edu.cn")
    session.cookies.set("PHPSESSID", phpsessid, domain="www.skalibrary.net")
    return session


def build_scan_url() -> str:
    scheme = os.getenv("SCAN_SCHEME", "http").strip().lower()
    if scheme not in {"http", "https"}:
        raise RuntimeError("invalid SCAN_SCHEME")

    timeout = int(os.getenv("TIMEOUT", "10"))
    session = build_session()
    response = session.get(
        TIME_API_URL,
        headers={"Referer": "https://libst.sdufe.edu.cn/"},
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != 1:
        raise RuntimeError(f"token api failed: {payload}")

    token = str(payload.get("data", "")).strip()
    if not token:
        raise RuntimeError(f"empty token: {payload}")

    return f"{scheme}://www.skalibrary.net/wx/scancheck?school=sdufe&type=1&t={quote(token)}"


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/link")
def link():
    try:
        scan_url = build_scan_url()
        return jsonify({"ok": True, "scan_url": scan_url})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/go")
def go():
    try:
        scan_url = build_scan_url()
        return redirect(scan_url, code=302)
    except Exception as exc:
        return redirect(url_for("session_page", reason=str(exc)))


@app.get("/session")
def session_page():
    reason = request.args.get("reason", "")
    current = _load_phpsessid()
    return render_template_string(
        """
        <!doctype html>
        <html>
        <head><meta charset="utf-8"><title>Update PHPSESSID</title></head>
        <body style="font-family: sans-serif; max-width: 720px; margin: 40px auto;">
            <h2>PHPSESSID Update</h2>
            {% if reason %}
              <p style="color:#b00020;"><b>当前会话失效：</b>{{ reason }}</p>
            {% endif %}
            <p>当前值：{{ current_masked }}</p>
            <form method="post" action="/session">
                <label>新的 PHPSESSID：</label><br />
                <input name="phpsessid" style="width:100%;padding:8px;" required />
                <button type="submit" style="margin-top:12px;padding:8px 14px;">保存并立即生效</button>
            </form>
            <p style="margin-top:20px;"><a href="/go">保存后点这里继续签到跳转</a></p>
        </body>
        </html>
        """,
        reason=reason,
        current_masked=_mask(current) if current else "(empty)",
    )


@app.post("/session")
def session_update():
    phpsessid = request.form.get("phpsessid", "").strip()
    if not phpsessid:
        return redirect(url_for("session_page", reason="empty PHPSESSID"))
    try:
        _save_phpsessid(phpsessid)
        return redirect(url_for("go"))
    except Exception as exc:
        return redirect(url_for("session_page", reason=str(exc)))


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    app.run(host=host, port=port)
