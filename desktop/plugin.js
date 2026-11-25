import { createElement as h, useEffect, useRef, useState } from 'react'

function Designer({ title: originalTitle, latest, start, apply, image }) {
  const [title, setTitle] = useState(originalTitle)
  const [subtitle, setSubtitle] = useState('')
  const [style, setStyle] = useState('清爽编辑风')
  const [mode, setMode] = useState('upload')
  const [file, setFile] = useState(null)
  const [authorized, authorize] = useState(false)
  const [x, setX] = useState(0.5)
  const [y, setY] = useState(0.5)
  const [job, setJob] = useState(null)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const lock = useRef(false)
  const sequence = useRef(0)
  const read = useRef(latest)
  read.current = latest
  useEffect(() => {
    let active = true
    let timer
    async function observe() {
      const turn = sequence.current
      try {
        const current = await read.current()
        if (active && turn === sequence.current && !lock.current) setJob(current)
      } catch (error) {
        if (active) setNotice(String(error))
      }
      if (active) timer = setTimeout(observe, 2500)
    }
    void observe()
    return () => { active = false; clearTimeout(timer) }
  }, [])
  const pending = job && ['queued', 'running'].includes(job.state)
  async function perform(fn) {
    if (lock.current) return
    lock.current = true
    sequence.current++
    setBusy(true)
    setNotice('')
    try { await fn() } catch (error) { setNotice(String(error)) }
    finally { lock.current = false; setBusy(false) }
  }
  function generate(type) {
    return perform(async () => {
      const next = await start({
        request_id: crypto.randomUUID(), mode: type, title, subtitle, style, x, y,
        ...(type === 'reuse' ? { previous: job.id } : {}),
        ...(type === 'upload' || type === 'background' ? { file, authorized } : {})
      })
      setJob(next)
    })
  }
  const field = (label, element) => h('label', { className: 'grid gap-1 text-sm' }, label, element)
  const text = (value, change, maxLength) => h('input', { className: 'rounded border bg-background p-2', value, maxLength,
    onChange: e => change(e.target.value) })
  const button = (label, action, disabled) => h('button', { type: 'button', className: 'rounded border px-3 py-2',
    disabled: !!(busy || pending || disabled), onClick: action }, label)
  const slider = (value, change) => h('input', { type: 'range', min: 0, max: 1, step: 0.01, value,
    onChange: e => change(Number(e.target.value)) })
  return h('section', { className: 'grid gap-3 rounded border p-3' },
    h('h3', null, '封面设计'),
    field('图片来源', h('select', { value: mode, onChange: e => setMode(e.target.value) },
      ...[['upload','上传成品封面'], ['background','上传底图并排版'], ['ai','AI 生成底图']].map(([value,label]) => h('option',{key:value,value},label)))),
    mode !== 'ai' && field('选择 PNG、JPEG 或 WebP', h('input', { type: 'file', accept: 'image/png,image/jpeg,image/webp',
      onChange: e => { setFile(e.target.files[0]); authorize(false) } })),
    mode !== 'ai' && field('我有权使用这张图片', h('input',{type:'checkbox',checked:authorized,onChange:e=>authorize(e.target.checked)})),
    mode !== 'upload' && field('标题', text(title, setTitle, 80)),
    mode !== 'upload' && field('副标题', text(subtitle, setSubtitle, 120)),
    mode !== 'upload' && field('横向裁切位置',slider(x,setX)),
    mode !== 'upload' && field('纵向裁切位置',slider(y,setY)),
    mode === 'ai' && field('底图风格',text(style,setStyle,400)),
    button(mode === 'ai' ? (job?.background ? '重新生成底图（调用生图服务）' : '生成底图（调用生图服务）') : '预览上传图片',
      () => generate(mode), mode !== 'ai' && (!file || !authorized)),
    mode !== 'upload' && job?.background && button('复用上张底图重新排版', () => generate('reuse')),
    pending && h('p',{role:'status'},'正在生成，稍后可回到本稿查看'),
    job?.error && h('p',{role:'alert'}, job.error),
    job?.state === 'completed' && h('div', null, h('p',null,'候选封面'), image(job.asset_id),
      button('应用这张候选封面',()=>perform(async()=>{await apply(job.id);setNotice('封面已应用')}))),
    notice && h('p',{role:'status'},notice))
}

export default {
  id: 'cover-designer', name: '封面设计',
  register(ctx) {
    ctx.register({ id: 'panel', area: 'operations.coverDesigner', data: { render: props => h(Designer, props) } })
  }
}
