import socket
import os
import time
import threading
import queue

class FileTransUtil:
    stop_event = threading.Event()
    # 全局队列，用于主线程和网络线程通信
    file_request_queue = queue.Queue()  # 收到的文件请求
    file_response_queue = queue.Queue()  # 收到的文件响应

    @staticmethod
    def format_size(size):
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 * 1024:.1f} MB"

    @classmethod
    def send_file_request(cls,sock, target_ip, target_port, from_nick, filepath):
        """发送文件请求（UDP信令）"""
        if not os.path.exists(filepath):
            print(f"[错误] 文件不存在: {filepath}")
            return None

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        # 发送文件请求
        req_msg = f"FILE_REQ:{from_nick}:{filename}:{filesize}"
        sock.sendto(req_msg.encode(), (target_ip, target_port))
        print(f"[系统] 正在向 {target_ip} 发送 {filename} ({cls.format_size(filesize)})...")

        return target_ip, target_port, filepath, filename, filesize

    @classmethod
    def send_file_tcp(cls, target_ip, target_port, filepath, filename, filesize):
        """通过TCP发送文件数据
        注意：TCP 文件传输使用 port+1，避免与 UDP 聊天端口冲突
        """
        tcp_port = target_port + 1  # UDP 用 port, TCP 用 port+1
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tcp_sock.connect((target_ip, tcp_port))
            start_time = time.time()
            sent_size = 0

            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    tcp_sock.send(chunk)
                    sent_size += len(chunk)
                    percent = sent_size / filesize * 100
                    print(f"\r[系统] 发送中... {percent:.1f}%", end="")

            tcp_sock.send(b"EOF")

            elapsed = time.time() - start_time
            speed = filesize / elapsed / 1024 if elapsed > 0 else 0
            print(f"\n[系统] 传输完成：{filename} ({cls.format_size(filesize)}, 用时 {elapsed:.1f}s, {speed:.1f} KB/s)")
            return True

        except Exception as e:
            print(f"\n[错误] 文件传输中断: {e}")
            return False
        finally:
            tcp_sock.close()

    @classmethod
    def tcp_file_server(cls, port, save_dir="./LanChat/received"):
        """TCP文件接收服务器线程
        注意：TCP 文件传输使用 port+1，避免与 UDP 聊天端口冲突
        """
        tcp_port = port + 1  # UDP 用 port, TCP 用 port+1
        os.makedirs(save_dir, exist_ok=True)

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("0.0.0.0", tcp_port))
        server_sock.listen(5)
        server_sock.settimeout(1.0)

        while not cls.stop_event.is_set():
            try:
                client_sock, addr = server_sock.accept()

                # 生成文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(save_dir, f"received_{timestamp}")

                print(f"\n[系统] 正在接收文件来自 {addr[0]}...")
                received_size = 0

                with open(filepath, "wb") as f:
                    while True:
                        chunk = client_sock.recv(4096)
                        if chunk == b"EOF" or not chunk:
                            break
                        f.write(chunk)
                        received_size += len(chunk)
                        print(f"\r[系统] 接收中... {cls.format_size(received_size)}", end="")

                client_sock.close()
                print(f"\n[系统] 文件已保存至: {filepath}")
                print(">", end="", flush=True)

            except socket.timeout:
                continue
            except Exception as e:
                if not cls.stop_event.is_set():
                    print(f"\n[错误] 文件接收异常: {e}")

        server_sock.close()