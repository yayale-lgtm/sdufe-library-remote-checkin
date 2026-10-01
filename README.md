# sdufe-library-remote-checkin

山东财经大学图书馆远程签到辅助项目，仅供学习研究与自动化测试交流。

这是一个轻量 Flask 服务：手机访问固定入口时，服务端实时获取最新参数并跳转到签到链接。`PHPSESSID` 过期时，页面会引导你更新新的会话值，无需重启服务。

## 公共服务（已停止）

之前提供的公共服务 `http://8.136.185.53:8080` 因服务器到期已停止，相关链接均不可用。

如需继续使用，推荐下面的「无服务器方案」，直接在手机上生成签到链接；也可以按后文步骤自行部署 Flask 服务。

## 无服务器方案（推荐）

签到链接本质上只需要一次请求：带上 `PHPSESSID` 请求 `v3qrtime` 拿到 token，再拼成签到链接。这一步可以直接在手机上完成，不需要服务器。

### 方案 A：iPhone「快捷指令」（无需安装任何东西）

在「快捷指令」App 新建快捷指令，依次添加以下操作：

1. **URL**：`https://libst.sdufe.edu.cn/api.php/v3qrtime`
2. **获取 URL 内容**：方法 `GET`，展开「头部」添加三项：
   - `Cookie` = `PHPSESSID=你的PHPSESSID`
   - `Referer` = `https://libst.sdufe.edu.cn/`
   - `User-Agent` = `Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.49(0x1800312c) NetType/WIFI Language/zh_CN`
3. **获取词典值**：获取「URL 的内容」中 `data` 的值
4. **URL 编码**：编码「词典值」
5. **文本**：`http://www.skalibrary.net/wx/scancheck?school=sdufe&type=1&t=`，后面插入变量「URL 编码的文本」
6. **拷贝到剪贴板**：「文本」
7. **打开 URL**：`weixin://`

运行后会自动打开微信，把链接粘贴到「文件传输助手」发送并点开即可签到。可以把快捷指令添加到主屏幕，一键运行。

`PHPSESSID` 过期时（第 3 步取不到 `data`），只需修改第 2 步里的 `Cookie` 值。

### 方案 B：在手机上运行 Python 脚本

仓库中的 `sign_local.py` 是独立脚本，只依赖 `requests`，可以在手机或电脑上直接运行：

- **Android**：安装 [Termux](https://f-droid.org/packages/com.termux/)（如需自动复制到剪贴板，再装 Termux:API）：

  ```bash
  pkg install python termux-api
  pip install requests
  python sign_local.py 你的PHPSESSID   # 首次运行，会保存到 phpsessid.txt
  python sign_local.py                 # 之后直接运行
  ```

- **iPhone**：在 Pythonista 或 a-Shell 中运行 `sign_local.py`（a-Shell 需先执行 `pip install requests`）。

脚本会输出签到链接并尽量复制到剪贴板，粘贴到微信「文件传输助手」后点开即可。`PHPSESSID` 过期时运行 `python sign_local.py 新的PHPSESSID` 即可更新。

> Android 用户也可以用「HTTP Shortcuts」等 App 按方案 A 的思路配置，无需 Termux。

## 自建服务器方案

### 功能

- `GET /go`：实时获取最新参数并 302 跳转到签到入口。
- `GET /link`：返回当前实时签到链接 JSON。
- `GET /session`：显示表单，手动更新 `PHPSESSID`。
- `POST /session`：保存新的 `PHPSESSID` 到本地文件，立即生效。
- `GET /health`：服务健康检查。

### 安装

```powershell
mkdir C:\signbot -Force
cd C:\signbot
py -m pip install -r requirements.txt
```

如果服务器上没有 `requirements.txt`，也可以直接安装：

```powershell
py -m pip install flask requests
```

把 `sign_web.py` 放到：

```text
C:\signbot\sign_web.py
```

### 配置

可选环境变量：

```powershell
setx SCAN_SCHEME "http" /M
setx PORT "8080" /M
```

首次使用可以不设置 `PHPSESSID`。访问 `/go` 时，如果没有可用会话，会自动跳到 `/session` 页面让你填写。

`PHPSESSID` 会保存到：

```text
phpsessid.txt
```

不要把这个文件提交到 GitHub。

### 启动

```powershell
python C:\signbot\sign_web.py
```

默认监听：

```text
0.0.0.0:8080
```

如果部署在云服务器，需要在云安全组和 Windows 防火墙放行 TCP `8080`。

### 使用

手机访问：

```text
http://你的服务器IP:8080/go
```

行为：

1. 如果 `PHPSESSID` 有效，会实时生成并跳转到签到链接。
2. 如果 `PHPSESSID` 缺失或失效，会自动跳到 `/session`。
3. 在 `/session` 输入新的 `PHPSESSID` 后，会保存并自动继续跳转。

其他接口：

```text
http://你的服务器IP:8080/session
http://你的服务器IP:8080/link
http://你的服务器IP:8080/health
```

### 开机自启（Windows）

```powershell
schtasks /Create /TN "SignWeb" /SC ONSTART /RU "SYSTEM" /RL HIGHEST /TR "cmd /c cd /d C:\signbot && python sign_web.py" /F
schtasks /Run /TN "SignWeb"
```

## 注意

- `PHPSESSID` 是登录会话，会过期。
- 过期后访问 `/go` 会进入 `/session`，重新填写一次即可。
- 建议后续给 `/session` 加密码保护，避免公开服务器被别人修改会话值。
