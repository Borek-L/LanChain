import time

class UdpUtil:
    pass
    # @staticmethod
    # def multicast_sender(conn, group, port):
    #     """发送组播"""
    #     while True:
    #         msg = "心跳"
    #         conn.sendto(msg.encode(), (group, port))
    #         # print(f"发送组播")  # 调试
    #         time.sleep(5)
    #
    # @staticmethod
    # def multicast_receiver(conn, group, port,userlist):
    #     """接收方，接受组播信息"""
    #     while True:
    #         data, addr = conn.recvfrom(4096)
    #         # print(f"接收到信息来自 {addr}: {data.decode()}")  # 调试
    #         # 加入用户列表
    #         for e in userlist:
    #             if e[0] != addr[0] or e[1] != addr[1]:
    #                 elem = {
    #                     'port': addr[0],
    #                     'host': addr[1]
    #                 }
    #                 print(f'{addr} 用户')
    #                 userlist.append(elem)