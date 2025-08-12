import requests
import base64
import ddddocr
import json
import time
import re
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from urllib.parse import quote
import logging
from datetime import datetime
import os
from models import db, Account, LoginLog

class LoginService:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Referer": "https://cms.ayybyyy.com/"
        }
        
        # 固定公钥
        self.first_public_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNR7I+SpqIZM5w3Aw4lrUlhrs7VurKbeViYXNhOfIgP/4acsWvJy5dPb/FejzUiv2cAiz5As2DJEQYEM10LvnmpnKx9Dq+QDo7WXnT6H2szRtX/8Q56Rlzp9bJMlZy7/i0xevlDrWZMWqx2IK3ZhO9+0nPu4z4SLXaoQGIrs7JxwIDAQAB"
        
        # 初始化OCR
        self.ocr = ddddocr.DdddOcr()
        self.max_attempts = 5
        
        # 设置日志
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志记录"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"login_{datetime.now().strftime('%Y-%m-%d')}.log"), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("LoginService")
    
    def save_log(self, account_id, level, message, details=None, is_success=False):
        """保存日志到数据库"""
        try:
            log = LoginLog(
                account_id=account_id,
                level=level,
                message=message,
                details=json.dumps(details) if details else None,
                is_success=is_success
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            self.logger.error(f"保存日志失败: {str(e)}")
    
    def get_token(self):
        """获取token"""
        url = "https://cmsapi3.qiucheng-wangluo.com/cms-api/token/generateCaptchaToken"
        try:
            response = self.session.post(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("iErrCode") == 0:
                    return result.get("result")
            return None
        except Exception as e:
            self.logger.error(f"获取token失败: {str(e)}")
            return None
    
    def get_captcha(self, token):
        """获取验证码图片"""
        url = "https://cmsapi3.qiucheng-wangluo.com/cms-api/captcha"
        data = {"token": token}
        try:
            response = self.session.post(url, headers=self.headers, data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("iErrCode") == 0:
                    return result.get("result")
            return None
        except Exception as e:
            self.logger.error(f"获取验证码失败: {str(e)}")
            return None
    
    def recognize_captcha(self, captcha_base64):
        """识别验证码"""
        try:
            captcha_img = base64.b64decode(captcha_base64)
            captcha_text = self.ocr.classification(captcha_img)
            captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
            if len(captcha_text) > 4:
                captcha_text = captcha_text[:4]
            return captcha_text.upper()
        except Exception as e:
            self.logger.error(f"识别验证码失败: {str(e)}")
            return None
    
    def load_public_key(self, key_str):
        """加载公钥"""
        try:
            if "-----BEGIN" in key_str:
                return serialization.load_pem_public_key(key_str.encode(), backend=default_backend())
            else:
                try:
                    der_data = base64.b64decode(key_str)
                    return serialization.load_der_public_key(der_data, backend=default_backend())
                except:
                    hex_str = re.sub(r'\s+', '', key_str)
                    if len(hex_str) % 2 != 0:
                        hex_str = '0' + hex_str
                    der_data = bytes.fromhex(hex_str)
                    return serialization.load_der_public_key(der_data, backend=default_backend())
        except Exception as e:
            self.logger.error(f"加载公钥失败: {str(e)}")
            return None
    
    def rsa_encrypt_long(self, text, public_key_str):
        """RSA加密长文本"""
        try:
            public_key = self.load_public_key(public_key_str)
            if not public_key:
                return None
            
            key_size = public_key.key_size // 8
            max_block_size = key_size - 11
            
            encrypted_blocks = []
            for i in range(0, len(text), max_block_size):
                block = text[i:i + max_block_size]
                encrypted_block = public_key.encrypt(
                    block.encode('utf-8'),
                    padding.PKCS1v15()
                )
                encrypted_blocks.append(encrypted_block)
            
            encrypted_data = b''.join(encrypted_blocks)
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"RSA加密失败: {str(e)}")
            return None
    
    def login(self, account, password, captcha, token):
        """登录"""
        url = "https://cmsapi3.qiucheng-wangluo.com/cms-api/login"
        
        # 双重加密
        first_encrypted_password = self.rsa_encrypt_long(password, self.first_public_key)
        if not first_encrypted_password:
            return None
        
        second_encrypted_password = self.rsa_encrypt_long(first_encrypted_password, token)
        if not second_encrypted_password:
            return None
        
        encrypted_account = self.rsa_encrypt_long(account, token)
        if not encrypted_account:
            return None
        
        data = {
            "account": encrypted_account,
            "data": second_encrypted_password,
            "safeCode": captcha,
            "token": token,
            "locale": "zh"
        }
        
        try:
            response = self.session.post(url, headers=self.headers, data=data)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"登录请求失败: {str(e)}")
            return None
    
    def login_account(self, account_id):
        """登录指定账号"""
        account = Account.query.get(account_id)
        if not account:
            return False, "账号不存在"
        
        self.save_log(account_id, "INFO", f"开始为账号 [{account.name}] 执行自动登录流程...")
        
        for attempt in range(1, self.max_attempts + 1):
            self.save_log(account_id, "INFO", f"尝试第 {attempt} 次登录 [{account.name}]...")
            
            # 获取token
            token = self.get_token()
            if not token:
                self.save_log(account_id, "ERROR", "获取token失败，等待重试...")
                time.sleep(2)
                continue
            
            self.save_log(account_id, "INFO", f"获取token成功: {token[:20]}...")
            
            # 获取验证码
            captcha_base64 = self.get_captcha(token)
            if not captcha_base64:
                self.save_log(account_id, "ERROR", "获取验证码失败，等待重试...")
                time.sleep(2)
                continue
            
            self.save_log(account_id, "INFO", "获取验证码成功")
            
            # 识别验证码
            captcha_text = self.recognize_captcha(captcha_base64)
            if not captcha_text or len(captcha_text) != 4:
                self.save_log(account_id, "ERROR", f"验证码识别失败或格式不正确: {captcha_text}，等待重试...")
                time.sleep(2)
                continue
            
            self.save_log(account_id, "INFO", f"识别验证码结果: {captcha_text}")
            
            # 登录
            login_result = self.login(account.email, account.password, captcha_text, token)
            
            if login_result:
                self.save_log(account_id, "INFO", f"登录结果: {json.dumps(login_result, ensure_ascii=False, indent=2)}")
                
                if login_result.get("iErrCode") == 0:
                    self.save_log(account_id, "INFO", "登录成功!", is_success=True)
                    self.save_log(account_id, "ERROR", "登录成功!", is_success=True)  # 同时记录到错误级别
                    
                    # 获取俱乐部列表
                    club_info = self.get_club_list(token, account.name)
                    if club_info:
                        self.save_log(account_id, "INFO", "获取俱乐部列表成功")
                    else:
                        self.save_log(account_id, "ERROR", "获取俱乐部列表失败")
                    
                    return True, "登录成功"
                else:
                    error_msg = login_result.get("sErrMsg", "未知错误")
                    self.save_log(account_id, "ERROR", f"登录失败: {error_msg}")
                    
                    if "验证码" in error_msg:
                        self.save_log(account_id, "INFO", "验证码错误，立即重试...")
                        time.sleep(1)
                        continue
            else:
                self.save_log(account_id, "ERROR", "登录请求失败")
            
            if attempt < self.max_attempts:
                wait_time = 2 ** attempt
                self.save_log(account_id, "INFO", f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        self.save_log(account_id, "ERROR", f"已达到最大尝试次数 {self.max_attempts}，登录失败")
        return False, "登录失败"
    
    def get_club_list(self, token, account_name="未知账号"):
        """获取俱乐部列表"""
        url = "https://cmsapi3.qiucheng-wangluo.com/cms-api/club/getClubList"
        
        headers = {
            "accept": "application/json, text/javascript",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "token": token,
            "referrer": "https://cms.ayybyyy.com/"
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("iErrCode") == 0:
                    club_data = result.get("result")
                    if isinstance(club_data, list) and len(club_data) > 0:
                        club_info = club_data[0]
                        club_id = club_info.get("lClubID")
                        club_name = club_info.get("sClubName")
                        create_user = club_info.get("lCreateUser")
                        credit_league_id = club_info.get("iCreditLeagueId")
                        
                        self.logger.info(f"[{account_name}] 俱乐部信息: lClubID={club_id}, sClubName={club_name}, lCreateUser={create_user}, iCreditLeagueId={credit_league_id}")
                        return club_info
                    elif isinstance(club_data, dict):
                        return club_data
            return None
        except Exception as e:
            self.logger.error(f"获取俱乐部列表失败: {str(e)}")
            return None