---
name: feilong-review
description: Review a Feilong pull request or diff (zvmsdk, smtLayer, zthin C code, REST API). Use whenever asked to review, re-review or check review comments on a Feilong PR. Adds verification rules on top of the generic code review, learned from findings that turned out wrong.
---

# Reviewing Feilong changes

Run the normal review (for example the `code-review` skill), then apply the
rules below before you report anything. A finding that fails a rule is
dropped, or reported as a question instead of a bug.

## 1. Read the PR's own evidence first

Before reporting, read the PR description, the comments and the review
threads, including the author's replies.

- Output from a real z/VM run (smcli output, rc/rs, screenshots, logs) beats
  reasoning by analogy. If the PR shows a call returning `rc=0 rs=0`, do not
  report that call's request format as broken because a sibling API encodes
  it differently.
- Do not repeat a point a reviewer already raised and the author fixed. Do
  say when an earlier comment is only partly fixed, and what is left.
- When re-reviewing, compare against the previous review: say which findings
  are new, which are fixed, and which are still open but not reported this
  time. Do not let a valid finding silently disappear.

Lesson: a review claimed `vmapiImageRenameDm.c` had to send
`new_image_name=<id>` NUL-terminated with no length prefix, like
`vmapiVirtualNetworkVswitchSetExtended.c`. The PR description showed the
length-prefixed form succeeding on z/VM. The "fix" would have broken it.

## 2. SMAPI and CP behaviour is not inferred from other APIs

SMAPI APIs, especially new ones added by an APAR (for example
`Image_Rename_DM`, VM66893), can lay out parameters differently from older
ones. The same goes for query output values (`PROM`, `OSDSIM`, `port_num`)
and for which keywords `Virtual_Network_Vswitch_Set_Extended` accepts
together.

- If the only evidence is "another API does it differently", report it as
  "verify against the SMAPI reference or a test run", not as a bug.
- Fixes that depend on such values must say so as an assumption.

## 3. Read the callee before claiming a bug

Follow the call into the helper before reporting what it does. Facts that
several wrong findings missed:

- `getAndParseSmapiBuffer()` (`zthin-parts/zthin/src/smapiTableParser.c`)
  frees the input buffer on every path, so callers must not free `inputP`.
- `namelist_add()` and `namelist_remove()` in `zvmsdk/smtclient.py` go
  through `_request_with_error_ignored()` and never raise.
- `smtLayer/ReqHandle.py` splits the request with `shlex.split()`, and the
  operands reach smcli as an argv list. A quoted value (`-k key='a b'`)
  stays one argument. An unquoted blank splits it.
- `query_vswitch()` raises `SDKObjectNotExistError` for a missing vswitch
  (rc 212 / rs 40). Its `authorized_users` keys can be in any case.
- `grant_user_to_vswitch()` does nothing if the user is already authorized.
- The `userid`, `assigner_id` and `owner` columns are `COLLATE NOCASE`.
- REST input is validated by the schemas in `zvmsdk/sdkwsgi/schemas`, but
  `zvmsdk/api.py` can also be called directly from Python, so `api.py`
  needs its own checks.

## 4. Rate likelihood, not just possibility

For each finding, state the concrete trigger and how likely it is.

- Lower the severity when the trigger needs an unusual state (for example a
  vswitch grant for a userid that does not exist on z/VM yet).
- Do not blame a PR for a problem the whole SDK has (for example, no guest
  operation takes a lock, so concurrent operations can always race). Mention
  it as context at most.

## 5. Review the fix too

When you propose or write a fix, list the new risks it brings: new failure
modes (for example, failing when any vswitch on the host cannot be queried),
extra SMAPI calls, and behaviour that has not been run on z/VM.

## 6. Run the checks that exist

- Unit tests: `python -m unittest discover -s zvmsdk/tests/unit`
- Style: `flake8` (settings in `tox.ini`, max line length 120), and
  `git diff --check` for trailing whitespace in C files.
- C syntax: `gcc -fsyntax-only -Izthin-parts/zthin/include <file>.c`

Report which checks ran and their results. Unit tests mock SMAPI, so they
cannot confirm the request format; say so when a finding depends on it.
