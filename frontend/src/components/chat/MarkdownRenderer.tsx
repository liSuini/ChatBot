import { useMemo } from 'react'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// 模块级单例：避免每次 render 重建解析器
const md = new MarkdownIt({
  html: false, // 防 XSS，不解析内嵌 HTML
  linkify: true, // 自动识别 URL 为链接
  typographer: true, // 排版优化（智能引号等）
  highlight(str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch {
        /* fall through to plain */
      }
    }
    // 未指定语言或不支持：返回转义后的纯文本
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

interface Props {
  content: string
}

/** 渲染 Markdown 内容（流式/完成均使用同一解析器，markdown-it 容忍不完整内容） */
export default function MarkdownRenderer({ content }: Props) {
  const html = useMemo(() => md.render(content), [content])
  return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
}
