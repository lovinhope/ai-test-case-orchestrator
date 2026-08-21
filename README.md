# ai-test-case-orchestrator

## 首次使用前：配置 Jira、Confluence 和 GitLab

本 Skill 需要通过 REST API 读取 Jira、Confluence 及 GitLab。首次使用前，请在本机创建用户级配置文件：

```text
C:\Users\<用户名>\.codex\lowrisk-jira.ini
```

配置格式如下。请使用真实凭证替换占位符，不要把 token 提交到 Git 或粘贴到聊天中：

```ini
[jira]
base_url = http://jira.lowrisk.com.cn
jira_token = <Jira API Token>

[confluence]
base_url = http://confluence.lowrisk.com.cn
token = <Confluence Token>

[gitlab]
base_url = http://git.lowrisk.com.cn
token = <GitLab Token>
```

然后在 PowerShell 中设置配置文件路径：

```powershell
[Environment]::SetEnvironmentVariable("TASKFLOW_CONFIG_PATH", "C:\Users\<用户名>\.codex\lowrisk-jira.ini", "User")
```

设置后请重启 Codex。每次使用本 Skill 时，若检测不到 `TASKFLOW_CONFIG_PATH` 或所需凭证，应先提醒用户完成上述一次性配置；不得要求用户在聊天中粘贴 token。

## 输入模式

- 产品需求、Jira 需求、业务规则：`requirement`
- OpenAPI/Swagger：`openapi`
- 源码、仓库、commit、diff：`source_code`
- 历史缺陷：`historical_defect`
- 脱敏行为统计：`business_profile`

## 统一流程

```text
输入
  -> 模式选择
  -> 业务知识、技术方案、相关代码三路关联
  -> 产品/代码对抗（单一模块）
  -> 人工评审
  -> 测试点、回归点分析
  -> 人工评审
  -> 历史测试用例关联
  -> 生成测试用例
  -> 人工评审
  -> 评估；总得分大于 60% 才通过
```

关联规则：

- 排除周报、QA 周计划、发布记录和状态跟踪页面。
- 新框架需求优先使用当前技术方案和已验证的新代码。
- 旧接口、旧权限判断和旧 SQL 只能作为兼容参考。
- 文档中的接口名、类名、表名只是代码线索；读取源码或 diff 后才能认定为代码证据。
- 中文人工评审材料不展示英文字段名、状态名或枚举值。

详细规则见 [SKILL.md](SKILL.md)。
