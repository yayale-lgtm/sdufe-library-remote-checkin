"""无服务器版本：在手机（Termux / Pythonista / a-Shell）或电脑上直接生成签到链接。

用法：
    python sign_local.py                 # 读取 PHPSESSID 环境变量或 phpsessid.txt，缺失时提示输入
    python sign_local.py 你的PHPSESSID    # 直接传入，并保存到 phpsessid.txt

只依赖 requests。
"""

import os
import shutil
import subprocess
import sys
from urllib.parse import quote

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

TIME_API_URL = "https://libst.sdufe.edu.cn/api.php/v3qrtime"
SESSION_FILE = os.getenv(
    "SESSION_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "phpsessid.txt")
)
DEFAULT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.49(0x1800312c) NetType/WIFI Language/zh_CN"
)


def load_phpsessid() -> str:
    env_value = os.getenv("PHPSESSID", "").strip()
    if env_value:
        return env_value
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_phpsessid(value: str) -> None:
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        f.write(value.strip())


def build_scan_url(phpsessid: str) -> str:
    scheme = os.getenv("SCAN_SCHEME", "http").strip().lower()
    if scheme not in {"http", "https"}:
        raise RuntimeError("invalid SCAN_SCHEME")

    response = requests.get(
        TIME_API_URL,
        headers={
            "User-Agent": os.getenv("USER_AGENT", DEFAULT_UA),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://libst.sdufe.edu.cn/",
            "Cookie": f"PHPSESSID={phpsessid}",
        },
        timeout=int(os.getenv("TIMEOUT", "10")),
        verify=False,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != 1:
        raise RuntimeError(f"token api failed（PHPSESSID 可能已过期）: {payload}")

    token = str(payload.get("data", "")).strip()
    if not token:
        raise RuntimeError(f"empty token: {payload}")

    return f"{scheme}://www.skalibrary.net/wx/scancheck?school=sdufe&type=1&t={quote(token)}"


def copy_to_clipboard(text: str) -> bool:
    # Pythonista
    try:
        import clipboard  # type: ignore

        clipboard.set(text)
        return True
    except ImportError:
        pass

    for cmd in (["termux-clipboard-set"], ["pbcopy"], ["clip"], ["xclip", "-selection", "clipboard"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=5)
                return True
            except Exception:
                continue
    return False


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        phpsessid = sys.argv[1].strip()
        save_phpsessid(phpsessid)
    else:
        phpsessid = load_phpsessid()
        if not phpsessid:
            phpsessid = input("请输入 PHPSESSID：").strip()
            if not phpsessid:
                print("PHPSESSID 为空", file=sys.stderr)
                return 1
            save_phpsessid(phpsessid)

    try:
        scan_url = build_scan_url(phpsessid)
    except Exception as exc:
        print(f"获取签到链接失败：{exc}", file=sys.stderr)
        print("如果是 PHPSESSID 过期，请运行：python sign_local.py 新的PHPSESSID", file=sys.stderr)
        return 1

    print(scan_url)
    if copy_to_clipboard(scan_url):
        print("已复制到剪贴板，粘贴到微信「文件传输助手」后点开即可签到。")
    else:
        print("请复制上面的链接，粘贴到微信「文件传输助手」后点开即可签到。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
