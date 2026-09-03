from html import escape

from views.html_formatters import stamp


def _esc(value):
    return escape("" if value is None else str(value))


def format_answer(question, answer, model):
    return f"""
<p class="project-id">{_esc(question)}</p>
<p>{_esc(answer)}</p>
<p class="project-id">Answered by {_esc(model)}</p>
""".strip()


def _format_observations(observations):
    if not observations:
        return '<p class="empty-state">The model returned no usable proposals.</p>'

    items = []
    for observation in observations:
        proposal = observation.get("proposal") or {}
        hours = observation.get("hours") or proposal.get("hours")
        target = observation.get("target_name") or (
            "deferred" if observation.get("target") is None else proposal.get("to_staff_id")
        )
        items.append(f"""
    <li style="margin-bottom:.6rem">
      {stamp(observation['verdict'])}
      Move {_esc(hours)}h of "{_esc(observation.get('activity'))}" &rarr; {_esc(target)}
      <br><span class="project-id">{_esc(observation['reason'])}</span>
    </li>""")
    return f'<ul style="list-style:none;padding-left:0">{"".join(items)}</ul>'


def _format_round(round_data):
    label = "Act" if round_data["phase"] == "act" else "Adapt"
    return f"""
  <details {"open" if round_data["phase"] == "act" else ""}>
    <summary>{_esc(label)} &mdash; round {round_data['round']}
             ({len(round_data['proposals'])} proposal(s))</summary>
    <h4>Observe</h4>
    {_format_observations(round_data['observations'])}
    <details>
      <summary class="project-id">Raw model response</summary>
      <pre style="overflow-x:auto;white-space:pre-wrap">{_esc(round_data['raw'])}</pre>
    </details>
  </details>"""


def format_cycle(cycle, saved=None):
    source = cycle["plan"]["source"]
    rounds = "".join(_format_round(r) for r in cycle["rounds"])

    saved_note = ""
    if saved:
        saved_note = (
            f'<p class="empty-state">{len(saved)} recommendation(s) saved for '
            f"human review.</p>"
        )

    adapted = any(r["phase"] == "adapt" for r in cycle["rounds"])
    adapt_note = (
        '<p class="project-id">Adapt round ran: the first set of proposals failed validation.</p>'
        if adapted else
        '<p class="project-id">No adapt round needed: the first set of proposals validated.</p>'
    )

    return f"""
<h3>Rebalance cycle &mdash; {_esc(source['staff_name'])} (staff {source['staff_id']})</h3>
<p class="project-id">{_esc(cycle['model'])} &middot;
   {source['computed_hours']:.1f}h of {source['cap']:.1f}h cap &middot;
   {len(cycle['accepted'])} accepted, {len(cycle['rejected'])} rejected</p>

<details>
  <summary>Plan &mdash; evidence gathered</summary>
  <pre style="overflow-x:auto;white-space:pre-wrap">{_esc(cycle['context'])}</pre>
</details>
{rounds}
{adapt_note}
{saved_note}
""".strip()
