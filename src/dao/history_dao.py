import time
from collections import defaultdict


class HistoryDao:
    """聊天记录管理"""
    # 存储结构：{对方IP: [{"from": "昵称", "content": "消息", "time": "时:分:秒"}, ...]}
    _records = defaultdict(list)

    @classmethod
    def add_record(cls, peer_ip, from_name, content):
        """添加一条聊天记录"""
        record = {
            "from": from_name,
            "content": content,
            "time": time.strftime("%H:%M:%S")
        }
        cls._records[peer_ip].append(record)

    @classmethod
    def get_records_by_ip(cls, peer_ip):
        """获取与指定IP的所有聊天记录"""
        return cls._records.get(peer_ip, [])

    @classmethod
    def get_all_summary(cls):
        """获取所有聊天记录摘要（每人最后一条）"""
        summary = []
        for peer_ip, records in cls._records.items():
            if records:
                last_record = records[-1]
                summary.append({
                    "peer_ip": peer_ip,
                    "last_time": last_record["time"],
                    "last_content": last_record["content"],
                    "total": len(records)
                })
        return summary

    @classmethod
    def clear(cls):
        """清空所有记录"""
        cls._records.clear()