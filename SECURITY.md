# Security Policy

如果你发现了安全问题，请不要把敏感细节直接公开发到 Issue。

建议通过以下方式处理：

- 先用最小化描述联系维护者
- 避免在公开页面贴出真实 Token、API Key、NAS 地址、用户名和密码
- 如果问题已经导致凭据泄露，请先轮换相关凭据，再补充复现信息

## 不应公开提交的内容

- `.env`
- Plex Token
- TMDB / OpenSubtitles API Key
- NASTool Webhook Token
- NAS 用户名、密码、共享路径中的真实私有信息

## 报告时建议附带

- 影响范围
- 复现步骤
- 触发条件
- 是否需要认证
- 日志中已做脱敏的关键片段
