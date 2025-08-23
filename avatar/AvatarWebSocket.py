# -*- coding: utf-8 -*-
import time
import uuid
import queue
import json
from ws4py.client.threadedclient import WebSocketClient
from ws4py.client.threadedclient import WebSocketBaseClient
import _thread
from avatar import AipaasAuth
# import avatar.AipaasAuth
import threading
import cv2


class avatarWebsocket(WebSocketClient, threading.Thread):

    def __init__(self, url, protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None, headers=None,
                 exclude_headers=None, parent=None):
        WebSocketBaseClient.__init__(self, url, protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None,
                                     headers=None, exclude_headers=None)
        threading.Thread.__init__(self)
        self._th = threading.Thread(target=super().run, name='WebSocketClient')
        self._th.daemon = True
        self.appId = ''
        self.vcn = ''
        self.anchorId = ''
        self.dataList = queue.Queue(maxsize=100)
        self.status = True
        self.linkConnected = False
        self.avatarLinked = False
        self.streamUrl = ''
        
        # 添加会话超时相关属性
        self.session_start_time = None
        self.session_timeout = 30 * 60  # 30分钟，单位：秒
        self.timeout_warning_sent = False
        self.timeout_timer = None

    def run(self):
        try:
            # 记录会话开始时间
            self.session_start_time = time.time()
            print(f"Avatar会话开始: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.session_start_time))}")
            
            # 启动超时监控线程
            self.start_timeout_monitor()
            
            self.connect()
            self.connectAvatar()
            _thread.start_new_thread(self.send_Message, ())
            while self.status and not self.terminated:
                self._th.join(timeout=0.1)
        except Exception as e:
            self.status = False
            print(e)
        finally:
            # 清理超时监控
            self.stop_timeout_monitor()

    def start_timeout_monitor(self):
        """启动超时监控线程"""
        self.timeout_timer = threading.Timer(self.session_timeout, self._handle_session_timeout)
        self.timeout_timer.daemon = True
        self.timeout_timer.start()
        
        # 启动25分钟警告定时器
        warning_timer = threading.Timer(25 * 60, self._send_timeout_warning)
        warning_timer.daemon = True
        warning_timer.start()

    def stop_timeout_monitor(self):
        """停止超时监控"""
        if self.timeout_timer:
            self.timeout_timer.cancel()

    def _send_timeout_warning(self):
        """发送超时警告"""
        if self.status and not self.timeout_warning_sent:
            self.timeout_warning_sent = True
            warning_text = "提醒：您的面试会话还有5分钟即将结束，请抓紧时间完成面试。"
            print(f"发送超时警告: {warning_text}")
            self.sendDriverText(warning_text)

    def _handle_session_timeout(self):
        """处理会话超时"""
        if self.status:
            timeout_text = "面试时间已到30分钟，会话即将自动结束。感谢您的参与！"
            print(f"会话超时，自动结束: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
            
            # 发送结束消息
            try:
                self.sendDriverText(timeout_text)
                time.sleep(3)  # 给一点时间让消息发送完成
            except Exception as e:
                print(f"发送超时消息时出错: {e}")
            
            # 强制结束会话
            self.stop()

    def get_session_remaining_time(self):
        """获取会话剩余时间（秒）"""
        if not self.session_start_time:
            return self.session_timeout
        
        elapsed_time = time.time() - self.session_start_time
        remaining_time = max(0, self.session_timeout - elapsed_time)
        return remaining_time

    def get_session_elapsed_time(self):
        """获取会话已用时间（秒）"""
        if not self.session_start_time:
            return 0
        
        return time.time() - self.session_start_time

    def is_session_expired(self):
        """检查会话是否已过期"""
        return self.get_session_remaining_time() <= 0

    def stop(self):
        self.status = False
        self.stop_timeout_monitor()  # 停止超时监控
        self.close(code=1000)

    def send_Message(self):
        """
        send msg to server, if no message to send, send ping msg
        :return:
        """
        while self.status:
            if self.linkConnected:
                try:
                    if self.avatarLinked:
                        task = self.dataList.get(block=True, timeout=5)
                        print('%s send msg: %s' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), task))
                        self.send(task)
                except queue.Empty:
                    if self.status and self.avatarLinked:
                        self.send(self.getPingMsg())
                    else:
                        time.sleep(0.1)
                except AttributeError:
                    pass
            else:
                time.sleep(0.1)

    def sendDriverText(self, driverText):
        """
        send text msg, interactive_mode default 0
        :param driverText:
        :return:
        """
        try:
            print("发送文本：", driverText)
            textMsg = {
                "header": {
                    "app_id": self.appId,
                    "request_id": str(uuid.uuid4()),
                    "ctrl": "text_driver"
                },
                "parameter": {
                    "tts": {
                        "vcn": self.vcn
                    },
                    "avatar_dispatch": {
                        "interactive_mode": 0
                    }
                },
                "payload": {
                    "text": {
                        "content": driverText
                    }
                }
            }
            self.dataList.put_nowait(json.dumps(textMsg))
        except Exception as e:
            print(e)

    def connectAvatar(self):
        """
        send avatar start Msg
        :return:
        """
        try:
            startMsg = {
                "header": {
                    "app_id": self.appId,
                    "request_id": str(uuid.uuid4()),
                    "ctrl": "start"
                },
                "parameter": {
                    "tts": {
                        "vcn": self.vcn
                    },
                    "avatar": {
                        "stream": {
                            "protocol": "rtmp"
                        },
                        "avatar_id": self.anchorId
                    }
                }
            }
            print("%s send start request: %s" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), json.dumps(startMsg)))
            self.send(json.dumps(startMsg))
        except Exception as e:
            print(e)

    def getPingMsg(self):
        """
        :return: ping msg
        """
        pingMsg = {
            "header": {
                "app_id": self.appId,
                "request_id": str(uuid.uuid4()),
                "ctrl": "ping"
            },
        }
        return json.dumps(pingMsg)

    def opened(self):
        """
        ws connected, msg can be sent
        :return:
        """
        self.linkConnected = True

    def closed(self, code, reason=None):
        msg = 'receive closed, code: ' + str(code)
        print(msg)
        self.status = False

    def received_message(self, message):
        try:
            # print(message)
            data = json.loads(str(message))
            if data['header']['code'] != 0:
                self.status = False
                print('receive error msg: %s' % str(message))
            else:
                if 'avatar' in data['payload'] and data['payload']['avatar']['error_code'] == 0 and \
                        data['payload']['avatar']['event_type'] == 'stop':
                    raise BreakException()
                if 'avatar' in data['payload'] and data['payload']['avatar']['event_type'] == 'stream_info':
                    self.avatarLinked = True
                    print('🎭 Avatar WebSocket 连接成功')
                    print('📨 完整消息:', str(message))
                    
                    # 从服务器获取原始streamUrl
                    original_streamUrl = data['payload']['avatar']['stream_url']
                    print('🔗 服务器返回的原始URL:', original_streamUrl)
                    
                    # 保留原始URL中的鉴权参数
                    if '?' in original_streamUrl:
                        base_url, auth_params = original_streamUrl.split('?', 1)
                        # 解析鉴权参数
                        auth_dict = {}
                        for param in auth_params.split('&'):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                auth_dict[key] = value
                        
                        # 只保留必要的鉴权参数
                        needed_params = ['token', 'auth_key', 'auth_time']
                        filtered_params = {k: v for k, v in auth_dict.items() if k in needed_params}
                        
                        # 重构URL
                        if filtered_params:
                            query_string = '&'.join([f"{k}={v}" for k, v in filtered_params.items()])
                            self.streamUrl = f"{base_url}?{query_string}"
                            print('⚠️ 保留鉴权参数:')
                            print(f'   🔴 原始URL: {original_streamUrl}')
                            print(f'   🟢 处理后URL: {self.streamUrl}')
                        else:
                            self.streamUrl = base_url
                            print('⚠️ 未找到鉴权参数，使用基础URL')
                    else:
                        # URL没有参数，直接使用
                        self.streamUrl = original_streamUrl
                        print(f'✅ URL无参数，直接使用: {self.streamUrl}')
                    
                    print(f'🎯 最终设置的streamUrl: {self.streamUrl}')

                if 'avatar' in data['payload'] and data['payload']['avatar']['event_type'] == 'pong':
                    pass
        except BreakException:
            print('receive error but continue')
        except Exception as e:
            print(e)


class BreakException(Exception):
    """自定义异常类，实现异常退出功能"""
    pass


if __name__ == '__main__':
    url = 'wss://avatar.cn-huadong-1.xf-yun.com/v1/interact'
    appId = 'a9730a45'
    appKey = 'fe16118b2de28ee8fff8046b015e3358'
    appSecret = 'NmJkYjU3OTI1NDRlNDViOWY1NjYyYzMx'
    anchorId = 'cnr5dg8n2000000003'
    vcn = 'x4_lingxiaoqi_oral'
    authUrl = AipaasAuth.assemble_auth_url(url, 'GET', appKey, appSecret)
    wsclient = avatarWebsocket(authUrl, protocols='', headers=None)
    try:
        wsclient.appId = appId
        wsclient.anchorId = anchorId
        wsclient.vcn = vcn
        wsclient.start()
        while wsclient.status and not wsclient.terminated:
            time.sleep(15)
            text = '你好，欢迎使用虚拟人'
            wsclient.sendDriverText(text)
    except Exception as e:
        print('receive error')
        print(e)
        wsclient.close()

