#  coding=UTF-8
#
# 「版本」<插件名>V1_0_0
# 「更新日期」2026/10/19
# 「备注」
# 「更新日志」初始版本
#
# 本插件由临皋闲人（3149790940）封装的 AI Skill 辅助生成
# 来源：https://github.com/chongguang89/olivadice-plugin-dev-internal

import OlivOS
import OlivaDiceCore
import os
import threading
import shutil
import re
import json
import time
import requests


messagelock = threading.Lock()
datafile = "datafile" #数据文件名，请手动修改，保持和插件名一致，且为英文

class Event(object):
    def init(plugin_event, Proc):
        pass

    def group_member_increase(plugin_event, Proc): #监测群成员增加事件
        pass

    def group_member_decrease(plugin_event, Proc): #监测群成员减少事件
        pass

    def group_message(plugin_event, Proc): #群聊消息
        handle_message(plugin_event, Proc, is_group=True)

    def private_message(plugin_event, Proc): #私聊消息
        handle_message(plugin_event, Proc, is_group=False)

    def poke(plugin_event, Proc):
        pass

    def save(plugin_event, Proc):
        pass


def handle_message(plugin_event, Proc, is_group):
    """
    统一消息处理入口，使用 ctx 字典封装常用参数。
    """
    uid = str(plugin_event.data.user_id) #获取用户的qq号
    message = plugin_event.data.message.strip() #获取消息内容
    groupid = str(plugin_event.data.group_id) if is_group else None #获取qq群号
    sender = plugin_event.data.sender.get("name", "未知") #获取发送消息者的qq昵称
    bot_id = str(plugin_event.bot_info.id) #获取bot的qq号
    bot_port = plugin_event.bot_info.post_info.port #获取bot的HTTP端口号
    bot_token = plugin_event.bot_info.post_info.access_token #获取bot的HTTPtoken
    platform = plugin_event.platform["platform"]
    tmp_botHash = plugin_event.bot_info.hash
    masterlist = getMaster(tmp_botHash, platform) #获取管理员/骰主的qq号列表

    # 构建上下文 ctx（推荐所有指令函数统一使用）
    ctx = {
        "plugin_event": plugin_event,
        "Proc": Proc,
        "uid": uid,
        "message": message,
        "groupid": groupid,
        "sender": sender,
        "bot_id": bot_id,
        "bot_port": bot_port,
        "bot_token": bot_token,
        "platform": platform,
        "masterlist": masterlist,
        "is_group": is_group,
    }

    # ========== 示例指令：展示 plugin_event.send 的群聊和私聊调用 ==========
    # 示例1：原地回复（群聊或私聊均可）
    if message == "测试回复":
        plugin_event.reply("这是原地回复，群聊私聊均可")
        return

    # 示例2：群聊发送消息
    if is_group and message == "测试群聊发送":
        plugin_event.send("group", groupid, "这是主动构造的发送到群的消息")
        return

    # 示例3：私聊发送消息
    if not is_group and message == "测试私聊":
        plugin_event.send("private", uid, "这是主动构造私聊回复消息")
        return

    # 示例4：需要管理员权限的指令    
    if is_group:
        if uid in masterlist:
            if message.startswith("指令1"):
                return
            if message.startswith("指令2"):
                return

    # 示例5：需要at格式的指令，id可为bot也可为其他用户
    m_gps = re.match(r"^艾特指令\s*\[OP:at,id=(\d+)\]$", message)
    if m_gps and m_gps.group(1) == bot_id:
        _private_data_check = getData("privategroup.json").get("示例数据", {})
        if uid not in _private_data_check:
            plugin_event.reply(f"「{sender}」无法使用该指令。")
            return
        return

    # 更多指令请在此处添加，可以直接使用 ctx 中的值，例如：
    # if message == "查看信息":
    #     if cmd_help(ctx):
    #         return


# ========== 数据读写（保留原函数及注释） ==========
def getData(filename):
    path = f"./plugin/data/{datafile}/"
    if not os.path.exists(path):
        os.makedirs(path)
    with messagelock:
        try:
            with open(path + filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            try:
                with open(path + filename + ".bak", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    shutil.copy(path + filename + ".bak", path + filename)
            except:
                with open(path + filename, "w", encoding="utf-8") as f:
                    pass
        with open(path + filename, "r", encoding="utf-8") as f:
            file = str(f.read())
            if len(file) == 0:
                data = {}
            else:
                data = json.loads(file)
            return data


def setData(filename, data):
    path = f"./plugin/data/{datafile}/"
    with messagelock:
        try:
            with open(path + filename, "r", encoding="utf-8") as f:
                check = json.load(f)
            shutil.copy(path + filename, path + filename + ".bak")
        except:
            pass
        with open(path + filename, "w", encoding="utf-8") as w:
            json.dump(data, w, indent=4, ensure_ascii=False)


# ========== 骰主列表获取 ==========
def getMaster(tmp_botHash, platform):
    dictConsoleSwitch = OlivaDiceCore.console.dictConsoleSwitch
    masterlist = []
    if tmp_botHash in dictConsoleSwitch:
        if "masterList" in dictConsoleSwitch[tmp_botHash]:
            for master_this in OlivaDiceCore.console.dictConsoleSwitch[tmp_botHash]["masterList"]:
                if master_this[1] == platform:
                    masterlist.append(master_this[0])
    return masterlist


# ========== 通用 API 请求封装 更多API请前往 https://api.luckylillia.com/doc-5341902 获取==========
def api_request(bot_port, bot_token, endpoint, payload, plugin_event=None):
    """
    通用 OneBot API 请求。
    :param bot_port: 骰子 HTTP 端口
    :param bot_token: 骰子 token
    :param endpoint: API 端点，例如 "send_group_msg"
    :param payload: 请求参数字典
    :param plugin_event: 可选，若提供则自动在请求失败时回复错误信息
    :return: 响应字典（含 retcode 等），失败返回 None
    """
    url = f"http://127.0.0.1:{bot_port}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("retcode") == 0:
                return result
            else:
                err_msg = result.get("message") or result.get("wording") or "未知错误"
                if plugin_event:
                    plugin_event.reply(f"【API报错】{endpoint} 失败: {err_msg}")
                return None
        else:
            if plugin_event:
                plugin_event.reply(f"【API报错】{endpoint} 请求失败，状态码 {resp.status_code}")
            return None
    except Exception as e:
        if plugin_event:
            plugin_event.reply(f"【API报错】{endpoint} 请求异常: {e}")
        return None


# ========== API ==========

def get_nickname(bot_port, bot_token, qq_id, plugin_event=None):
    """
    获取指定 QQ 号的昵称（陌生人信息）。
    使用 api_request 统一封装。
    失败时返回 QQ 号字符串。
    """
    result = api_request(bot_port, bot_token, "get_stranger_info",
                         {"user_id": int(qq_id)}, plugin_event)
    if result and "data" in result:
        return result["data"].get("nickname", str(qq_id))
    return str(qq_id)

# ========== 合并转发消息（必须使用bot_id 和 bot_nickname，不可使用发送者id与nickname） ==========
def send_forward_message(bot_port, bot_token, group_id, nodes_data): #可调用该函数构造合并转发消息
    url = f"http://127.0.0.1:{bot_port}/get_login_info"
    headers = {"Authorization": f"Bearer {bot_token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get("retcode") == 0 and "data" in result:
            default_nickname = result["data"].get("nickname", "QQ用户")
        else:
            default_nickname = "QQ用户"
    except Exception:
        default_nickname = "QQ用户"

    def build_node(node_dict):
        uin = node_dict.get("bot_id")
        if not uin:
            return None
        name = node_dict.get("bot_nickname", default_nickname)
        content_list = node_dict.get("content_list")
        if content_list is None:
            content_text = node_dict.get("content_text")
            if content_text is not None:
                content_list = [{"type": "text", "data": {"text": content_text}}]
            else:
                content_list = []
        processed_content = []
        for item in content_list:
            if isinstance(item, dict) and "bot_id" in item:
                sub_node = build_node(item)
                if sub_node:
                    processed_content.append(sub_node)
            else:
                processed_content.append(item)
        return {
            "type": "node",
            "data": {"uin": int(uin), "name": name, "content": processed_content},
        }

    messages = []
    for node in nodes_data:
        built = build_node(node)
        if built:
            messages.append(built)
    payload = {"group_id": int(group_id), "messages": messages}
    url = f"http://127.0.0.1:{bot_port}/send_group_forward_msg"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=10
        )
        return response.json()
    except Exception as e:
        return {"retcode": -1, "message": f"请求失败: {str(e)}"}


# ========== 扩展说明 ==========
"""
【使用说明】
1. 将本文件命名为 main.py，与 app.json、__init__.py 一起放进以插件名命名的文件夹。
2. 修改 datafile = "你的插件英文名"。
3. 在 handle_message 函数中编写自己的指令逻辑。
4. 常用 API 调用：
   - 发送群消息：plugin_event.send("group", groupid, "内容")
   - 发送私聊消息：plugin_event.send("private", uid, "内容")
   - 原地回复：plugin_event.reply("内容")
   - 调用 OneBot API：api_request(bot_port, bot_token, "send_msg", {...})
   - 发送合并转发：send_forward_message(bot_port, bot_token, groupid, nodes)
   - 读取/写入数据：data = getData("xxx.json"); setData("xxx.json", data)

【动笔前必读】
- 先确认协议端：napcat 还是 LLBot？版本多少？（两边扩展接口不通用，字段类型也可能不同）
- 先把需求问清楚：指令原文写法、权限、数据、输出形式、是否涉及批量操作。
- 限速：私聊通知 sleep(1)，批量/分块 sleep(2)，合并转发单次 ≤90 节点（常规 70）。
- 调试用 reply 输出，不要用 print。
- app.json 只改 name / author / namespace / info，且 namespace 必须与 name 完全一致。
"""
