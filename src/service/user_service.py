from core.user_manager import UserManager
from dao.config_dao import ConfigDao
from dao.history_dao import HistoryDao


class UserService:
    @classmethod
    def user_chat(cls,user,msg):
        pass

    @classmethod
    def get_last_chat(cls,userlist,now_connect):
        # 查看最近联系人
        UserManager.get_last_chat(userlist,now_connect)

    @classmethod
    def send_file_to_specified_chat(cls):
        # 传文件给指定用户
        pass

    @classmethod
    def get_online_user(cls,userlist):
        # 得到在线用户
        UserManager.show_user(userlist)

    @classmethod
    def get_user_chat_history(cls):
        # 查看用户聊天记录
        pass

    @classmethod
    def change_username(cls,message,user):
        if len(message) < 2 or not message[1]:
            print("[错误] 格式：/nick <新昵称>")
            return False
        new_nick = message[1].strip()
        if not new_nick:
            print("[错误] 昵称不能为空")
            return False
        if new_nick == user.nickname:
            return False
        return True


    @staticmethod
    def help():
        # 显示帮助
        UserManager.help()

    @staticmethod
    def about():
        # 显示版本
        UserManager.about()

    @staticmethod
    def show_history(userlist, target_name=None):
        """显示聊天记录"""
        if target_name is None:
            # 无参数：显示摘要
            UserService._show_history_summary(userlist)
        else:
            # 有参数：显示与指定用户的记录
            UserService._show_history_detail(userlist, target_name)

    @staticmethod
    def _show_history_summary(userlist):
        """显示聊天记录摘要"""
        summary = HistoryDao.get_all_summary()
        if not summary:
            print("[系统] 暂无聊天记录")
            return

        # 构建IP到昵称的映射
        ip_to_nick = {}
        for u in userlist:
            ip_to_nick[u.host] = u.nickname

        print("═══════════════════════════════════════════")
        print("              聊天记录摘要")
        print("═══════════════════════════════════════════")
        print(f"{'对方':<15} {'最后消息时间':<12} {'最后消息'}")
        print("───────────────────────────────────────────")

        for item in summary:
            peer_nick = ip_to_nick.get(item["peer_ip"], item["peer_ip"])
            content = item["last_content"]
            if len(content) > 20:
                content = content[:20] + "..."
            print(f"{peer_nick:<15} {item['last_time']:<12} {content}")
        print("═══════════════════════════════════════════")

    @staticmethod
    def _show_history_detail(userlist, target_name):
        """显示与指定用户的详细聊天记录"""
        # 通过昵称查找IP
        target_ip = None
        target_nick = None
        for u in userlist:
            if u.nickname == target_name:
                target_ip = u.host
                target_nick = u.nickname
                break

        # 如果在线列表中没找到，尝试从历史记录中查找（用户可能已离线）
        if target_ip is None:
            # 遍历历史记录，找到匹配昵称的IP
            for peer_ip, records in HistoryDao._records.items():
                if records and records[0].get("from") == target_name:
                    target_ip = peer_ip
                    target_nick = target_name
                    break

        if target_ip is None:
            print(f'[系统] 与 "{target_name}" 暂无聊天记录')
            return

        records = HistoryDao.get_records_by_ip(target_ip)
        if not records:
            print(f'[系统] 与 "{target_name}" 暂无聊天记录')
            return

        print("═══════════════════════════════════════════")
        print(f"  与 {target_nick} 的聊天记录 (共 {len(records)} 条)")
        print("═══════════════════════════════════════════")

        for record in records:
            from_name = record["from"]
            time_str = record["time"]
            content = record["content"]
            # 如果发送者是自己，显示"[我]"
            if from_name == "我":
                print(f"[我] {time_str}")
            else:
                print(f"[{from_name}] {time_str}:")
            print(f"    {content}")
        print("═══════════════════════════════════════════")