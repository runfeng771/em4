# 部署指南

## 本地部署

### 方法一：使用启动脚本（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd auto-login-web

# 运行启动脚本
./start.sh
```

启动脚本会自动：
- 创建虚拟环境
- 安装所有依赖
- 初始化数据库
- 启动应用

### 方法二：手动部署

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
export FLASK_APP=app.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 4. 创建日志目录
mkdir -p logs

# 5. 启动应用
python app.py
```

访问 `http://localhost:5000` 即可使用系统。

## Render部署

### 1. 准备GitHub仓库

确保您的代码已推送到GitHub仓库：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. 配置Render服务

1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New +" → "Web Service"
3. 选择 "Build and deploy from a Git repository"
4. 选择您的GitHub仓库并授权
5. 配置服务参数：

**Basic Information**
- **Name**: auto-login-web (或您喜欢的名称)
- **Region**: 选择离您最近的区域
- **Branch**: main

**Runtime**
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

**Environment Variables** (点击 "Add Environment Variable")
```
Key: SECRET_KEY
Value: your-super-secret-key-here

Key: FLASK_ENV
Value: production
```

### 3. 高级配置（可选）

#### 使用PostgreSQL数据库

1. 在Render Dashboard中创建PostgreSQL数据库
2. 获取数据库连接字符串
3. 添加环境变量：
```
Key: DATABASE_URL
Value: postgresql://user:password@host:port/database
```

#### 自定义域名

1. 在服务设置中添加自定义域名
2. 按照提示配置DNS记录

### 4. 部署

点击 "Create Web Service" 开始部署。Render会自动：
- 克隆您的代码
- 安装依赖
- 构建应用
- 启动服务

部署完成后，您可以通过Render提供的URL访问应用。

## 其他云平台部署

### Heroku部署

1. 安装Heroku CLI
2. 登录Heroku：`heroku login`
3. 创建应用：`heroku create`
4. 添加构建包：
```bash
heroku buildpacks:add heroku/python
```
5. 设置环境变量：
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
```
6. 部署：
```bash
git push heroku main
```

### Vercel部署

1. 安装Vercel CLI：`npm i -g vercel`
2. 登录：`vercel login`
3. 部署：`vercel`

## 环境变量说明

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `SECRET_KEY` | Flask密钥 | dev-secret-key | 是 |
| `DATABASE_URL` | 数据库连接字符串 | sqlite:///auto_login.db | 否 |
| `FLASK_ENV` | 运行环境 | development | 否 |
| `MAIL_SERVER` | SMTP服务器 | smtp.email.cn | 否 |
| `MAIL_PORT` | SMTP端口 | 465 | 否 |
| `MAIL_USERNAME` | 邮箱用户名 | 18@HH.email.cn | 否 |
| `MAIL_PASSWORD` | 邮箱密码 | yuHKfnKvCqmw6HNN | 否 |
| `DEFAULT_RECEIVER_EMAIL` | 默认收件人 | Steven@HH.email.cn | 否 |

## 故障排除

### 常见问题

1. **数据库迁移失败**
   ```bash
   # 删除迁移文件夹重新初始化
   rm -rf migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

2. **依赖安装失败**
   ```bash
   # 更新pip
   pip install --upgrade pip
   
   # 清理缓存
   pip cache purge
   
   # 重新安装
   pip install -r requirements.txt
   ```

3. **邮件发送失败**
   - 检查SMTP服务器配置
   - 确认邮箱密码正确
   - 某些邮箱需要使用应用专用密码

4. **定时任务不执行**
   - 确保服务持续运行
   - 检查账号是否启用
   - 查看日志排查错误

### 日志查看

- **本地部署**：查看控制台输出和 `logs/` 目录下的文件
- **Render部署**：在Dashboard中查看Logs
- **其他平台**：查看平台提供的日志服务

## 性能优化

1. **数据库优化**
   - 生产环境建议使用PostgreSQL
   - 定期清理过期日志
   - 添加适当的索引

2. **缓存优化**
   - 启用Redis缓存（可选）
   - 缓存频繁访问的数据

3. **监控优化**
   - 添加健康检查接口
   - 监控系统资源使用情况
   - 设置错误告警

## 安全建议

1. **更改默认密码**
   - 修改默认邮箱密码
   - 使用强密码作为SECRET_KEY

2. **HTTPS配置**
   - 生产环境必须使用HTTPS
   - 配置SSL证书

3. **访问控制**
   - 添加身份验证
   - 限制管理接口访问

4. **数据保护**
   - 定期备份数据库
   - 加密敏感信息

## 维护指南

1. **定期更新**
   - 更新依赖包到最新版本
   - 关注安全漏洞

2. **日志管理**
   - 定期清理日志文件
   - 设置日志轮转

3. **备份策略**
   - 定期备份数据库
   - 保存配置文件

4. **监控告警**
   - 设置服务监控
   - 配置错误告警