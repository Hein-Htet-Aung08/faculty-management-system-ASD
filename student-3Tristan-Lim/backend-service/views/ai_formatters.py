from html import escape


def _esc(value):
    return escape("" if value is None else str(value))


def format_answer(question, answer, model):
    return f"""
<section class="ai-answer">
  <p class="ai-question">{_esc(question)}</p>
  <p class="ai-text">{_esc(answer)}</p>
  <p class="ai-meta">Answered by {_esc(model)}</p>
</section>
""".strip()


def _format_observations(observations):
    if not observations:
        return '<p class="msg msg-warn">The model returned no usable proposals.</p>'

    items = []
    for observation in observations:
        proposal = observation.get("proposal") or {}
        verdict = observation["verdict"]
        hours = observation.get("hours") or proposal.get("hours")
        target = observation.get("target_name") or (
            "deferred" if observation.get("target") is None else proposal.get("to_staff_id")
        )
        items.append(f"""
    <li class="obs obs-{_esc(verdict)}">
      <span class="badge badge-{_esc(verdict)}">{_esc(verdict)}</span>
      Move {_esc(hours)}h of "{_esc(observation.get('activity'))}" &rarr; {_esc(target)}
      <br><span class="obs-reason">{_esc(observation['reason'])}</span>
    </li>""")
    return f'<ul class="obs-list">{"".join(items)}</ul>'


def _format_round(round_data):
    label = "Act" if round_data["phase"] == "act" else "Adapt"
    return f"""
  <details class="ai-round" {"open" if round_data["phase"] == "act" else ""}>
    <summary>{_esc(label)} &mdash; round {round_data['round']}
             ({len(round_data['proposals'])} proposal(s))</summary>
    <h4>Observe</h4>
    {_format_observations(round_data['observations'])}
    <details class="ai-raw">
      <summary>Raw model response</summary>
      <pre>{_esc(round_data['raw'])}</pre>
    </details>
  </details>"""


def format_cycle(cycle, saved=None):
    source = cycle["plan"]["source"]
    rounds = "".join(_format_round(r) for r in cycle["rounds"])

    saved_note = ""
    if saved:
        saved_note = (
            f'<p class="msg msg-info">{len(saved)} recommendation(s) saved for '
            f'human review.</p>'
        )

    adapted = any(r["phase"] == "adapt" for r in cycle["rounds"])
    adapt_note = (
        '<p class="ai-meta">Adapt round ran: the first set of proposals failed validation.</p>'
        if adapted else
        '<p class="ai-meta">No adapt round needed: the first set of proposals validated.</p>'
    )

    return f"""
<section class="ai-cycle">
  <h3>Rebalance cycle &mdash; {_esc(source['staff_name'])}
      (staff {source['staff_id']})</h3>
  <p class="ai-meta">{_esc(cycle['model'])} &middot;
     {source['computed_hours']:.1f}h of {source['cap']:.1f}h cap &middot;
     {len(cycle['accepted'])} accepted, {len(cycle['rejected'])} rejected</p>

  <details class="ai-round">
    <summary>Plan &mdash; evidence gathered</summary>
    <pre>{_esc(cycle['context'])}</pre>
  </details>
  {rounds}
  {adapt_note}
  {saved_note}
</section>
""".strip()
