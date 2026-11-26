# 运营插件

每个插件位于 `plugins/<插件名>/`，维护各自的 `plugin.yaml`、使用说明和测试。带桌面界面的插件将入口放在自己的 `desktop/plugin.js`。

| 插件 | 用途 |
| --- | --- |
| [封面设计](plugins/cover-designer/README.md) | 由 Agent 为稿件选择封面风格、生成候选并依据实图评审修订 |

## 安装封面设计

在 Hermes 桌面端打开「扩展工具 → 插件 → 从 Git 安装」，输入以下地址，勾选智能体插件和桌面 UI，再安装并启用。

```text
https://github.com/jihuisoftware/operation-plugins.git#plugins/cover-designer
```

本地开发可使用 `file:///绝对路径/operation-plugins#plugins/cover-designer`，安装器读取 Git 已提交的版本。

## 添加其他插件

在 `plugins/` 下为新插件建立同名目录，放入其清单、代码和 README，并更新上表。安装地址的 `#` 后填写该插件相对于仓库根目录的路径。
