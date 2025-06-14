from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading
from concurrent.futures import ThreadPoolExecutor

class ACPanelController:
    def __init__(self, room_number):
        self.room_number = room_number
        self.url = f"http://localhost:3000/aircon/{room_number}"
        self.driver = None
        self.wait = None
        
    def setup_browser(self):
        """初始化浏览器"""
        options = webdriver.ChromeOptions()
        # 可选：无头模式
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=500,800')
        
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # 打开房间页面
        self.driver.get(self.url)
        print(f"✅ 房间 {self.room_number} 浏览器已启动")
        
    def wait_for_element(self, selector, timeout=10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except:
            print(f"❌ 房间 {self.room_number} 元素未找到: {selector}")
            return None
    
    def power_on(self):
        """开机操作"""
        try:
            power_btn = self.wait_for_element('.power-btn')
            if power_btn:
                button_text = power_btn.text.strip()
                if button_text == '开机':
                    power_btn.click()
                    print(f"✅ 房间 {self.room_number} 开机成功")
                    time.sleep(1)  # 等待状态更新
                elif button_text == '关机':
                    print(f"ℹ️ 房间 {self.room_number} 已经是开机状态")
                elif '请求中' in button_text:
                    print(f"⏳ 房间 {self.room_number} 正在处理请求...")
                    self.wait_for_request_complete()
        except Exception as e:
            print(f"❌ 房间 {self.room_number} 开机失败: {e}")
    
    def power_off(self):
        """关机操作"""
        try:
            power_btn = self.wait_for_element('.power-btn')
            if power_btn:
                button_text = power_btn.text.strip()
                if button_text == '关机':
                    power_btn.click()
                    print(f"✅ 房间 {self.room_number} 关机成功")
                    time.sleep(1)
                elif button_text == '开机':
                    print(f"ℹ️ 房间 {self.room_number} 已经是关机状态")
                elif '请求中' in button_text:
                    print(f"⏳ 房间 {self.room_number} 正在处理请求...")
                    self.wait_for_request_complete()
        except Exception as e:
            print(f"❌ 房间 {self.room_number} 关机失败: {e}")
    
    def wait_for_request_complete(self, max_wait=20):
        """等待请求完成"""
        for _ in range(max_wait):
            try:
                power_btn = self.driver.find_element(By.CSS_SELECTOR, '.power-btn')
                if '请求中' not in power_btn.text:
                    break
                time.sleep(0.5)
            except:
                break
    
    def get_current_target_temp(self):
        """获取当前目标温度"""
        try:
            temp_span = self.driver.find_element(By.CSS_SELECTOR, '.control-group span')
            temp_text = temp_span.text.strip()
            import re
            match = re.search(r'(\d+)', temp_text)
            return int(match.group(1)) if match else None
        except:
            return None
    
    def set_target_temperature(self, target_temp):
        """设置目标温度"""
        try:
            # 检查空调是否开启
            power_btn = self.driver.find_element(By.CSS_SELECTOR, '.power-btn')
            if power_btn.text.strip() == '开机':
                print(f"⚠️ 房间 {self.room_number} 空调未开启，无法设置温度")
                return
            
            current_temp = self.get_current_target_temp()
            if current_temp is None:
                print(f"❌ 房间 {self.room_number} 无法获取当前温度")
                return
            
            diff = target_temp - current_temp
            print(f"📊 房间 {self.room_number} 当前温度: {current_temp}°C → 目标: {target_temp}°C (差值: {diff})")
            
            if diff == 0:
                print(f"ℹ️ 房间 {self.room_number} 温度已经是 {target_temp}°C")
                return
            
            # 找到温度调节按钮
            temp_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.control-group button')
            plus_button = None
            minus_button = None
            
            for btn in temp_buttons:
                if btn.text.strip() == '+':
                    plus_button = btn
                elif btn.text.strip() == '-':
                    minus_button = btn
            
            if diff > 0 and plus_button:
                # 需要增加温度
                for i in range(diff):
                    plus_button.click()
                    print(f"  🔺 房间 {self.room_number} 温度+1 ({i+1}/{diff})")
                    time.sleep(0.3)
            elif diff < 0 and minus_button:
                # 需要减少温度
                for i in range(abs(diff)):
                    minus_button.click()
                    print(f"  🔻 房间 {self.room_number} 温度-1 ({i+1}/{abs(diff)})")
                    time.sleep(0.3)
            
            # 验证最终温度
            time.sleep(0.5)
            final_temp = self.get_current_target_temp()
            if final_temp == target_temp:
                print(f"✅ 房间 {self.room_number} 温度设置成功: {final_temp}°C")
            else:
                print(f"⚠️ 房间 {self.room_number} 温度设置可能失败: 期望{target_temp}°C, 实际{final_temp}°C")
                
        except Exception as e:
            print(f"❌ 房间 {self.room_number} 设置温度失败: {e}")
    
    def set_fan_speed(self, speed):
        """设置风速"""
        try:
            # 检查空调是否开启
            power_btn = self.driver.find_element(By.CSS_SELECTOR, '.power-btn')
            if power_btn.text.strip() == '开机':
                print(f"⚠️ 房间 {self.room_number} 空调未开启，无法设置风速")
                return
            
            speed_map = {'低': 'low', '中': 'medium', '高': 'high'}
            speed_value = speed_map.get(speed, speed)
            
            # 查找风速按钮
            fan_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.control-group button')
            target_button = None
            
            for btn in fan_buttons:
                if btn.text.strip() == speed:
                    target_button = btn
                    break
            
            if target_button:
                target_button.click()
                print(f"✅ 房间 {self.room_number} 风速设置成功: {speed}")
                time.sleep(0.5)
                
                # 验证是否设置成功（检查active类）
                if 'active' in target_button.get_attribute('class'):
                    print(f"✅ 房间 {self.room_number} 风速设置验证成功")
            else:
                print(f"❌ 房间 {self.room_number} 未找到风速按钮: {speed}")
                
        except Exception as e:
            print(f"❌ 房间 {self.room_number} 设置风速失败: {e}")
    
    def get_current_status(self):
        """获取当前状态"""
        try:
            power_btn = self.driver.find_element(By.CSS_SELECTOR, '.power-btn')
            current_temp = self.driver.find_element(By.CSS_SELECTOR, '.current-temp strong')
            target_temp = self.driver.find_element(By.CSS_SELECTOR, '.target-temp strong')
            mode = self.driver.find_element(By.CSS_SELECTOR, '.status-display div:first-child strong')
            fan_speed = self.driver.find_element(By.CSS_SELECTOR, '.status-display div:nth-child(2) strong')
            
            return {
                'isOn': power_btn.text.strip() == '关机',
                'currentTemp': current_temp.text,
                'targetTemp': target_temp.text,
                'mode': mode.text,
                'fanSpeed': fan_speed.text
            }
        except Exception as e:
            print(f"❌ 房间 {self.room_number} 获取状态失败: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print(f"🔒 房间 {self.room_number} 浏览器已关闭")

class ACTestRunner:
    def __init__(self):
        self.rooms = {}
        self.time_slice_interval = 20  # 20秒
        
        # 测试流程定义
        self.test_flow = {
            0: {'101': ['开机']},
            1: {'101': ['目标', 18], '102': ['开机'], '202': ['开机']},
            2: {'103': ['开机']},
            3: {'102': ['目标', 19], '201': ['开机']},
            4: {'202': ['目标', 22]},
            5: {'101': ['风速', '高']},
            6: {'102': ['关机']},
            7: {'102': ['开机'], '202': ['风速', '高']},
            8: {},
            9: {'101': ['目标', 22], '201': ['目标', 18, '风速', '高']},
            10: {},
            11: {'102': ['目标', 22]},
            12: {'202': ['风速', '低']},
            13: {},
            14: {'101': ['关机'], '103': ['目标', 24, '风速', '低']},
            15: {'202': ['目标', 20, '风速', '高']},
            16: {'102': ['关机']},
            17: {'103': ['风速', '高']},
            18: {'101': ['开机'], '201': ['目标', 20, '风速', '中']},
            19: {'102': ['开机']},
            20: {'202': ['目标', 25]},
            21: {},
            22: {'103': ['关机']},
            23: {'202': ['关机']},
            24: {'101': ['关机']},
            25: {'102': ['关机'], '201': ['关机']}
        }
    
    def setup_rooms(self):
        """初始化所有房间"""
        room_numbers = ['101', '102', '103', '201', '202']
        
        print("🚀 正在启动所有房间的浏览器...")
        
        for room_num in room_numbers:
            try:
                controller = ACPanelController(room_num)
                controller.setup_browser()
                self.rooms[room_num] = controller
                time.sleep(2)  # 间隔启动，避免资源冲突
            except Exception as e:
                print(f"❌ 房间 {room_num} 初始化失败: {e}")
        
        print(f"✅ 成功启动 {len(self.rooms)} 个房间")
    
    def execute_room_actions(self, room_num, actions):
        """执行单个房间的操作"""
        if room_num not in self.rooms:
            print(f"❌ 房间 {room_num} 未初始化")
            return
        
        controller = self.rooms[room_num]
        print(f"🏠 房间 {room_num} 执行操作: {actions}")
        
        i = 0
        while i < len(actions):
            action = actions[i]
            
            try:
                if action == '开机':
                    controller.power_on()
                elif action == '关机':
                    controller.power_off()
                elif action == '目标' and i + 1 < len(actions):
                    temperature = actions[i + 1]
                    controller.set_target_temperature(temperature)
                    i += 1  # 跳过下一个参数
                elif action == '风速' and i + 1 < len(actions):
                    speed = actions[i + 1]
                    controller.set_fan_speed(speed)
                    i += 1  # 跳过下一个参数
                
                time.sleep(0.8)  # 操作间隔
                
            except Exception as e:
                print(f"❌ 房间 {room_num} 操作失败: {action}, {e}")
            
            i += 1
    
    def execute_time_slice(self, slice_number):
        """执行单个时间片"""
        actions = self.test_flow.get(slice_number, {})
        
        if not actions:
            print(f"⏱️ 时间片 {slice_number}: 无操作")
            return
        
        print(f"\n🕐 === 时间片 {slice_number} 开始 ({time.strftime('%H:%M:%S')}) ===")
        
        # 并行执行所有房间的操作
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for room_num, room_actions in actions.items():
                future = executor.submit(self.execute_room_actions, room_num, room_actions)
                futures.append(future)
            
            # 等待所有操作完成
            for future in futures:
                future.result()
        
        print(f"✅ 时间片 {slice_number} 完成")
    
    def run_test(self):
        """运行完整测试"""
        print("🎯 开始 ACPanel 自动化测试")
        print(f"📋 测试参数: 时间片间隔 {self.time_slice_interval}秒, 总计 {len(self.test_flow)} 个时间片")
        
        try:
            # 初始化所有房间
            self.setup_rooms()
            
            # 执行所有时间片
            for slice_num in range(26):  # 0-25
                self.execute_time_slice(slice_num)
                
                # 等待下一个时间片
                if slice_num < 25:
                    print(f"⏳ 等待 {self.time_slice_interval} 秒进入下一时间片...\n")
                    time.sleep(self.time_slice_interval)
            
            print("🎉 测试流程完成!")
            
        except KeyboardInterrupt:
            print("\n⏹️ 测试被用户中断")
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("🧹 正在清理资源...")
        for room_num, controller in self.rooms.items():
            controller.close()
        print("✅ 清理完成")

# 使用示例
if __name__ == "__main__":
    # 运行完整测试
    test_runner = ACTestRunner()
    test_runner.run_test()
    
    # 或者手动控制单个房间
    # controller = ACPanelController('101')
    # controller.setup_browser()
    # controller.power_on()
    # controller.set_target_temperature(22)
    # controller.set_fan_speed('高')
    # print(controller.get_current_status())
    # controller.close()