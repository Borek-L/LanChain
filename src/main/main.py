import socket
import struct
import threading
import time
import queue

from service.user_service import UserService
from dao.config_dao import ConfigDao
from po.user import User
from core.file_trans_util import FileTransUtil
from dao.history_dao import HistoryDao

# 在线用户列表
userlist = []
stop_event = threading.Event()
TIMEOUT = 30  # 心跳最大时间

def multicast_sender(conn,group, port,user):
    """发送组播
    用户加入
    """
    while not stop_event.is_set():  # 退出标志
        msg = user.nickname if user.nickname else "anonymous"
        msg = f"HEARTBEAT:{msg}"
        conn.sendto(msg.encode(), (group, port))
        time.sleep(5)

def multicast_receiver(conn,group,port):
    """接收方，接受组播信息
    用户加入：心跳 HEARTBEAT
    用户消息：聊天 CHAT
    """
    while not stop_event.is_set():
        try:
            data, addr = conn.recvfrom(4096)
            data = data.decode().strip()
            # 调试：打印收到的数据来源
            print(f"\n[调试] 收到数据来自 {addr[0]}:{addr[1]}，类型: {data[:20]}...")
            # 字符串解析即可
            if data.startswith("HEARTBEAT:"):
                # 心跳 f"HEARTBEAT:{msg}"
                nick = data[10:].strip()
                # 查找是否存在
                updated = False
                for u in userlist:
                    if u.host == addr[0]:
                        u.nickname = nick
                        u.last_heartbeat = time.time()
                        updated = True
                        break
                if not updated:
                    userlist.append(User(addr[0], addr[1], nick))

            elif data.startswith("CHAT:"):
                # 消息 f"CHAT:{nick_name}:{message}"
                data = data[5:]
                parts = data.split(":", 1)
                if len(parts) < 2:
                    continue  # 格式不正确的消息，跳过
                nick_name, message = parts[0], parts[1]
                print(f"\n[{nick_name}] {time.strftime('%H:%M:%S')}:")
                print(message)
                print(">", end="", flush=True)
                # history
                HistoryDao.add_record(addr[0], nick_name, message)

            elif data.startswith("FILE_REQ:"):
                # 文件请求：FILE_REQ:发送者昵称:文件名:大小
                parts = data[9:].split(":", 2)
                if len(parts) == 3:
                    from_nick, filename, filesize = parts
                    filesize = int(filesize)

                    # 直接在接收线程中询问用户
                    print(f"\n[系统] {from_nick} 向你发送文件 {filename} ({FileTransUtil.format_size(filesize)})，是否接收？(y/n): ",
                          end="", flush=True)

                    choice = input().strip().lower()
                    if choice == "y":
                        conn.sendto(b"FILE_RESP:Y", (addr[0], port))
                        print("[系统] 等待接收文件...")
                    else:
                        conn.sendto(b"FILE_RESP:N", (addr[0], port))
                        print(f"[系统] 已拒绝 {from_nick} 的文件")

                    print(">", end="", flush=True)  # 恢复提示符

            elif data.startswith("FILE_RESP:"):
                # 把响应放入队列，发送方的主线程会取
                resp = data[10:].strip()
                FileTransUtil.file_response_queue.put(resp)

            elif data.startswith("OFFLINE:"):
                nick = data[8:].strip()
                for u in userlist[:]:
                    if u.nickname == nick:
                        userlist.remove(u)
                        print(f"\n[系统] \"{nick}\" 已下线")
                        print(">", end="", flush=True)
                        break

        except socket.timeout:
            continue
        except OSError:
            if stop_event.is_set():
                break
        except Exception as e:
            print(f"\n异常：{e}")
            print(">", end="", flush=True)

def send_one_multicast_msg(sock,group,port,message):
    """单次发送组播信息"""
    sock.sendto(message.encode(), (group, port))

def send_unicast_msg(sock,target_ip,target_port,user_name,message):
    """发送单播信息"""
    message = f"CHAT:{user_name}:{message}"
    sock.sendto(message.encode(), (target_ip, target_port))


def heartbeat_monitor(my_host):
    """心跳超时检测"""
    while not stop_event.is_set():
        # 每10秒检查一次
        time.sleep(10)

        now = time.time()
        offline_list = []

        for u in userlist:
            if u.host == my_host:
                continue
            if now - u.last_heartbeat > TIMEOUT:
                offline_list.append(u)

        # 去除在线列表里面的离线客户端
        for u in offline_list:
            userlist.remove(u)
            print(f"\n[系统] \"{u.nickname}\" 连接超时，已标记离线")
            print(">", end="", flush=True)

def main():
    global userlist,stop_event
    port = 9000
    group = "224.1.1.1"

    # 用户登录
    UserService.about()
    user = ConfigDao.load_config()

    # 1. 创建socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 2. 多地址复用
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    # 3. bind绑定窗口
    sock.bind(("", port))
    sock.settimeout(1)

    # 4. 加入组播，指定接口
    mreq = struct.pack("4s4s", socket.inet_aton(group), socket.inet_aton(user.host))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # 5. 设置发送接口
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(user.host))

    # 6. 设置心跳
    ttl = struct.pack('b', 64)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    # 7. 设置不回环(并且开局发送自身)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    print(f"已入组播组：{group}:{port}，使用接口{user.host}:{user.port}")
    print(f"[调试] 本机 IP: {user.host}，UDP 端口: {port}，TCP 文件端口: {port + 1}")
    myself = User(host=user.host, port=user.port, nickname=user.nickname)
    userlist.append(myself)

    # 8. 启动线程
    ## 1. 接收线程(接收)
    t_recv = threading.Thread(target=multicast_receiver,args=(sock,group,port),daemon=True)
    t_recv.start()

    ## 2. 发送线程(向组播发送)
    t_send = threading.Thread(target=multicast_sender,args=(sock,group,port,user),daemon=True)
    t_send.start()

    ## 3. 文件线程
    t_file = threading.Thread(target=FileTransUtil.tcp_file_server, args=(port,), daemon=True)
    t_file.start()

    ## 4. 心跳超时
    t_monitor = threading.Thread(target=heartbeat_monitor,args=(user.host,),daemon=True)
    t_monitor.start()

    # 9. 主线程堵塞
    try:
        # 开始的时候进行列出在线列表
        UserService.get_online_user(userlist)
        send_one_multicast_msg(sock,group,port,f'[系统] "{user.nickname}" 上线了 ({user.host})')
        while True:
            # 输入
            message = input(">").strip()

            # 退出、帮助、版本信息
            if message in ["/exit"]:
                send_one_multicast_msg(sock, group, port, f'[系统] "{user.nickname}" 已下线')
                print("[系统] 已通知所有在线用户，正在退出...")
                print("[系统] 再见！")
                break
            elif message in ["/help"]:
                UserService.help()
                continue
            elif message in ["/about"]:
                UserService.about()
                continue

            # 信息处理
            message = message.split(" ")
            cmd_type = message[0]

            if cmd_type in ["/chat","/msg"]:
                # 聊天 /chat [*]用户 消息   /msg 消息
                # * ip         无* 昵称
                if cmd_type == '/chat':
                    s_user = message[1]
                    s_msg = "".join(message[2:])
                    # UserService.user_chat(s_user,s_msg)
                    # 格式错误
                    if s_user is None or s_msg is None:
                        print("[错误] 格式：/chat <用户名> <消息内容>")
                        continue

                    # 判断对方是否存在
                    flag = True
                    # 输入ip
                    if s_user[0] == "*":
                        s_user = s_user[1:]
                        # 判断是否为自己
                        if s_user == user.host:
                            print(f"[错误] 不能给自己发消息")
                        else:
                            for u in userlist:
                                if u.host == s_user:
                                    user.now_connect = u.nickname
                                    send_unicast_msg(sock,u.host,u.port,user.nickname,s_msg)
                                    # history
                                    HistoryDao.add_record(u.host, "我", s_msg)
                                    flag = False
                                    break
                    # 输入昵称
                    else:
                        if s_user == user.nickname:
                            print("[错误] 不能给自己发消息")
                        else:
                            for u in userlist:
                                if u.nickname == s_user:
                                    user.now_connect = u.nickname
                                    send_unicast_msg(sock,u.host,u.port,user.nickname,s_msg)
                                    # history
                                    HistoryDao.add_record(u.host, "我", s_msg)
                                    flag = False
                                    break
                    if flag:
                        print(f"[错误] '{s_user}' 当前不在线")


                elif cmd_type == '/msg':
                    s_msg = "".join(message[1:])
                    # UserService.user_chat(user.now_connect,s_msg)
                    if user.now_connect is None:
                        print("[错误] 请先用 /chat <用户名> <消息内容> 发送一条消息")
                        continue
                    flag = True
                    for u in userlist:
                        if u.nickname == user.now_connect:
                            send_unicast_msg(sock,u.host,u.port,u.nickname,s_msg)
                            # history
                            HistoryDao.add_record(u.host, "我", s_msg)
                            flag = False
                            break
                    if flag:
                        print(f"[错误] '{user.now_connect}' 当前不在线")

            elif cmd_type in ["/whois"]:
                # 查看最近联系人
                if user.now_connect is None:
                    print("[系统] 暂无最近联系人，请先用 /chat 发送消息")
                else:
                    UserService.get_last_chat(userlist,user.now_connect)

            elif cmd_type in ["/file"]:
                # 发送文件给指定用户
                if len(message) < 3:
                    print("[错误] 格式：/file <用户> <文件路径>")
                    continue

                target = message[1]
                filepath = message[2]

                # 查找目标用户
                target_user = None
                if target.startswith("*"):
                    ip = target[1:]
                    for u in userlist:
                        if u.host == ip or u.host.endswith("." + ip):
                            target_user = u
                            break
                else:
                    for u in userlist:
                        if u.nickname == target:
                            target_user = u
                            break

                if target_user is None:
                    print(f'[错误] "{target}" 当前不在线')
                elif target_user.host == user.host:
                    print("[错误] 不能给自己发文件")
                else:
                    # 发送文件请求
                    result = FileTransUtil.send_file_request(sock, target_user.host, target_user.port, user.nickname, filepath)
                    if result:
                        # 等待对方响应（超时30秒）
                        try:
                            resp = FileTransUtil.file_response_queue.get(timeout=30)
                            if resp == "Y":
                                # 对方接受，开始TCP传输
                                target_ip, target_port, filepath, filename, filesize = result
                                threading.Thread(
                                    target=FileTransUtil.send_file_tcp,
                                    args=(target_ip, target_port, filepath, filename, filesize),
                                    daemon=True
                                ).start()
                            else:
                                print(f"[系统] 对方拒绝了文件接收")
                        except queue.Empty:
                            print("[错误] 等待对方响应超时")

            elif cmd_type in ["/who"]:
                # 查看在线用户
                UserService.get_online_user(userlist)

            elif cmd_type in ["/history"]:
                # 查看聊天记录
                if len(message) == 1:
                    # 无参数
                    UserService.show_history(userlist)
                elif len(message) == 2:
                    # 有参数
                    UserService.show_history(userlist, message[1])
                else:
                    print("[错误] 格式：/history 或 /history <用户名>")

            elif cmd_type in ["/nick"]:
                # 修改名字
                if UserService.change_username(message,user):
                    old_nick, user.nickname = user.nickname, message[1].strip()
                    ConfigDao.update_nickname(user.nickname)
                    # 更新 userlist
                    for u in userlist:
                        if u.host == user.host and u.port == user.port:
                            u.nickname = user.nickname
                            break
                    send_one_multicast_msg(sock,group,port,f'[系统] "{old_nick}" 已将昵称修改为 "{user.nickname}"')
                    print(f"[系统] 昵称已修改：{old_nick} → {user.nickname}")
                    print("[系统] 已通知所有在线用户，config.ini 已更新")

            else:
                # 报错
                print('错误格式')
                continue

    except KeyboardInterrupt:
        print("退出")

    finally:
        # 结束循环
        stop_event.set()
        # 等待线程退出
        t_recv.join()
        t_send.join()
        t_file.join()
        t_monitor.join()
        sock.close()


if __name__ == '__main__':
    main()
