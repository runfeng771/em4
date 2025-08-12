import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
import json
import os
from models import db, Account, LoginLog, EmailConfig

class EmailService:
    def __init__(self):
        self.default_config = {
            "smtp_server": "smtp.email.cn",
            "smtp_port": 465,
            "sender_email": "18@HH.email.cn",
            "sender_password": "yuHKfnKvCqmw6HNN",
            "default_receiver": "Steven@HH.email.cn"
        }
    
    def get_email_config(self):
        """获取邮件配置"""
        config = EmailConfig.query.filter_by(is_active=True).first()
        if config:
            return config.to_dict()
        return self.default_config
    
    def send_email(self, to_email, subject, content, config=None):
        """发送邮件"""
        try:
            if not config:
                config = self.get_email_config()
            
            # 创建邮件内容
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = Header(config['sender_email'])
            message['To'] = Header(to_email)
            message['Subject'] = Header(subject, 'utf-8')
            
            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(
                config['smtp_server'],
                config['smtp_port']
            ) as server:
                server.login(
                    config['sender_email'],
                    config['sender_password']
                )
                server.sendmail(
                    config['sender_email'],
                    [to_email],
                    message.as_string()
                )
            
            return True, "邮件发送成功"
        except Exception as e:
            return False, f"发送邮件失败: {str(e)}"
    
    def send_login_success_email(self, account_id):
        """发送登录成功邮件"""
        try:
            account = Account.query.get(account_id)
            if not account:
                return False, "账号不存在"
            
            # 检查是否启用邮件通知
            if not account.email_notification:
                return True, "账号未启用邮件通知"
            
            # 获取接收邮箱
            receiver_email = account.custom_email if account.custom_email else self.get_email_config()['default_receiver']
            
            # 获取今天的登录日志
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = LoginLog.query.filter(
                LoginLog.account_id == account_id,
                LoginLog.created_at >= f"{today} 00:00:00",
                LoginLog.created_at <= f"{today} 23:59:59",
                LoginLog.is_success == True
            ).order_by(LoginLog.created_at.desc()).all()
            
            # 构建邮件内容
            subject = f"自动登录成功通知 - {account.name} - {today}"
            
            content = f"""
账号: {account.name}
邮箱: {account.email}
登录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
登录状态: 成功

今日登录详情:
"""
            
            for log in today_logs:
                content += f"[{log.created_at.strftime('%H:%M:%S')}] {log.message}\n"
            
            content += f"""
---
此邮件由自动登录系统发送
"""
            
            # 发送邮件
            success, message = self.send_email(receiver_email, subject, content)
            
            if success:
                # 记录邮件发送日志
                login_service = LoginService()
                login_service.save_log(
                    account_id, 
                    "INFO", 
                    f"登录成功邮件已发送到 {receiver_email}"
                )
            
            return success, message
            
        except Exception as e:
            return False, f"发送登录成功邮件失败: {str(e)}"
    
    def send_daily_log_email(self, account_id=None):
        """发送每日日志邮件"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if account_id:
                # 发送指定账号的日志
                accounts = [Account.query.get(account_id)]
                if not accounts[0]:
                    return False, "账号不存在"
            else:
                # 发送所有启用邮件通知的账号日志
                accounts = Account.query.filter_by(email_notification=True, is_active=True).all()
            
            config = self.get_email_config()
            sent_count = 0
            
            for account in accounts:
                if not account.email_notification:
                    continue
                
                # 获取今天的所有日志
                today_logs = LoginLog.query.filter(
                    LoginLog.account_id == account.id,
                    LoginLog.created_at >= f"{today} 00:00:00",
                    LoginLog.created_at <= f"{today} 23:59:59"
                ).order_by(LoginLog.created_at.desc()).all()
                
                if not today_logs:
                    continue
                
                # 获取接收邮箱
                receiver_email = account.custom_email if account.custom_email else config['default_receiver']
                
                # 构建邮件内容
                subject = f"自动登录日志 - {account.name} - {today}"
                
                content = f"""
账号: {account.name}
邮箱: {account.email}
日期: {today}

今日登录日志:
"""
                
                for log in today_logs:
                    level_icon = "✅" if log.is_success else "❌"
                    content += f"{level_icon} [{log.created_at.strftime('%H:%M:%S')}] [{log.level}] {log.message}\n"
                
                # 统计信息
                total_logs = len(today_logs)
                success_logs = len([log for log in today_logs if log.is_success])
                content += f"""
---
统计信息:
总日志数: {total_logs}
成功次数: {success_logs}
失败次数: {total_logs - success_logs}

此邮件由自动登录系统发送
"""
                
                # 发送邮件
                success, message = self.send_email(receiver_email, subject, content)
                if success:
                    sent_count += 1
                    
                    # 记录邮件发送日志
                    login_service = LoginService()
                    login_service.save_log(
                        account.id, 
                        "INFO", 
                        f"每日日志邮件已发送到 {receiver_email}"
                    )
            
            return True, f"已发送 {sent_count} 封日志邮件"
            
        except Exception as e:
            return False, f"发送每日日志邮件失败: {str(e)}"
    
    def save_email_config(self, config_data):
        """保存邮件配置"""
        try:
            # 检查是否已存在配置
            existing_config = EmailConfig.query.first()
            
            if existing_config:
                # 更新现有配置
                for key, value in config_data.items():
                    if hasattr(existing_config, key):
                        setattr(existing_config, key, value)
                existing_config.updated_at = datetime.utcnow()
            else:
                # 创建新配置
                new_config = EmailConfig(**config_data)
                db.session.add(new_config)
            
            db.session.commit()
            return True, "邮件配置保存成功"
        except Exception as e:
            db.session.rollback()
            return False, f"保存邮件配置失败: {str(e)}"