const box = (x, y, w, h, fill) => <rect x={x} y={y} width={w} height={h} rx='8' fill={fill} stroke='var(--cds-border-strong, #888)' />;
const arrow = (x1, y1, x2, y2) => <line x1={x1} y1={y1} x2={x2} y2={y2} stroke='var(--cds-text-secondary, #888)' strokeWidth='1.5' markerEnd='url(#ah)' />;
export default () => <svg viewBox='0 0 760 400' role='img' aria-label='Agent frame versus workflow frame' fontSize='12'>
<defs><marker id='ah' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='var(--cds-text-secondary, #888)' /></marker></defs>
<text data-claude-text-id='title' x='20' y='26' fontSize='15' fontWeight='600' fill='var(--cds-text-primary)'>Same job, two frames: the model decides the route, or the files do</text>
<g data-claude-anchor='agent-frame'>
<text data-claude-text-id='agent-head' x='30' y='60' fontSize='13' fontWeight='600' fill='var(--cds-text-primary)'>Agent frame</text>
{box(30, 74, 320, 44, 'var(--cds-background-secondary, #f3f3f3)')}
<text data-claude-text-id='agent-persona' x='46' y='101' fill='var(--cds-text-primary)'>"An agent that does X" (persona, goal, tools)</text>
{arrow(190, 118, 190, 140)}
{box(30, 140, 320, 70, 'var(--cds-background-secondary, #f3f3f3)')}
<text x='46' y='164' fill='var(--cds-text-primary)'><tspan data-claude-text-id='orch-1'>Orchestration code: memory, handoffs,</tspan><tspan data-claude-text-id='orch-2' x='46' dy='18'>tool routing, retries, when-am-I-done logic</tspan></text>
{arrow(190, 210, 190, 232)}
{box(30, 232, 320, 44, 'var(--cds-background-secondary, #f3f3f3)')}
<text data-claude-text-id='agent-model' x='46' y='259' fill='var(--cds-text-primary)'>Model chooses the next step each turn</text>
<text x='30' y='306' fill='var(--cds-text-secondary)'><tspan data-claude-text-id='agent-note-1'>Hundreds of lines to steer one agent to the</tspan><tspan data-claude-text-id='agent-note-2' x='30' dy='17'>right place at the right time (Weinberg's 80%).</tspan></text>
</g>
<g data-claude-anchor='workflow-frame'>
<text data-claude-text-id='wf-head' x='410' y='60' fontSize='13' fontWeight='600' fill='var(--cds-text-primary)'>Workflow frame</text>
{box(410, 74, 320, 44, 'var(--cds-background-secondary, #f3f3f3)')}
<text data-claude-text-id='wf-map' x='426' y='101' fill='var(--cds-text-primary)'>CLAUDE.md / AGENTS.md: route table per job</text>
{arrow(570, 118, 570, 140)}
{box(410, 140, 150, 70, 'var(--cds-background-secondary, #f3f3f3)')}
<text x='422' y='164' fill='var(--cds-text-primary)'><tspan data-claude-text-id='step1-1'>Step 1 .md</tspan><tspan data-claude-text-id='step1-2' x='422' dy='18'>reads input, uses</tspan><tspan data-claude-text-id='step1-3' x='422' dy='18'>script, writes out1</tspan></text>
{arrow(560, 175, 580, 175)}
{box(580, 140, 150, 70, 'var(--cds-background-secondary, #f3f3f3)')}
<text x='592' y='164' fill='var(--cds-text-primary)'><tspan data-claude-text-id='step2-1'>Step 2 .md</tspan><tspan data-claude-text-id='step2-2' x='592' dy='18'>reads out1,</tspan><tspan data-claude-text-id='step2-3' x='592' dy='18'>writes gaps.md</tspan></text>
{arrow(655, 210, 655, 232)}
{box(580, 232, 150, 44, 'var(--cds-background-secondary, #f3f3f3)')}
<text data-claude-text-id='owner' x='592' y='259' fill='var(--cds-text-primary)'>Owner reviews (gate)</text>
{box(410, 232, 150, 44, 'var(--cds-background-secondary, #f3f3f3)')}
<text data-claude-text-id='runtime' x='422' y='259' fill='var(--cds-text-primary)'>Model = runtime</text>
<text x='410' y='306' fill='var(--cds-text-secondary)'><tspan data-claude-text-id='wf-note-1'>Every arrow has a verb: reads, uses, writes.</tspan><tspan data-claude-text-id='wf-note-2' x='410' dy='17'>Determinism = fixed route + scripts + checks,</tspan><tspan data-claude-text-id='wf-note-3' x='410' dy='17'>not the model reading Markdown.</tspan></text>
</g>
<line x1='380' y1='50' x2='380' y2='370' stroke='var(--cds-border-strong, #ccc)' strokeDasharray='4 4' />
</svg>;