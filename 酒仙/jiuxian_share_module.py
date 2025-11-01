#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import json
from typing import Dict, Optional, Tuple
from jiuxian_config import JiuxianConfig

class JiuxianShareModule:
    """酒仙分享任务模块"""
    
    def __init__(self, session: requests.Session, token: str, username: str = None):
        self.session = session
        self.token = token
        self.username = username
        self.results = {
            'share_task': '未执行',
            'lottery': '未执行',
            'lottery_prize': '',
            'share_gold': 0
        }
        
        # 小程序User-Agent
        self.user_agent = 'Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.180 Mobile Safari/537.36 XWEB/1380283 MMWEBSDK/20250904 MMWEBID/2537 MicroMessenger/8.0.64.2940(0x2800403E) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wx244a18142bb0c78a'

    def get_phone_tail(self) -> str:
        """获取手机号脱敏显示（后4位）"""
        if self.username and len(self.username) >= 4:
            return f"***{self.username[-4:]}"
        return "***"

    def get_task_status(self) -> Optional[Dict]:
        """获取任务状态信息"""
        try:
            url = JiuxianConfig.MEMBER_INFO_URL
            params = {**JiuxianConfig.MINI_PROGRAM_INFO, 'token': self.token}
            
            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://servicewechat.com/wx244a18142bb0c78a/144/page-frame.html',
                'content-type': 'application/json',
                'secure': 'false',
                'charset': 'utf-8'
            }
            
            response = self.session.get(url, params=params, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') == '1':
                    task_channel = result.get('result', {}).get('taskChannel', {})
                    task_list = task_channel.get('taskList', [])
                    task_token = task_channel.get('taskToken')
                    
                    # 分析任务状态
                    share_task = None
                    for task in task_list:
                        if task.get('id') == 12:  # 分享任务ID
                            share_task = task
                            break
                    
                    return {
                        'task_token': task_token,
                        'share_task': share_task,
                        'complete_count': task_channel.get('completeTaskCount', 0),
                        'total_count': task_channel.get('totalTaskCount', 0),
                        'all_tasks': task_list
                    }
            return None
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 获取任务状态异常 ({phone_tail}): {str(e)}")
            return None

    def check_share_task_status(self) -> Tuple[Optional[str], Optional[Dict], bool]:
        """检查分享任务状态"""
        phone_tail = self.get_phone_tail()
        print(f"🔍 检查分享任务状态 ({phone_tail})...")
        task_status = self.get_task_status()
        
        if not task_status:
            print(f"❌ 获取任务状态失败 ({phone_tail})")
            return None, None, False
        
        task_token = task_status['task_token']
        share_task = task_status['share_task']
        complete_count = task_status['complete_count']
        total_count = task_status['total_count']
        
        print(f"📊 任务完成进度 ({phone_tail}): {complete_count}/{total_count}")
        
        if share_task:
            task_state = share_task.get('state', 0)
            gold_num = share_task.get('goldNum', 0)
            
            # state: 0-未完成, 1-已完成未领取, 2-已完成已领取
            if task_state == 2:
                print(f"✅ 分享任务已完成 ({phone_tail})")
                return task_token, share_task, True
            elif task_state == 1:
                print(f"🔄 分享任务已完成未领取 ({phone_tail})")
                return task_token, share_task, True
            else:
                print(f"❌ 分享任务未完成 ({phone_tail})")
                return task_token, share_task, False
        else:
            print(f"⚠️ 未找到分享任务 ({phone_tail})")
            return task_token, None, False

    def visit_activity_page(self, task_token: str) -> bool:
        """访问活动页面"""
        try:
            url = JiuxianConfig.ACTIVITY_PAGE_URL
            params = {
                'viewType': '2',
                'actId': '7418',
                'taskToken': task_token,
                'taskId': '12',
                'token': self.token
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://servicewechat.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            }
            
            response = self.session.get(url, params=params, headers=headers)
            phone_tail = self.get_phone_tail()
            print(f"📱 访问活动页面 ({phone_tail}): {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 访问活动页面异常 ({phone_tail}): {str(e)}")
            return False

    def report_share_count(self, task_token: str) -> bool:
        """上报分享统计"""
        try:
            # 构建分享统计URL
            share_url = f"https://shop.jiuxian.com/show/wap/act/viewShopActivity.htm?viewType=2&actId=7418&taskToken={task_token}&taskId=12&token={self.token}"
            encoded_url = requests.utils.quote(share_url, safe='')
            
            cnt_url = f"https://s.oadz.com/cnt;C1;1918;.jiuxian.com;khJS5d5rEdLgZqn3Tk9lFCfWpCY=;?1&{encoded_url}&-&-&-&ozlvd=1761917858&ozept=%u300A%u6512%u79EF%u5206%20%u5151%u8305%u53F0%u300B&ozsru=-&ozrucs=0&ozscr=412*915&ozplt=0&ozalx=0&oznvs=-&ozwxid=-&ozsac=-&ozccu=vid%3Dv904bba2010a2f.0%26ctime%3D1761917875%26ltime%3D1761917858&ozccy=erefer%3D-%26eurl%3Dhttps%253A//shop.jiuxian.com/show/wap/act/viewShopActivity.htm%253FviewType%253D2%2526actId%253D7418%2526taskToken%253D{task_token}%2526taskId%253D12%2526token%253D{self.token}%26etime%3D1761917858%26ctime%3D1761917875%26ltime%3D1761917858%26compid%3D1918&ozcck=-&ozccs=-"
            
            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://shop.jiuxian.com/'
            }
            
            response = self.session.get(cnt_url, headers=headers)
            phone_tail = self.get_phone_tail()
            print(f"📊 上报分享统计 ({phone_tail}): {response.status_code}")
            return response.status_code in [200, 302]
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 上报分享统计异常 ({phone_tail}): {str(e)}")
            return False

    def complete_task(self, task_token: str) -> bool:
        """上报任务完成"""
        try:
            url = JiuxianConfig.COMPLETE_TASK_URL
            params = {
                **JiuxianConfig.MINI_PROGRAM_INFO,
                'token': self.token,
                'taskToken': task_token,
                'taskId': '12'
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://servicewechat.com/wx244a18142bb0c78a/144/page-frame.html',
                'content-type': 'application/json',
                'secure': 'false',
                'charset': 'utf-8'
            }
            
            response = self.session.get(url, params=params, headers=headers)
            result = response.json()
            success = result.get('success') == '1'
            phone_tail = self.get_phone_tail()
            print(f"✅ 完成任务 ({phone_tail}): {success}")
            return success
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 完成任务异常 ({phone_tail}): {str(e)}")
            return False

    def receive_share_reward(self) -> bool:
        """领取分享任务奖励"""
        try:
            url = JiuxianConfig.RECEIVE_REWARD_URL
            params = {
                **JiuxianConfig.MINI_PROGRAM_INFO,
                'token': self.token,
                'taskId': '12'
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Referer': 'https://servicewechat.com/wx244a18142bb0c78a/144/page-frame.html',
                'content-type': 'application/json',
                'secure': 'false',
                'charset': 'utf-8'
            }
            
            response = self.session.get(url, params=params, headers=headers)
            result = response.json()
            success = result.get('success') == '1'
            phone_tail = self.get_phone_tail()
            
            if success:
                reward_data = result["result"]
                gold_num = reward_data.get("goldNum", 0)
                self.results['share_gold'] = gold_num
                print(f"🎉 领取分享奖励成功 ({phone_tail})，获得 {gold_num} 金币")
            else:
                print(f"❌ 领取分享奖励失败 ({phone_tail}): {result.get('errMsg', '未知错误')}")
            
            return success
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 领取分享奖励异常 ({phone_tail}): {str(e)}")
            return False

    def lottery_draw(self) -> bool:
        """抽奖功能"""
        try:
            phone_tail = self.get_phone_tail()
            print(f"🎰 开始抽奖 ({phone_tail})...")
            
            # 先访问抽奖页面获取cookie
            draw_url = JiuxianConfig.DRAW_PAGE_URL
            params = {
                'id': '8e8b7f5386194798ab1ae7647f4af6ba',
                'token': self.token
            }
            
            draw_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'X-Requested-With': 'com.tencent.mm',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = self.session.get(draw_url, params=params, headers=draw_headers)
            print(f"🎰 抽奖页面访问 ({phone_tail}): {response.status_code}")
            
            # 执行抽奖
            lottery_url = JiuxianConfig.LOTTERY_DRAW_URL
            current_time = int(time.time() * 1000)
            
            data = {
                'id': '8e8b7f5386194798ab1ae7647f4af6ba',
                'isOrNotAlert': 'false',
                'orderSn': '',
                'advId': '',
                'time': str(current_time)
            }
            
            lottery_headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://h5market2.jiuxian.com',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': f'https://h5market2.jiuxian.com/draw.htm?id=8e8b7f5386194798ab1ae7647f4af6ba&token={self.token}',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = self.session.post(lottery_url, data=data, headers=lottery_headers)
            result = response.json()
            
            # 解析抽奖结果
            if 'luck' in result:
                if result['luck'] is False:
                    print(f"❌ 今日已抽奖 ({phone_tail})")
                    self.results['lottery'] = '已抽过'
                    self.results['lottery_prize'] = '已抽过'
                    return False
                else:
                    luck_info = result.get('luck', {})
                    luck_name = luck_info.get('luckname', '未知')
                    state = luck_info.get('State', 0)
                    object_id = luck_info.get('ObjectID', 0)
                    
                    # State=1, ObjectID=0 是未中奖
                    if state == 1 and object_id == 0:
                        print(f"❌ 未中奖 ({phone_tail}): {luck_name}")
                        self.results['lottery'] = '未中奖'
                        self.results['lottery_prize'] = luck_name
                        return False
                    elif state == 1 and object_id > 0:
                        print(f"🎉 中奖 ({phone_tail}): {luck_name}")
                        self.results['lottery'] = '中奖'
                        self.results['lottery_prize'] = luck_name
                        return True
                    else:
                        print(f"❓ 未知 ({phone_tail}): {luck_name}")
                        self.results['lottery'] = '未知'
                        self.results['lottery_prize'] = luck_name
                        return False
            else:
                print(f"❌ 抽奖失败 ({phone_tail})")
                self.results['lottery'] = '失败'
                self.results['lottery_prize'] = '失败'
                return False
                
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 抽奖异常 ({phone_tail}): {str(e)}")
            self.results['lottery'] = '异常'
            self.results['lottery_prize'] = '异常'
            return False

    def run_share_task(self, task_token: str) -> bool:
        """执行分享任务"""
        phone_tail = self.get_phone_tail()
        print(f"🔄 执行分享任务 ({phone_tail})...")
        
        # 1. 访问活动页面
        if not self.visit_activity_page(task_token):
            print(f"❌ 访问活动页面失败 ({phone_tail})")
            return False
        
        time.sleep(2)
        
        # 2. 上报分享统计
        if not self.report_share_count(task_token):
            print(f"⚠️ 上报分享统计失败 ({phone_tail})，继续执行")
        
        time.sleep(2)
        
        # 3. 上报任务完成
        if not self.complete_task(task_token):
            print(f"❌ 上报任务完成失败 ({phone_tail})")
            return False
        
        time.sleep(2)
        
        # 4. 领取奖励
        if not self.receive_share_reward():
            print(f"❌ 领取奖励失败 ({phone_tail})")
            return False
        
        print(f"✅ 分享任务完成 ({phone_tail})")
        self.results['share_task'] = '完成'
        return True

    def run_share_and_lottery(self) -> Dict:
        """执行分享和抽奖任务"""
        phone_tail = self.get_phone_tail()
        print(f"\n🎯 开始执行分享和抽奖任务 ({phone_tail})")
        
        # 1. 先检查任务状态
        task_token, share_task, is_completed = self.check_share_task_status()
        
        if not task_token:
            print(f"❌ 无法获取taskToken ({phone_tail})，任务终止")
            self.results['share_task'] = '失败'
            return self.results
        
        # 2. 如果分享任务未完成，执行分享任务
        share_success = True
        if not is_completed:
            print(f"🔄 执行分享任务 ({phone_tail})...")
            share_success = self.run_share_task(task_token)
            
            # 重新检查任务状态确认是否完成
            if share_success:
                _, _, is_completed = self.check_share_task_status()
        else:
            print(f"✅ 分享任务已完成 ({phone_tail})")
            self.results['share_task'] = '已完成'
            # 如果是已完成但未领取状态，尝试领取奖励
            if share_task and share_task.get('state') == 1:
                self.receive_share_reward()
        
        # 3. 如果分享任务完成，执行抽奖
        if is_completed:
            print(f"🎰 开始抽奖 ({phone_tail})...")
            self.lottery_draw()
        else:
            print(f"❌ 分享任务未完成 ({phone_tail})，跳过抽奖")
            self.results['lottery'] = '跳过'
            self.results['lottery_prize'] = '任务未完成'
        
        return self.results
