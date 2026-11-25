import { createElement as h, useEffect, useId, useRef, useState } from 'react'

function Designer({ title: originalTitle, latest, detail, start, apply, image }) {
  const styleList = useId()
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
  const unresolved = useRef(null)
  const read = useRef(latest)
  const poll = useRef(detail)
  read.current = latest
  poll.current = detail
  useEffect(() => {
    let active = true
    const turn = sequence.current
    read.current().then(current => {
      if (active && turn === sequence.current) setJob(current)
    }).catch(error => { if (active) setNotice(String(error)) })
    return () => { active = false }
  }, [])
  const pending = job && ['queued', 'running'].includes(job.state)
  useEffect(() => {
    if (!pending) return
    let active = true
    let timer
    async function observe() {
      try {
        const current = await poll.current(job.id)
        if (active) setJob(current)
      } catch (error) {
        if (active) setNotice(String(error))
      }
      if (active) timer = setTimeout(observe, 2000)
    }
    timer = setTimeout(observe, 600)
    return () => { active = false; clearTimeout(timer) }
  }, [pending, job?.id])
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
      const payload = { mode: type, title, subtitle, style, x, y,
        ...(type === 'reuse' ? { previous: job.id } : {}),
        ...(type === 'upload' || type === 'background' ? { file, authorized } : {})
      }
      const key = JSON.stringify([type, title, subtitle, style, x, y, payload.previous, file?.name, file?.size, file?.lastModified])
      if (unresolved.current?.key !== key) unresolved.current = { key, id: crypto.randomUUID() }
      const next = await start({ ...payload, request_id: unresolved.current.id })
      unresolved.current = null
      setJob(next)
    })
  }
  const field = (label, element) => h('label', { className: 'grid gap-1 text-sm' }, label, element)
  const text = (value, change, maxLength, list) => h('input', { className: 'rounded border bg-background p-2', value, maxLength, list,
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
    mode === 'ai' && field('底图风格',text(style,setStyle,400,styleList)),
    mode === 'ai' && h('datalist', { id: styleList }, ...['清爽编辑风','水彩插画','自然摄影','复古印刷'].map(value=>h('option',{key:value,value}))),
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
