from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import json
from config import Config
from models import db, Account, Schedule, LoginLog, EmailConfig
from services.login_service import LoginService
from services.email_service import EmailService
from services.scheduler_service import SchedulerService

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)
migrate = Migrate(app, db)

# 初始化服务
login_service = LoginService()
email_service = EmailService()
scheduler_service = SchedulerService(app)

# 创建数据库表
with app.app_context():
    db.create_all()
    
    # 初始化默认账号
    if Account.query.count() == 0:
        default_account = Account(
            name="tbh2356@126.com",
            email="tbh2356@126.com",
            password="112233qq",
            is_active=True,
            email_notification=True
        )
        db.session.add(default_account)
        db.session.commit()
    
    # 初始化邮件配置
    if EmailConfig.query.count() == 0:
        default_email_config = EmailConfig(
            smtp_server="smtp.email.cn",
            smtp_port=465,
            sender_email="18@HH.email.cn",
            sender_password="yuHKfnKvCqmw6HNN",
            default_receiver="Steven@HH.email.cn",
            is_active=True
        )
        db.session.add(default_email_config)
        db.session.commit()

@app.route('/')
def index():
    """首页"""
    accounts = Account.query.all()
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', accounts=accounts, today=today)

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """获取所有账号"""
    accounts = Account.query.all()
    accounts_data = []
    
    for account in accounts:
        account_dict = account.to_dict()
        # 获取任务状态
        job_status = scheduler_service.get_account_job_status(account.id)
        account_dict['schedule_status'] = job_status
        
        # 获取今日登录次数
        today = datetime.now().strftime('%Y-%m-%d')
        today_logs = LoginLog.query.filter(
            LoginLog.account_id == account.id,
            LoginLog.created_at >= f"{today} 00:00:00",
            LoginLog.created_at <= f"{today} 23:59:59"
        ).count()
        account_dict['today_logins'] = today_logs
        
        accounts_data.append(account_dict)
    
    return jsonify({'success': True, 'data': accounts_data})

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """添加账号"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} 不能为空'}), 400
        
        # 创建新账号
        new_account = Account(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            is_active=data.get('is_active', True),
            email_notification=data.get('email_notification', True),
            custom_email=data.get('custom_email')
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        # 如果设置了定时任务，添加定时任务
        if data.get('schedule_minutes'):
            scheduler_service.add_account_schedule(
                new_account.id, 
                data['schedule_minutes'],
                data.get('schedule_name')
            )
        
        return jsonify({
            'success': True, 
            'message': '账号添加成功',
            'data': new_account.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'添加账号失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """更新账号"""
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        data = request.get_json()
        
        # 更新账号信息
        account.name = data.get('name', account.name)
        account.email = data.get('email', account.email)
        account.password = data.get('password', account.password)
        account.is_active = data.get('is_active', account.is_active)
        account.email_notification = data.get('email_notification', account.email_notification)
        account.custom_email = data.get('custom_email', account.custom_email)
        account.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 更新定时任务
        if data.get('schedule_minutes'):
            scheduler_service.add_account_schedule(
                account_id, 
                data['schedule_minutes'],
                data.get('schedule_name')
            )
        elif data.get('remove_schedule'):
            scheduler_service.remove_account_schedule(account_id)
        
        return jsonify({
            'success': True, 
            'message': '账号更新成功',
            'data': account.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新账号失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """删除账号"""
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        # 删除定时任务
        scheduler_service.remove_account_schedule(account_id)
        
        # 删除账号
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '账号删除成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除账号失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>/login', methods=['POST'])
def login_account(account_id):
    """手动登录账号"""
    try:
        success, message = scheduler_service.execute_login_now(account_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>/schedule', methods=['POST'])
def add_schedule(account_id):
    """添加定时任务"""
    try:
        data = request.get_json()
        interval_minutes = data.get('interval_minutes')
        schedule_name = data.get('schedule_name')
        
        if not interval_minutes:
            return jsonify({'success': False, 'message': '间隔时间不能为空'}), 400
        
        success, message = scheduler_service.add_account_schedule(
            account_id, 
            interval_minutes, 
            schedule_name
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加定时任务失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>/schedule', methods=['DELETE'])
def remove_schedule(account_id):
    """移除定时任务"""
    try:
        success, message = scheduler_service.remove_account_schedule(account_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'移除定时任务失败: {str(e)}'}), 500

@app.route('/api/accounts/<int:account_id>/schedule/toggle', methods=['POST'])
def toggle_schedule(account_id):
    """切换定时任务状态"""
    try:
        success, message = scheduler_service.toggle_account_schedule(account_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'切换定时任务状态失败: {str(e)}'}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取日志"""
    try:
        # 获取查询参数
        account_id = request.args.get('account_id', type=int)
        date = request.args.get('date')
        level = request.args.get('level')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 构建查询
        query = LoginLog.query
        
        if account_id:
            query = query.filter(LoginLog.account_id == account_id)
        
        if date:
            start_date = f"{date} 00:00:00"
            end_date = f"{date} 23:59:59"
            query = query.filter(LoginLog.created_at >= start_date, LoginLog.created_at <= end_date)
        
        if level:
            query = query.filter(LoginLog.level == level.upper())
        
        # 排序和分页
        query = query.order_by(LoginLog.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建返回数据
        logs_data = []
        for log in pagination.items:
            logs_data.append(log.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日志失败: {str(e)}'}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """清空日志"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        date = data.get('date')
        
        # 构建删除查询
        query = LoginLog.query
        
        if account_id:
            query = query.filter(LoginLog.account_id == account_id)
        
        if date:
            start_date = f"{date} 00:00:00"
            end_date = f"{date} 23:59:59"
            query = query.filter(LoginLog.created_at >= start_date, LoginLog.created_at <= end_date)
        
        # 执行删除
        deleted_count = query.count()
        query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'已删除 {deleted_count} 条日志'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'清空日志失败: {str(e)}'}), 500

@app.route('/api/email/config', methods=['GET'])
def get_email_config():
    """获取邮件配置"""
    try:
        config = email_service.get_email_config()
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取邮件配置失败: {str(e)}'}), 500

@app.route('/api/email/config', methods=['POST'])
def update_email_config():
    """更新邮件配置"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'default_receiver']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} 不能为空'}), 400
        
        success, message = email_service.save_email_config(data)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新邮件配置失败: {str(e)}'}), 500

@app.route('/api/email/test', methods=['POST'])
def test_email():
    """测试邮件发送"""
    try:
        data = request.get_json()
        test_email = data.get('test_email')
        
        if not test_email:
            return jsonify({'success': False, 'message': '测试邮箱不能为空'}), 400
        
        success, message = email_service.send_email(
            test_email,
            "自动登录系统测试邮件",
            "这是一封来自自动登录系统的测试邮件，如果您收到此邮件，说明邮件配置正确。"
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'测试邮件发送失败: {str(e)}'}), 500

@app.route('/api/email/send-daily-log', methods=['POST'])
def send_daily_log():
    """发送每日日志邮件"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        success, message = email_service.send_daily_log_email(account_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送每日日志邮件失败: {str(e)}'}), 500

@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """获取调度器状态"""
    try:
        jobs = scheduler_service.get_all_jobs()
        return jsonify({'success': True, 'data': jobs})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取调度器状态失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
