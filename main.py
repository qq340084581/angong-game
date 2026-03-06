# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty
from kivy.graphics import Rectangle
from kivy.clock import Clock
import threading
import requests
import websocket
import json
import time
from kivy.uix.floatlayout import FloatLayout
import logging
logging.basicConfig(level=logging.DEBUG)
# 最终目标是APK游戏，
Window.size = (390, 844)
Window.title = "三公游戏客户端"

# 服务器地址（请根据实际情况修改）
SERVER_URL = "http://naobaij.v6.army:56900"

# ------------------ 注册弹窗 ------------------
class 注册弹窗(Popup):
    def __init__(self, 登录界面引用, **kwargs):
        super().__init__(**kwargs)
        self.登录界面 = 登录界面引用
        self.title = "注册新账号"
        self.size_hint = (0.8, 0.6)

        内容 = BoxLayout(orientation='vertical', spacing=10, padding=20)

        内容.add_widget(Label(text="用户名:", font_name="simhei.ttf", size_hint_y=0.2))
        self.用户名输入 = TextInput(multiline=False, font_name="simhei.ttf")
        内容.add_widget(self.用户名输入)

        内容.add_widget(Label(text="密码:", font_name="simhei.ttf", size_hint_y=0.2))
        self.密码输入 = TextInput(password=True, multiline=False, font_name="simhei.ttf")
        内容.add_widget(self.密码输入)

        按钮布局 = BoxLayout(size_hint_y=0.3, spacing=10)
        self.注册按钮 = Button(text="注册", font_name="simhei.ttf")
        self.注册按钮.bind(on_press=self.执行注册)
        取消按钮 = Button(text="取消", font_name="simhei.ttf")
        取消按钮.bind(on_press=self.dismiss)
        按钮布局.add_widget(self.注册按钮)
        按钮布局.add_widget(取消按钮)
        内容.add_widget(按钮布局)

        self.提示标签 = Label(text="", color=(1,0,0,1), font_name="simhei.ttf", size_hint_y=0.2)
        内容.add_widget(self.提示标签)

        self.content = 内容

        # 重试相关标志
        self._register_stop_retry = False
        self._register_retry_count = 0
        self._register_max_retries = 10
        self._register_retry_interval = 2
        self._register_in_progress = False

        # 弹窗关闭时停止重试
        self.bind(on_dismiss=self._on_dismiss)

    def _on_dismiss(self, instance):
        self._register_stop_retry = True

    def 执行注册(self, instance):
        if self._register_in_progress:
            return
        self._register_in_progress = True

        用户名 = self.用户名输入.text.strip()
        密码 = self.密码输入.text.strip()

        if not 用户名 or not 密码:
            self.提示标签.text = "用户名和密码不能为空"
            self._register_in_progress = False
            return

        # 禁用注册按钮
        self.注册按钮.disabled = True
        self.提示标签.text = "注册中..."
        self.提示标签.color = (0,0,1,1)

        self._register_stop_retry = False
        self._register_retry_count = 0

        def 注册线程():
            while not self._register_stop_retry and self._register_retry_count < self._register_max_retries:
                try:
                    响应 = requests.post(f"{SERVER_URL}/api/注册", json={
                        "用户名": 用户名,
                        "密码": 密码,
                    }, timeout=10)
                    if 响应.status_code == 200:
                        数据 = 响应.json()
                        Clock.schedule_once(lambda dt: self.注册成功(数据))
                        return
                    else:
                        错误信息 = 响应.json().get("detail", "注册失败")
                        # 服务器错误（5xx）才重试
                        if 响应.status_code >= 500:
                            self._register_retry_count += 1
                            Clock.schedule_once(lambda dt: self.更新提示(f"服务器错误，正在重试 ({self._register_retry_count}/{self._register_max_retries})..."))
                        else:
                            Clock.schedule_once(lambda dt: self.显示错误(错误信息))
                            return
                except Exception as e:
                    self._register_retry_count += 1
                    友好消息 = self._友好错误信息(e)
                    Clock.schedule_once(lambda dt: self.更新提示(f"{友好消息}，正在重试 ({self._register_retry_count}/{self._register_max_retries})..."))

                # 等待重试间隔（每0.1秒检查一次停止标志）
                for i in range(int(self._register_retry_interval * 10)):
                    if self._register_stop_retry:
                        break
                    time.sleep(0.1)

            # 达到最大重试次数
            if self._register_retry_count >= self._register_max_retries:
                Clock.schedule_once(lambda dt: self.显示错误("网络连接失败，请检查网络后重试"))

        threading.Thread(target=注册线程, daemon=True).start()

    def 更新提示(self, 消息):
        self.提示标签.text = 消息
        self.提示标签.color = (0,0,1,1)

    def 注册成功(self, 数据):
        self._register_stop_retry = True
        self.提示标签.text = "注册成功，请登录"
        self.提示标签.color = (0,1,0,1)
        # 自动填充用户名到登录界面
        self.登录界面.用户名输入.text = self.用户名输入.text
        self.登录界面.密码输入.text = ""
        # 延迟关闭弹窗
        Clock.schedule_once(lambda dt: self._启用注册按钮并关闭(), 1.5)

    def _启用注册按钮并关闭(self):
        self.注册按钮.disabled = False
        self._register_in_progress = False
        self.dismiss()

    def 显示错误(self, 错误信息):
        self.提示标签.text = f"错误: {错误信息}"
        self.提示标签.color = (1,0,0,1)
        self.注册按钮.disabled = False
        self._register_in_progress = False

    def _友好错误信息(self, e):
        if isinstance(e, requests.exceptions.ConnectionError):
            return "网络连接失败，请检查网络或服务器地址"
        elif isinstance(e, requests.exceptions.Timeout):
            return "连接超时，请稍后重试"
        elif isinstance(e, requests.exceptions.RequestException):
            return "请求出错，请稍后重试"
        else:
            return f"发生错误: {str(e)}"

# ------------------ 登录界面 ------------------
class 登录界面(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 使用 FloatLayout 以便自由放置子控件
        self.root_layout = FloatLayout()
        self.add_widget(self.root_layout)

        # 背景图片（全屏）
        with self.root_layout.canvas.before:
            self.背景图 = Rectangle(source='jiemian.jpg', pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._更新背景, size=self._更新背景)

        # 登录表单容器（垂直布局，占屏幕宽80%、高50%，居中）
        表单 = BoxLayout(
            orientation='vertical',
            spacing=15,
            padding=[20, 20],
            size_hint=(0.8, 0.5),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.root_layout.add_widget(表单)

        # 标题
        标题 = Label(
            text="欢迎登录,聪哥三公",
            font_size='28sp',
            color=(1,0.84,0,1),
            size_hint_y=0.2,
            font_name="simhei.ttf",
            halign='center',
            valign='middle'
        )
        表单.add_widget(标题)

        # 用户名输入
        self.用户名输入 = TextInput(
            hint_text="用户名",
            multiline=False,
            size_hint_y=0.2,
            background_color=(1,1,1,1),
            foreground_color=(0,0,0,1),
            font_name="simhei.ttf"
        )
        表单.add_widget(self.用户名输入)

        # 密码输入
        self.密码输入 = TextInput(
            hint_text="密码",
            password=True,
            multiline=False,
            size_hint_y=0.2,
            background_color=(1,1,1,1),
            foreground_color=(0,0,0,1),
            font_name="simhei.ttf"
        )
        表单.add_widget(self.密码输入)

        # 登录按钮
        self.登录按钮 = Button(
            text="登录",
            size_hint_y=0.2,
            background_color=(0.1, 0.5, 0.3, 1),
            color=(1,0.84,0,1),
            font_name="simhei.ttf"
        )
        self.登录按钮.bind(on_press=self.登录处理)
        表单.add_widget(self.登录按钮)

        # 注册按钮
        注册按钮 = Button(
            text="注册新账号",
            size_hint_y=0.15,
            background_color=(0.2, 0.3, 0.7, 1),
            color=(1,0.84,0,1),
            font_name="simhei.ttf"
        )
        注册按钮.bind(on_press=self.显示注册)
        表单.add_widget(注册按钮)

        # 提示信息标签
        self.提示标签 = Label(
            text="",
            color=(1,0,0,1),
            size_hint_y=0.1,
            font_name="simhei.ttf",
            halign='center',
            valign='middle'
        )
        表单.add_widget(self.提示标签)

        # 重试相关标志
        self._login_stop_retry = False
        self._login_retry_count = 0
        self._login_max_retries = 10
        self._login_retry_interval = 2
        self._login_in_progress = False

    def _更新背景(self, instance, value):
        self.背景图.pos = instance.pos
        self.背景图.size = instance.size

    def 显示注册(self, instance):
        弹窗 = 注册弹窗(self)
        弹窗.open()

    def 登录处理(self, instance):
        if self._login_in_progress:
            return
        self._login_in_progress = True

        用户名 = self.用户名输入.text.strip()
        密码 = self.密码输入.text.strip()
        if not 用户名 or not 密码:
            self.提示标签.text = "用户名和密码不能为空"
            self._login_in_progress = False
            return

        # 禁用登录按钮
        self.登录按钮.disabled = True
        self.提示标签.text = "登录中..."
        self.提示标签.color = (0,0,1,1)

        self._login_stop_retry = False
        self._login_retry_count = 0

        def 登录线程():
            while not self._login_stop_retry and self._login_retry_count < self._login_max_retries:
                try:
                    响应 = requests.post(f"{SERVER_URL}/api/登录", json={
                        "用户名": 用户名,
                        "密码": 密码
                    }, timeout=10)
                    if 响应.status_code == 200:
                        数据 = 响应.json()
                        Clock.schedule_once(lambda dt: self.登录成功(数据))
                        return
                    else:
                        错误信息 = 响应.json().get("detail", "登录失败")
                        # 服务器错误（5xx）才重试
                        if 响应.status_code >= 500:
                            self._login_retry_count += 1
                            Clock.schedule_once(lambda dt: self.更新提示(f"服务器错误，正在重试 ({self._login_retry_count}/{self._login_max_retries})..."))
                        else:
                            Clock.schedule_once(lambda dt: self.显示错误(错误信息))
                            return
                except Exception as e:
                    self._login_retry_count += 1
                    友好消息 = self._友好错误信息(e)
                    Clock.schedule_once(lambda dt: self.更新提示(f"{友好消息}，正在重试 ({self._login_retry_count}/{self._login_max_retries})..."))

                # 等待重试间隔（每0.1秒检查一次停止标志）
                for i in range(int(self._login_retry_interval * 10)):
                    if self._login_stop_retry:
                        break
                    time.sleep(0.1)

            # 达到最大重试次数
            if self._login_retry_count >= self._login_max_retries:
                Clock.schedule_once(lambda dt: self.显示错误("网络连接失败，请检查网络后重试"))
            else:
                # 如果是因为停止标志退出，不额外处理
                pass

        threading.Thread(target=登录线程, daemon=True).start()

    def 更新提示(self, 消息):
        self.提示标签.text = 消息
        self.提示标签.color = (0,0,1,1)

    def 登录成功(self, 数据):
        self._login_stop_retry = True
        print("登录返回数据:", 数据)
        self.提示标签.text = ""
        大厅界面 = self.manager.get_screen('game_lobby')
        大厅界面.更新用户信息(数据["用户名"], 数据["积分"])
        self.manager.current = 'game_lobby'
        # 启用登录按钮（虽然已经切换到大厅，但为防万一）
        self.登录按钮.disabled = False
        self._login_in_progress = False

    def 显示错误(self, 错误信息):
        self.提示标签.text = f"错误: {错误信息}"
        self.提示标签.color = (1,0,0,1)
        self.登录按钮.disabled = False
        self._login_in_progress = False

    def on_enter(self, *args):
        """进入登录界面时设置为竖屏"""
        Window.orientation = 'portrait'

    def on_leave(self, *args):
        """离开登录界面时停止重试"""
        self._login_stop_retry = True
        super().on_leave(*args)

    def _友好错误信息(self, e):
        if isinstance(e, requests.exceptions.ConnectionError):
            return "网络连接失败，请检查网络或服务器地址"
        elif isinstance(e, requests.exceptions.Timeout):
            return "连接超时，请稍后重试"
        elif isinstance(e, requests.exceptions.RequestException):
            return "请求出错，请稍后重试"
        else:
            return f"发生错误: {str(e)}"

# ------------------ 游戏大厅界面 ------------------
class 游戏大厅界面(Screen):
    用户名 = StringProperty('')
    积分 = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.弹窗音乐 = None
        self.ws = None
        self.ws_thread = None
        self.ws_connected = False
        主布局 = BoxLayout(orientation='vertical', spacing=10, padding=[20, 20])
        self.add_widget(主布局)

        # 顶部信息栏（头像、用户名、积分）
        顶部栏 = BoxLayout(size_hint_y=0.15, spacing=15)
        主布局.add_widget(顶部栏)

        # 头像
        self.头像 = Image(source='touxiang.png', size_hint=(None, None), size=(50,50))
        顶部栏.add_widget(self.头像)

        # 用户名标签
        self.用户名标签 = Label(
            text=self.用户名,
            font_size=20,
            color=(1,1,1,1),
            font_name="simhei.ttf",
            halign='left'
        )
        顶部栏.add_widget(self.用户名标签)

        # 积分标签
        self.积分标签 = Label(
            text=f"积分：{self.积分}",
            font_size=20,
            color=(1,1,1,1),
            font_name="simhei.ttf",
            halign='right'
        )
        顶部栏.add_widget(self.积分标签)

        # 闪耀文字（欢迎语）
        self.闪耀文字 = Label(
            text="欢迎来到公测版本，聪哥三公",
            font_size=24,
            color=(1,0.84,0,1),  # 金色
            font_name="simhei.ttf",
            size_hint_y=0.1
        )
        主布局.add_widget(self.闪耀文字)
        self.开始闪耀动画()

        # 游戏按钮网格（2行3列）
        网格 = GridLayout(cols=3, rows=2, spacing=10, size_hint_y=0.6)
        主布局.add_widget(网格)

        游戏列表 = ["三公", "斗地主", "十三张", "斗金花", "牛牛", "设置"]
        for 游戏名 in 游戏列表:
            按钮 = Button(
                text=游戏名,
                font_name="simhei.ttf",
                background_color=(0, 1, 1, 0.3),  # 青色半透明
                color=(1,0.84,0,1)
            )
            按钮.bind(on_press=self.按钮点击占位)
            网格.add_widget(按钮)

        # 退出登录按钮
        退出按钮 = Button(
            text="退出登录",
            size_hint_y=0.1,
            font_name="simhei.ttf",
            background_color=(0.8, 0.2, 0.2, 1)
        )
        退出按钮.bind(on_press=self.退出登录)
        主布局.add_widget(退出按钮)

        # 设置背景图片
        with self.canvas.before:
            self.大厅背景图 = Rectangle()
        self.大厅背景图.source = 'youxineib.png'
        self.大厅背景图.pos = self.pos
        self.大厅背景图.size = self.size
        self.bind(size=self._更新大厅背景, pos=self._更新大厅背景)

    def 连接WebSocket(self):
        if self.ws_connected:
            return
        # 服务器 WebSocket 地址，使用与 HTTP 相同的域名和端口
        ws_url = f"ws://naobaij.v6.army:56900/ws/lobby"  # 房间ID可以固定或动态生成
        try:
            self.ws = websocket.WebSocketApp(ws_url,
                on_open=self.on_ws_open,
                on_message=self.on_ws_message,
                on_error=self.on_ws_error,
                on_close=self.on_ws_close)
            self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()
        except Exception as e:
            print(f"WebSocket 连接失败: {e}")

    def on_ws_open(self, ws):
        print("WebSocket 已连接")
        self.ws_connected = True
        # 发送第一条消息：用户名
        ws.send(json.dumps({"用户名": self.用户名}))

    def on_ws_message(self, ws, message):
        # 在后台线程中接收消息，通过 Clock 调度到主线程处理
        Clock.schedule_once(lambda dt: self.处理WebSocket消息(message))

    def on_ws_error(self, ws, error):
        print(f"WebSocket 错误: {error}")

    def on_ws_close(self, ws, close_status_code, close_msg):
        print("WebSocket 已关闭")
        self.ws_connected = False

    def 处理WebSocket消息(self, 消息):
        try:
            数据 = json.loads(消息)
            类型 = 数据.get("type")
            if 类型 == "积分更新":
                新积分 = 数据.get("新积分")
                if 新积分 is not None:
                    self.积分 = 新积分
                    self.积分标签.text = f"积分：{新积分}"
                    print(f"积分更新为: {新积分}")
            # 其他消息类型可扩展
        except Exception as e:
            print(f"处理WebSocket消息出错: {e}")

    def _更新大厅背景(self, 实例, 值):
        self.大厅背景图.pos = self.pos
        self.大厅背景图.size = self.size

    def 更新用户信息(self, 用户名, 积分):
        self.用户名 = 用户名
        self.积分 = 积分
        self.用户名标签.text = 用户名
        self.积分标签.text = f"积分：{积分}"
        # 连接 WebSocket（如果尚未连接）
        if not self.ws_connected:
            self.连接WebSocket()

    def 按钮点击占位(self, 实例):
        """点击游戏按钮时弹出提示并播放一次音效"""
        内容 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        标签 = Label(text="0积分请充值", font_name="simhei.ttf")
        关闭按钮 = Button(text="关闭", size_hint_y=0.3, font_name="simhei.ttf")
        内容.add_widget(标签)
        内容.add_widget(关闭按钮)

        弹窗 = Popup(title="提示", content=内容, size_hint=(0.6, 0.4))
        关闭按钮.bind(on_press=弹窗.dismiss)

        try:
            if self.弹窗音乐:
                self.弹窗音乐.stop()
            self.弹窗音乐 = SoundLoader.load('tanchuyiny.mp3')
            if self.弹窗音乐:
                self.弹窗音乐.play()
            else:
                print("⚠️ 无法加载弹窗音乐文件")
        except Exception as e:
            print(f"❌ 播放弹窗音乐时出错: {e}")

        弹窗.open()

    def 尝试重连(self, *args):
        if not self.ws_connected and self.用户名:
            print("尝试重连 WebSocket...")
            self.连接WebSocket()

    def 退出登录(self, 实例):
        if self.ws:
            self.ws.close()
            self.ws_connected = False
        # 返回登录界面，并清空输入框和提示
        登录界面 = self.manager.get_screen('login')
        登录界面.用户名输入.text = ''
        登录界面.密码输入.text = ''
        登录界面.提示标签.text = ''
        self.manager.current = 'login'

    def 开始闪耀动画(self):
        颜色动画 = Animation(color=(1,0,0,1), duration=0.8) + Animation(color=(1,0.84,0,1), duration=0.8)
        颜色动画.repeat = True
        大小动画 = Animation(font_size=30, duration=0.6) + Animation(font_size=24, duration=0.6)
        大小动画.repeat = True
        颜色动画.start(self.闪耀文字)
        大小动画.start(self.闪耀文字)

    def on_enter(self, *args):
        """进入游戏大厅界面时设置为横屏"""
        Window.orientation = 'landscape'

# ------------------ 应用程序主类 ------------------
class 登录应用(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.背景音乐 = None

    def build(self):
        管理器 = ScreenManager()

        登录 = 登录界面(name='login')
        管理器.add_widget(登录)

        大厅 = 游戏大厅界面(name='game_lobby')
        管理器.add_widget(大厅)

        self.播放背景音乐()

        return 管理器

    def 播放背景音乐(self):
        try:
            self.背景音乐 = SoundLoader.load('jiemianyinyue.mp3')
            if self.背景音乐:
                self.背景音乐.loop = True
                self.背景音乐.play()
                print("✅ 背景音乐已开始播放")
            else:
                print("⚠️ 无法加载背景音乐文件")
        except Exception as e:
            print(f"❌ 播放背景音乐时出错: {e}")

    def on_stop(self):
        if self.背景音乐:
            self.背景音乐.stop()
            print("🛑 背景音乐已停止")

if __name__ == '__main__':
    登录应用().run()