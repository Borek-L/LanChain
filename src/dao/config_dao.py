import socket
import os
from po.user import User
import configparser

class ConfigDao:
    @staticmethod
    def _get_local_ip():
        """自动获取本机局域网IP"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addr = s.getsockname()
        s.close()
        return addr[0] if addr[0] else "127.0.0.1"

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