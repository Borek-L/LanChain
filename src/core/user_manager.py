class UserManager:

    @staticmethod
    def help():
        """输出操作信息"""
        print("═══════════════════════════════════════════")
        print("          LanChat 命令帮助中心")
        print("═══════════════════════════════════════════")
        print("  [*]                      含义：(* = IP定位，无* = 昵称定位)")
        print("  /help                    显示所有可用命令及用法")
        print("  /about                   显示软件名称及版本号")
        print("  /chat [*]用户 <消息>       发送消息并记为最近联系人")
        print("  /msg <消息>               向最近联系人发送消息")
        print("  /whois                   查看最近联系人")
        print("  /file [*]用户 <路径>       发送文件给指定用户")
        print("  /who                     查看在线用户列表(主机名、IP、昵称)")
        print("  /history <用户名>          查看聊天记录")
        print("  /nick <新昵称>             修改自己的昵称，并通知全网")
        print("  /exit                     退出程序")
        print("═══════════════════════════════════════════")

    @staticmethod
    def about():
        """显示版本号"""
        print("═══════════════════════════════════════════")
        print("   LanChat v1.0")
        print("   去中心化内网通讯工具")
        print("   架构：对等去中心化")
        print("═══════════════════════════════════════════")

    @staticmethod
    def show_user(userlist):
        """展示用户"""
        print("═══════════════════════════════════════════")
        print(f" 在线用户 (共 {len(userlist)} 人)")
        print("═══════════════════════════════════════════")
        print("序号   昵称     IP地址")
        print("═══════════════════════════════════════════")
        count = 1
        for user in userlist:
            print(f"{count}  {user.nickname}  {user.host}")
            count += 1
        print("═══════════════════════════════════════════")

    @staticmethod
    def change_username():
        return input("请输入您的新昵称：").strip()

    @staticmethod
    def get_last_chat(userlist,now_connect):
        """查看最近联系人"""
        for user in userlist:
            if user == now_connect:
                print(f"最近联系人：{user.nickname}({user.port})")
                break
