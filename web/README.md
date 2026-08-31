# 对抗评审 Web 界面

这是 `ai-test-case-orchestrator` 的第一阶段人工评审页面，使用 Flask/Jinja2 服务端渲染，Vue 3 增强表单交互。

## 本地运行

在仓库根目录执行：

```powershell
py -m pip install -r requirements.txt
py -m web.app
```

打开 <http://127.0.0.1:5000/reviews/challenge>。

页面提交后，后端先写入 `web/runtime/cases/<case-id>/02-review.md`，再调用测试点生成脚本。`CASE_ROOT`、`TEST_POINT_SCRIPT` 和 `VUE_SCRIPT_URL` 可通过 Flask 配置或环境变量适配宿主环境。

## 宿主桥接

宿主可在页面加载前注入 `window.__TEST_REVIEW_BRIDGE__`，实现同样的 `submit(payload)` 方法。页面会等待返回的 `accepted`、`persisted_artifact` 和 `next_stage`，不会仅依据按钮点击显示成功。
