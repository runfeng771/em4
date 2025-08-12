# 自动登录管理系统

一个基于Flask的可爱风格自动登录管理系统，支持多账号管理、定时任务、日志记录和邮件通知功能。

## ✨ 功能特点

- 🎨 **圆润可爱UI设计** - 采用毛玻璃效果和渐变色彩，界面美观友好
- 📧 **多账号管理** - 支持添加、编辑、删除多个登录账号
- ⏰ **灵活定时任务** - 可为每个账号设置不同的定时登录间隔
- 📊 **详细日志记录** - 按日期分页显示登录日志，支持筛选和清空
- 📬 **智能邮件通知** - 登录成功后自动发送邮件通知，支持自定义收件人
- 🔄 **实时状态监控** - 查看账号状态、定时任务运行情况
- 💡 **友好交互体验** - 所有操作都有飘窗提示，无需刷新页面

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd auto-login-web
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. **运行应用**
```bash
python app.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:5000`

## 📦 部署到Render

### 1. 准备代码

确保您的代码已经推送到GitHub仓库。

### 2. 创建Render服务

1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New +" → "Web Service"
3. 选择您的GitHub仓库
4. 配置服务：

**Runtime Environment:**
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

**Environment Variables:**
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///auto_login.db
FLASK_ENV=production
```

### 3. 配置数据库（可选）

如果需要使用PostgreSQL数据库，可以添加以下环境变量：
```
DATABASE_URL=postgresql://username:password@host:port/database
```

### 4. 部署

点击 "Create Web Service" 开始部署。Render会自动构建和部署您的应用。

## 🛠️ 配置说明

### 邮件配置

系统支持自定义邮件配置，您可以在界面的"邮件配置"中设置：

- **SMTP服务器**: 邮件服务器地址（如：smtp.email.cn）
- **SMTP端口**: 邮件服务器端口（如：465）
- **发件人邮箱**: 发送通知邮件的邮箱地址
- **发件人密码**: 邮箱密码或应用专用密码
- **默认收件人**: 默认接收通知邮件的邮箱地址

### 账号配置

每个账号可以独立配置：

- **账号名称**: 显示名称
- **邮箱/账号**: 登录账号
- **密码**: 登录密码
- **邮件通知**: 是否启用登录成功邮件通知
- **自定义邮箱**: 可设置该账号专用的通知邮箱
- **定时任务**: 设置自动登录的间隔时间（分钟）

## 📁 项目结构

```
auto-login-web/
├── app.py                 # Flask主应用
├── config.py              # 配置文件
├── models.py              # 数据库模型
├── requirements.txt       # 依赖包列表
├── services/              # 业务逻辑
│   ├── __init__.py
│   ├── login_service.py   # 登录服务
│   ├── email_service.py   # 邮件服务
│   └── scheduler_service.py # 定时任务服务
├── static/                # 静态文件
│   ├── css/
│   ├── js/
│   └── img/
├── templates/             # HTML模板
│   ├── base.html
│   ├── index.html
│   └── components/
├── logs/                  # 日志文件目录
├── migrations/            # 数据库迁移文件
└── auto_login.db          # SQLite数据库文件
```

## 🔧 API接口

### 账号管理
- `GET /api/accounts` - 获取所有账号
- `POST /api/accounts` - 添加账号
- `PUT /api/accounts/<id>` - 更新账号
- `DELETE /api/accounts/<id>` - 删除账号
- `POST /api/accounts/<id>/login` - 手动登录

### 定时任务
- `POST /api/accounts/<id>/schedule` - 添加定时任务
- `DELETE /api/accounts/<id>/schedule` - 移除定时任务
- `POST /api/accounts/<id>/schedule/toggle` - 切换任务状态

### 日志管理
- `GET /api/logs` - 获取日志
- `POST /api/logs/clear` - 清空日志

### 邮件服务
- `GET /api/email/config` - 获取邮件配置
- `POST /api/email/config` - 更新邮件配置
- `POST /api/email/test` - 测试邮件发送
- `POST /api/email/send-daily-log` - 发送每日日志

### 系统状态
- `GET /api/scheduler/status` - 获取调度器状态

## 🎨 UI设计特色

- **毛玻璃效果**: 使用backdrop-filter实现现代化的毛玻璃背景
- **渐变色彩**: 采用紫色渐变主题，营造科技感
- **圆润设计**: 所有元素都采用圆角设计，界面友好
- **动画效果**: 按钮悬停、卡片浮动等微交互动画
- **响应式布局**: 适配各种屏幕尺寸

## 📝 注意事项

1. **安全性**: 请妥善保管您的邮箱密码，建议使用应用专用密码
2. **定时任务**: 系统会在后台自动运行定时任务，请确保服务持续运行
3. **日志管理**: 建议定期清理日志文件，避免占用过多存储空间
4. **邮件发送**: 请确保邮件服务器配置正确，避免通知发送失败

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License

## 🌟 Star History

如果这个项目对您有帮助，请给个Star支持一下！