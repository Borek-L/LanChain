import socket
import os
from po.user import User
import configparser

class ConfigDao:
    @staticmethod
    def _get_local_ip():
        """自动获取本机局域网IP
        优先使用 UDP connect 方式（不真正发送数据），
        失败时回退到 hostname 解析方式，适配内网无外网环境。
        """
        # 方法1：UDP connect（推荐，能穿透 NAT 获取真实出口 IP）
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # 方法2：通过 hostname 解析
        try:
            import platform
            hostname = platform.node()
            ip = socket.gethostbyname(hostname)
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # 方法3：遍历所有网络接口
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            # 使用局域网广播地址探测
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        return "127.0.0.1"

    @staticmethod
    def load_config():
        """
        启动时加载配置：
            存在则读取，
            不存在则输入并生成
        """
        config = configparser.ConfigParser()

        if os.path.exists('config.ini'):
            config.read("config.ini")
            nickname = config.get("User", "nickname", fallback="")
            port = config.getint("User", "port", fallback=9000)
            host = ConfigDao._get_local_ip()

        else:
            nickname = input("请输入你的昵称（可选，回车跳过）：").strip()
            port_str = input("请输入监听端口（默认 9000）：").strip()
            port = int(port_str) if port_str else 9000
            host = ConfigDao._get_local_ip()

            config["User"] = {
                "nickname": nickname,
                "port": str(port)
            }
            with open("config.ini", "w", encoding="utf-8") as f:
                config.write(f)

        return User(host, port, nickname)

    @staticmethod
    def update_nickname(new_nickname):
        """更新文件昵称，写入磁盘.ini文件"""
        config = configparser.ConfigParser()
        config.read("config.ini")
        if not config.has_section("User"):
            config.add_section("User")
        config.set("User", "nickname", new_nickname)
        with open("config.ini", "w") as f:
            config.write(f)