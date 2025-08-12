import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///auto_login.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.email.cn'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '18@HH.email.cn'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'yuHKfnKvCqmw6HNN'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or '18@HH.email.cn'
    
    # 默认接收邮箱
    DEFAULT_RECEIVER_EMAIL = os.environ.get('DEFAULT_RECEIVER_EMAIL') or 'Steven@HH.email.cn'
    
    # 日志配置
    LOG_DIR = os.environ.get('LOG_DIR') or 'logs'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # 定时任务配置
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'