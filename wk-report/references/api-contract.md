# 开发四部周报接口契约

## 地址

- 生产 API 基址：`https://gw-ai-bot.online`
- 本地 API 基址：`http://localhost:8000`
- 后端上下文路径：`/api/dev4`
- 认证请求头：`satoken`

脚本同时接受包含 `/api/dev4` 的 API 基址，避免重复拼接上下文路径。

## 登录

调用 `POST /api/dev4/v1/auth/login`：

```json
{
  "username": "用户名",
  "password": "密码",
  "rememberMe": false
}
```

成功响应使用统一包装体：

```json
{
  "success": true,
  "msg": "请求成功",
  "detail": null,
  "data": {
    "accessToken": "Sa-Token 值",
    "refreshToken": "兼容字段",
    "expiresIn": 7200,
    "mustChangePassword": false
  }
}
```

登录会执行系统既有业务逻辑：确保当前周周报草稿存在，并触发上周计划自动导入。因此，在线模式必须获得用户明确授权，不能把登录描述为完全只读。

若 `mustChangePassword` 为 `true`，停止导出并提示用户先在系统页面完成首次改密。

## 团队周报导出

调用 `GET /api/dev4/v1/weekly-reports/team/export`，请求头携带登录返回的 `accessToken`：

```text
satoken: <accessToken>
```

可选查询参数：

- `week_date=YYYY-MM-DD`：目标自然周内任意一天；不传表示服务端当前周。

成功响应为 UTF-8 Markdown 附件，文件名通常为 `<weekCode>-weekly-meeting.md`。调用账号必须拥有 `weekly.team` 菜单权限。

## 退出

导出完成后调用 `POST /api/dev4/v1/auth/logout`，请求头继续携带 `satoken`。脚本默认尽力退出，即使导出失败也不保留令牌。

## 错误处理

- `401` / `INVALID_PASSWORD`：提示账号或密码错误，不区分账号是否存在。
- `403` / `FORBIDDEN`：提示账号停用或无团队周报权限。
- `PASSWORD_CHANGE_REQUIRED`：提示先完成首次改密。
- 网络、网关或非标准响应：保留原始登录态判断，不猜测业务结果，不重复提交登录请求。

## 凭据规则

- 不把密码写入 `SKILL.md`、脚本参数、生成文件、日志或聊天回复。
- 优先通过 `WK_REPORT_PASSWORD` 环境变量或 `getpass` 隐藏输入提供密码。
- 可通过 `WK_REPORT_USERNAME` 和 `WK_REPORT_API_BASE` 提供账号与 API 基址。
- 不打印、缓存或持久化 `accessToken`。
