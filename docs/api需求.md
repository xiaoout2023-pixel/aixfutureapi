这里是我展示的一个API，我需要你完善

<br />

{
"model\_id": "唯一标识（string，用于系统主键，比如 gpt-4.1）",
"model\_name": "模型名称（string，用于前端展示，比如 GPT-4.1）",
"provider": "厂商名称（string，比如 OpenAI / Anthropic / Google）",
"release\_date": "发布时间（YYYY-MM-DD，用于判断模型新旧，例如 2024-06-13）",
"status": "状态（string：active=可用 / beta=测试中 / deprecated=已废弃）",

"capabilities": {
"text\_generation": "是否支持文本生成（true/false，用于聊天、写作）",
"code\_generation": "是否支持代码生成（true/false，用于编程能力）",
"vision": "是否支持图像理解（true/false，用于看图/OCR）",
"audio": "是否支持音频能力（true/false，如语音输入输出）",
"multimodal": "是否支持多模态（true/false，文本+图像+音频）",
"tool\_calling": "是否支持工具调用（true/false，用于Agent调用API）",
"context\_length": "最大上下文长度（数字，单位token，例如128000）",
"reasoning\_level": "推理能力等级（low / medium / high）"
},

"pricing": {
"input\_price\_per\_1m\_tokens": "输入token价格（每100万token费用，例如5=5美元）",
"output\_price\_per\_1m\_tokens": "输出token价格（生成内容费用，通常更贵）",
"currency": "计价货币（默认USD）"
},

"scores": {
"reasoning\_score": "推理能力评分（0-100，越高越强）",
"coding\_score": "编程能力评分（0-100）",
"speed\_score": "响应速度评分（0-100，越高越快）",
"cost\_efficiency\_score": "性价比评分（能力/价格综合）",
"overall\_score": "综合评分（用于排序推荐）"
},

"tags": "模型标签数组（用于筛选，如 reasoning / fast / cheap / coding / multimodal）",

"source": {
"model\_page": "模型官方页面URL（用于抓取模型信息来源）",
"api\_docs": "API文档URL（开发参考）",
"pricing\_page": "价格页面URL（用于价格同步更新）",
"last\_updated": "数据最后更新时间（YYYY-MM-DD，用于判断是否需要更新）"
}
}
