from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
from models import db, Account, Schedule
from .login_service import LoginService
from .email_service import EmailService

class SchedulerService:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.login_service = LoginService()
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化调度器"""
        self.app = app
        self.scheduler.configure(job_defaults={'max_instances': 3})
        
        # 启动调度器
        self.scheduler.start()
        
        # 添加每日日志邮件任务（每天23:59执行）
        self.add_daily_log_job()
        
        # 应用上下文结束时停止调度器
        @app.teardown_appcontext
        def shutdown_scheduler(exception=None):
            if exception:
                self.scheduler.shutdown()
    
    def add_account_schedule(self, account_id, interval_minutes, schedule_name=None):
        """添加账号定时任务"""
        try:
            account = Account.query.get(account_id)
            if not account:
                return False, "账号不存在"
            
            if not schedule_name:
                schedule_name = f"{account.name}_定时登录"
            
            # 停止该账号的现有任务
            self.remove_account_schedule(account_id)
            
            # 创建新的定时任务
            job_id = f"account_{account_id}_login"
            trigger = IntervalTrigger(minutes=interval_minutes)
            
            self.scheduler.add_job(
                func=self._execute_login_task,
                trigger=trigger,
                id=job_id,
                args=[account_id],
                name=schedule_name,
                replace_existing=True,
                max_instances=1
            )
            
            # 更新数据库中的任务信息
            schedule = Schedule.query.filter_by(account_id=account_id).first()
            if schedule:
                schedule.interval_minutes = interval_minutes
                schedule.name = schedule_name
                schedule.is_active = True
                schedule.next_run_time = self.scheduler.get_job(job_id).next_run_time
                schedule.updated_at = datetime.utcnow()
            else:
                new_schedule = Schedule(
                    account_id=account_id,
                    name=schedule_name,
                    interval_minutes=interval_minutes,
                    is_active=True,
                    next_run_time=self.scheduler.get_job(job_id).next_run_time
                )
                db.session.add(new_schedule)
            
            db.session.commit()
            
            return True, f"定时任务添加成功，每 {interval_minutes} 分钟执行一次"
            
        except Exception as e:
            db.session.rollback()
            return False, f"添加定时任务失败: {str(e)}"
    
    def remove_account_schedule(self, account_id):
        """移除账号定时任务"""
        try:
            job_id = f"account_{account_id}_login"
            
            # 停止任务
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 更新数据库中的任务状态
            schedule = Schedule.query.filter_by(account_id=account_id).first()
            if schedule:
                schedule.is_active = False
                schedule.next_run_time = None
                schedule.updated_at = datetime.utcnow()
                db.session.commit()
            
            return True, "定时任务已移除"
            
        except Exception as e:
            db.session.rollback()
            return False, f"移除定时任务失败: {str(e)}"
    
    def toggle_account_schedule(self, account_id):
        """切换账号定时任务状态"""
        try:
            job_id = f"account_{account_id}_login"
            job = self.scheduler.get_job(job_id)
            
            if job:
                # 任务存在，暂停任务
                self.scheduler.pause_job(job_id)
                
                # 更新数据库
                schedule = Schedule.query.filter_by(account_id=account_id).first()
                if schedule:
                    schedule.is_active = False
                    schedule.updated_at = datetime.utcnow()
                    db.session.commit()
                
                return True, "定时任务已暂停"
            else:
                # 任务不存在，重新添加
                schedule = Schedule.query.filter_by(account_id=account_id).first()
                if schedule and schedule.interval_minutes:
                    return self.add_account_schedule(account_id, schedule.interval_minutes, schedule.name)
                else:
                    return False, "未找到定时任务配置"
                    
        except Exception as e:
            db.session.rollback()
            return False, f"切换定时任务状态失败: {str(e)}"
    
    def execute_login_now(self, account_id):
        """立即执行登录任务"""
        try:
            success, message = self._execute_login_task(account_id)
            return success, message
        except Exception as e:
            return False, f"执行登录任务失败: {str(e)}"
    
    def _execute_login_task(self, account_id):
        """执行登录任务（内部方法）"""
        try:
            with self.app.app_context():
                account = Account.query.get(account_id)
                if not account:
                    return False, "账号不存在"
                
                if not account.is_active:
                    return False, "账号已禁用"
                
                # 执行登录
                success, message = self.login_service.login_account(account_id)
                
                # 如果登录成功且启用了邮件通知，发送邮件
                if success and account.email_notification:
                    email_service = EmailService()
                    email_service.send_login_success_email(account_id)
                
                return success, message
                
        except Exception as e:
            return False, f"执行登录任务时发生错误: {str(e)}"
    
    def add_daily_log_job(self):
        """添加每日日志邮件任务"""
        try:
            # 每天23:59执行
            self.scheduler.add_job(
                func=self._execute_daily_log_task,
                trigger=CronTrigger(hour=23, minute=59),
                id='daily_log_email',
                name='每日日志邮件',
                replace_existing=True,
                max_instances=1
            )
            
            return True, "每日日志邮件任务已添加"
            
        except Exception as e:
            return False, f"添加每日日志邮件任务失败: {str(e)}"
    
    def _execute_daily_log_task(self):
        """执行每日日志邮件任务（内部方法）"""
        try:
            with self.app.app_context():
                email_service = EmailService()
                success, message = email_service.send_daily_log_email()
                return success, message
        except Exception as e:
            return False, f"执行每日日志邮件任务时发生错误: {str(e)}"
    
    def get_all_jobs(self):
        """获取所有任务信息"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def get_account_job_status(self, account_id):
        """获取账号任务状态"""
        job_id = f"account_{account_id}_login"
        job = self.scheduler.get_job(job_id)
        
        if job:
            return {
                'active': True,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'name': job.name
            }
        else:
            return {
                'active': False,
                'next_run_time': None,
                'name': None
            }
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()