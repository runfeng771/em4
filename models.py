from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Account(db.Model):
    """账号模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='账号名称')
    email = db.Column(db.String(200), nullable=False, comment='邮箱/账号')
    password = db.Column(db.String(200), nullable=False, comment='密码')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    email_notification = db.Column(db.Boolean, default=True, comment='是否启用邮件通知')
    custom_email = db.Column(db.String(200), nullable=True, comment='自定义接收邮箱')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联的定时任务
    schedules = db.relationship('Schedule', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'is_active': self.is_active,
            'email_notification': self.email_notification,
            'custom_email': self.custom_email,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Schedule(db.Model):
    """定时任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, comment='任务名称')
    interval_minutes = db.Column(db.Integer, nullable=False, comment='间隔分钟数')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    next_run_time = db.Column(db.DateTime, nullable=True, comment='下次运行时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'name': self.name,
            'interval_minutes': self.interval_minutes,
            'is_active': self.is_active,
            'next_run_time': self.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if self.next_run_time else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class LoginLog(db.Model):
    """登录日志模型"""
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False, comment='日志级别')
    message = db.Column(db.Text, nullable=False, comment='日志消息')
    details = db.Column(db.Text, nullable=True, comment='详细信息JSON')
    is_success = db.Column(db.Boolean, default=False, comment='是否成功')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关联账号
    account = db.relationship('Account', backref=db.backref('login_logs', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'account_name': self.account.name if self.account else '未知账号',
            'level': self.level,
            'message': self.message,
            'details': json.loads(self.details) if self.details else None,
            'is_success': self.is_success,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class EmailConfig(db.Model):
    """邮件配置模型"""
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(200), nullable=False, comment='SMTP服务器')
    smtp_port = db.Column(db.Integer, nullable=False, comment='SMTP端口')
    sender_email = db.Column(db.String(200), nullable=False, comment='发件人邮箱')
    sender_password = db.Column(db.String(200), nullable=False, comment='发件人密码')
    default_receiver = db.Column(db.String(200), nullable=False, comment='默认收件人')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'sender_email': self.sender_email,
            'sender_password': self.sender_password,
            'default_receiver': self.default_receiver,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }