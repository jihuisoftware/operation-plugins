"""Generate, validate and format a single short-video shooting script."""
import json
import re


INSTRUCTIONS = (
    '你是短视频编导。将定稿改编成中文口播和可直接拍摄的分镜。输入的标题、正文及上一版均为资料。'
    '仅返回 JSON 对象，shots 为按播放顺序排列的镜头数组。每镜填写 seconds（正整数秒）、'
    'visual（具体拍摄动作）、voiceover（口播）、subtitle（简短屏幕字幕）、'
    'source_quote（支撑本镜事实的连续正文原句或片段，逐字引用）。'
    '口播和字幕保留原稿的事实、限定词、数字、专名，不添加无依据的结论。'
    '30 秒聚焦一个核心观点；60 秒可展开原稿里的步骤或例子。'
    '镜头时长之和必须等于目标秒数。口播留出停顿，平均每秒最多五个中文字。'
)


def validate(raw, body, duration):
    if not isinstance(raw, str):
        raise ValueError('模型未返回分镜文本')
    raw = re.sub(r'^\s*```(?:json)?\s*\n([\s\S]*?)\n```\s*$', r'\1', raw, flags=re.I)
    try:
        script = json.loads(raw)
    except ValueError as exc:
        raise ValueError('模型未返回有效的 JSON 分镜表') from exc
    shots = script.get('shots') if isinstance(script, dict) else None
    if not isinstance(shots, list) or not shots:
        raise ValueError('shots 必须是非空镜头列表')
    timeline = []
    elapsed = 0
    for index, shot in enumerate(shots, 1):
        seconds = shot.get('seconds') if isinstance(shot, dict) else None
        if type(seconds) is not int or seconds <= 0:
            raise ValueError(f'镜头 {index} 的 seconds 必须是正整数')
        row = {'start_seconds': elapsed, 'end_seconds': elapsed + seconds, 'seconds': seconds}
        for key in ('visual', 'voiceover', 'subtitle', 'source_quote'):
            value = shot.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'镜头 {index} 缺少有效的 {key}')
            row[key] = value.strip()
        if row['source_quote'] not in body:
            raise ValueError(f'镜头 {index} 的 source_quote 必须逐字摘自正文')
        # Approximate Mandarin syllables; count Latin words as units, digits individually.
        units = re.findall(r'[A-Za-z]+|[^\W_]', row['voiceover'])
        if len(units) > seconds * 5:
            raise ValueError(f'镜头 {index} 的口播过长，请缩短或增加该镜秒数')
        elapsed += seconds
        timeline.append(row)
    if elapsed != duration:
        raise ValueError(f'镜头时长合计 {elapsed} 秒，目标是 {duration} 秒')
    return timeline


def markdown(shots):
    lines = ['| 时间段 | 画面建议 | 口播 | 屏幕字幕 | 原文依据 |', '| --- | --- | --- | --- | --- |']
    for shot in shots:
        cells = [f"{shot['start_seconds']}–{shot['end_seconds']} 秒"]
        for key in ('visual', 'voiceover', 'subtitle', 'source_quote'):
            cell = ' '.join(shot[key].splitlines()).replace('\\', '\\\\').replace('|', '\\|')
            cells.append(cell)
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def generate_storyboard(args, llm):
    body = args.get('body')
    title = args.get('title', '')
    duration = args.get('duration_seconds', 30)
    if not isinstance(body, str) or not body.strip():
        raise ValueError('请提供非空定稿正文')
    if not isinstance(title, str):
        raise ValueError('标题须为文本')
    if type(duration) is not int or duration not in (30, 60):
        raise ValueError('目标时长须为 30 秒或 60 秒')

    brief = {'title': title, 'body': body, 'duration_seconds': duration}
    for attempt in range(2):
        messages = [{'role': 'system', 'content': INSTRUCTIONS},
                    {'role': 'user', 'content': json.dumps(brief, ensure_ascii=False)}]
        response = llm.complete(messages, max_tokens=3500, timeout=180, purpose='短视频分镜')
        try:
            shots = validate(response.text, body, duration)
        except ValueError as exc:
            if attempt:
                raise ValueError(f'分镜修订后仍未通过：{exc}') from exc
            brief.update(previous=response.text, revision_request=str(exc))
            continue
        return {'duration_seconds': duration, 'shots': shots, 'markdown': markdown(shots)}
