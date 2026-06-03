# 如月风铃的skills
[en](README_en.md) | [zh](README.md) | [ja](README_ja.md)
## 简介
这是我在玩claude code时候撰写的一些skill文档，用于解决我在大学生活中遇到的方方面面的问题

我的电脑系统是arch linux， 可能和你的不太一样， 如果能够帮到您的话就太好了

## 安装
没有什么花里胡哨的操作，把整个仓库克隆下来，丢进claude code的skills文件夹

当然你也可以选择丢进项目的skills文件夹

---

## 文档处理类

- `pdf-math-convert`：将数学密集型PDF（讲义、教材、论文）转为Markdown文本，支持LaTeX数学公式提取和图片处理
  > 特色：1. 自动识别并修复公式占位符 2. LaTeX数学公式包裹 3. Base64嵌入或引用模式 4. 支持批量并行处理

- `markdown-translate`：用LLM翻译Markdown文本，保留LaTeX数学公式、代码块、图片和所有格式
  > 特色：1. 保护数学公式/代码/图片不被翻译 2. 支持批量并行翻译 3. 翻译后自动校验完整性 4. 支持大文件分块翻译

- `ocr-md-polish`：修复OCR生成的Markdown文件中的公式渲染问题（下标、指数分组、嵌套定界符），清理图片附近OCR重复文本
  > 特色：1. 修复缺失的下标（x0 → x_0） 2. 修复指数分组（e^x arctan(x) → e^{x \arctan(x)}） 3. 合并嵌套的$...$数学模式 4. 支持tesseract OCR验证去重

## 编程辅助类

- `find-docs`：使用Context7 CLI检索最新的开发技术文档、API参考和代码示例
  > 特色：1. 比训练数据更新、更准确 2. 支持版本特定查询 3. 支持主流框架/库/工具