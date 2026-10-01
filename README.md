# sdufe-library-remote-checkin

山东财经大学图书馆远程签到辅助项目，仅供学习研究与自动化测试交流。

这是一个轻量 Flask 服务：手机访问固定入口时，服务端实时获取最新参数并跳转到签到链接。`PHPSESSID` 过期时，页面会引导你更新新的会话值，无需重启服务。

## 公共服务（已停止）

之前提供的公共服务 `http://8.136.185.53:8080` 因服务器到期已停止，相关链接均不可用。

如需继续使用，请按下文步骤用仓库代码自行部署（本地电脑或任意云服务器均可）。

## 功能

- `GET /go`：实时获取最新参数并 302 跳转到签到入口。
- `GET /link`：返回当前实时签到链接 JSON。
- `GET /session`：显示表单，手动更新 `PHPSESSID`。
- `POST /session`：保存新的 `PHPSESSID` 到本地文件，立即生效。
- `GET /health`：服务健康检查。

## 安装

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

## 配置

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

## 启动

```powershell
python C:\signbot\sign_web.py
```

默认监听：

```text
0.0.0.0:8080
```

如果部署在云服务器，需要在云安全组和 Windows 防火墙放行 TCP `8080`。

## 使用

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

## 开机自启（Windows）

```powershell
schtasks /Create /TN "SignWeb" /SC ONSTART /RU "SYSTEM" /RL HIGHEST /TR "cmd /c cd /d C:\signbot && python sign_web.py" /F
schtasks /Run /TN "SignWeb"
```

## 注意

- `PHPSESSID` 是登录会话，会过期。
- 过期后访问 `/go` 会进入 `/session`，重新填写一次即可。
- 建议后续给 `/session` 加密码保护，避免公开服务器被别人修改会话值。
