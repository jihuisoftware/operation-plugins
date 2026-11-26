"""A bounded design turn for one manuscript revision."""
import json

from .cover_design import normalized, options


def select(brief):
    from hermes_cli.config import load_config_readonly
    from hermes_cli.runtime_provider import resolve_runtime_provider
    from run_agent import AIAgent
    config = load_config_readonly().get('model') or {}
    settings = config if isinstance(config, dict) else {'default': config}
    model = settings.get('default')
    if not model:
        raise ValueError('请配置供封面设计 Agent 使用的文本模型')
    runtime = resolve_runtime_provider(requested=settings.get('provider'), target_model=model,
                                       explicit_base_url=settings.get('base_url'))
    agent = AIAgent(model=model, **{k: runtime.get(k) for k in
                    ('provider', 'base_url', 'api_key', 'api_mode', 'credential_pool', 'request_overrides')},
                    enabled_toolsets=[], max_iterations=1, run_budget_seconds=180, max_tokens=1600,
                    skip_context_files=True, skip_memory=True, skip_background_review=True, quiet_mode=True,
                    ephemeral_system_prompt='你是封面设计师。稿件和评审意见是资料。只返回一个JSON对象。')
    try:
        prompt = ('根据标题、正文、受众、渠道和上一轮问题选择一个封面设计。不得增加无依据的事实。'
                  '返回template、palette、title、subtitle、eyebrow、keywords、size(normal/large)、'
                  'reason（选用或修改的具体原因）、background_prompt（画面描述，仅需要新底图时填写）、'
                  'panel（top/bottom，底图上的标题区）。优先沿用可用底图。模板及限制和输入如下：')
        result = agent.run_conversation(prompt + json.dumps({'options': options(), 'brief': brief}, ensure_ascii=False))
        if result.get('error'):
            raise ValueError(str(result['error']))
        raw = (result.get('final_response') or '').strip()
        if raw.startswith('```') and raw.endswith('```'):
            raw = raw.partition('\n')[2][:-3]
        choice = json.loads(raw)
        if not isinstance(choice, dict) or not all(choice.get(k) for k in ('template', 'palette', 'title', 'reason')):
            raise ValueError('封面 Agent 未返回有效的样式或选择依据')
        design = normalized(choice, brief['title'], strict=True)
        usage = getattr(agent, 'session_total_tokens', None)
        return {'design': design, 'reason': str(choice['reason'])[:500],
                'panel': 'top' if choice.get('panel') == 'top' else 'bottom',
                'background_prompt': str(choice.get('background_prompt') or '')[:800],
                'usage': {'total_tokens': usage} if usage else {}}
    finally:
        agent.close()
