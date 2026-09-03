/** 流式打字光标：闪烁动画 */
export default function StreamingCursor() {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 6,
        height: 16,
        background: '#999',
        marginLeft: 2,
        animation: 'blink 1s step-end infinite',
        verticalAlign: 'text-bottom',
      }}
    />
  )
}
