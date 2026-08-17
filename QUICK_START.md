# LanChat 快速使用指南

## 启动

```bash
cd LanChat/src
python main/main.py
```

首次运行会提示输入昵称和端口（默认 9000，回车即可），之后自动读取配置。

---

## 命令速查

| 命令 | 用途 | 示例 |
|------|------|------|
| `/who` | 查看在线用户 | `/who` |
| `/chat <昵称> <消息>` | 按昵称发消息 | `/chat Alice 你好` |
| `/chat *<IP> <消息>` | 按 IP 发消息 | `/chat *192.168.1.100 你好` |
| `/msg <消息>` | 给最近联系人发消息 | `/msg 在吗` |
| `/whois` | 查看最近联系人是谁 | `/whois` |
| `/file <昵称> <路径>` | 发文件 | `/file Alice ./doc.pdf` |
| `/history` | 聊天记录摘要 | `/history` |
| `/history <昵称>` | 与某人的完整记录 | `/history Alice` |
| `/nick <新昵称>` | 改昵称 | `/nick Bob` |
| `/help` | 显示帮助 | `/help` |
| `/exit` | 退出 | `/exit` |

---

## 最简流程（3 步聊天）

```
> /who                          # 1. 看谁在线
> /chat Alice 你好！             # 2. 发消息
> /msg 下午开会吗？               # 3. 继续聊（自动发给最近联系人）
```

---

## 防火墙放行（每台机器都要配）

| 协议 | 端口 | 用途 |
|------|------|------|
| UDP | 9000 | 用户发现 + 聊天 |
| TCP | 9000 | 文件传输 |
| IGMP | — | 组播发现（必须） |

### Windows（管理员 PowerShell）

```powershell
New-NetFirewallRule -DisplayName "LanChat UDP" -Direction Inbound -Protocol UDP -LocalPort 9000 -Action Allow
New-NetFirewallRule -DisplayName "LanChat TCP" -Direction Inbound -Protocol TCP -LocalPort 9000 -Action Allow
```

### Linux（ufw）

```bash
sudo ufw allow 9000/udp && sudo ufw allow 9000/tcp
```

### Linux（iptables）

```bash
sudo iptables -A INPUT -p udp --dport 9000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9000 -j ACCEPT
sudo iptables -A INPUT -p igmp -j ACCEPT
```

### Linux（firewalld）

```bash
sudo firewall-cmd --permanent --add-port=9000/udp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

### macOS

系统偏好设置 → 安全性与隐私 → 防火墙 → 防火墙选项 → 添加 python3 到允许列表

---

## 注意事项

- 所有用户必须在**同一局域网**内
- 组播地址 `224.1.1.1:9000`，心跳间隔 5 秒，30 秒无心跳标记离线
- 聊天记录仅存内存，退出即清空
- 收到的文件保存在 `src/main/LanChat/received/` 目录
- 配置文件位于 `src/main/config.ini`，可手动编辑昵称和端口

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 看不到其他用户 | 检查 IGMP 和 UDP 9000 是否放行，确认同一网段 |
| 发消息对方收不到 | 检查 UDP 9000 入站规则 |
| 文件传输失败 | 检查 TCP 9000 入站规则 |
| 跨网段无法通信 | 组播不跨网段，需配置 IGMP Proxy 或使用同网段 |
