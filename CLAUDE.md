# Feilong

## Code review

When reviewing a change in this repository, follow
`.claude/skills/feilong-review/SKILL.md`. In short:

- Read the PR description and discussion first. A real z/VM run shown there
  beats reasoning by analogy with other SMAPI APIs.
- Do not infer SMAPI request formats or query output values from other APIs;
  report them as "needs verification" unless there is direct evidence.
- Read the called helper before claiming what it does.
- Give each finding a concrete trigger and its likelihood; do not blame a PR
  for problems the whole SDK has.
- On a re-review, say which earlier findings are fixed, still open, or new.
