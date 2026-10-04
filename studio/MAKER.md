# TechMendly Reel Maker: playbook for unattended runs

Goal: keep `queue.json` stocked with 7+ pending Reels that are accurate, useful and visually varied. Quality over quantity: if a Reel isn't good, remake it or drop it. Never post anything yourself here; the Daily TechMendly Reel task does the posting.

## Run steps
1. Clone/attach repo `shahjeek266/techmendly-reels` (push access). Count items with status "pending" in queue.json. If 5 or more, stop and say "queue is fine".
2. Run `bash studio/setup.sh` (installs deps, downloads the Kokoro voice model, ~340 MB).
3. Read `studio/topics.md` (used topics + idea bank). Pick topics so the new batch is a MIX (see rules). Make enough Reels to bring pending to 7 (max 7 new per run).
4. For each Reel write `studio/specs/<id>.json` (see `specs/reel-05-ai-ask-first.json` as the model) and render:
   `KOKORO_DIR=~/kokoro python3 studio/render_spec.py studio/specs/<id>.json`
   Outputs `reels/<id>.mp4`, `covers/<id>-cover.png`, `captions/<id>.txt`, and a check sheet at `/tmp/<id>_check/sheet.png`.
5. QUALITY CHECK each Reel (do not skip): open sheet.png and look at it. Fail and fix if: text is cut off or overlaps the caption box, a scene is mostly empty, a typo, a card overflows. Check duration is 25-45 s (`ffprobe`). Re-render until it passes. Read the spoken lines aloud in your head: awkward or wrong pronunciation (acronyms, URLs, brand names) gets a respelling in `say` and the proper form in `shown`.
6. Do this one Reel at a time and commit+push after EACH Reel so progress is saved if the session stops. Append each Reel to the END of the `queue` in queue.json as `{"id": "<id>", "status": "pending"}`, add the topic to `studio/topics.md` under Used, commit ("Add <ids> to queue") and push to main.
7. Report: topics made, one line each, and the new pending count.

## Content rules (what keeps the account from looking like spam)
- Every Reel teaches ONE concrete, useful thing a viewer can do in under a minute. No filler, no vague hype.
- ACCURACY: only state things you are sure are true and current. If a fact could be outdated (prices, menu paths, feature names, limits), check with WebSearch first or leave it out. Never invent stats; prefer no statistic over a made-up one. No medical, legal or financial advice. Don't name competitors negatively.
- MIX per batch of 7: about 2 AI tips, 2 WordPress/website fixes, 1 automation/productivity, 1 online safety, 1 free choice. Don't put two Reels on the same topic in a row.
- VARIETY (important for originality): rotate `theme` (dark, light, teal) so no two consecutive Reels share a theme, and vary the scene order and mix. Use at least 4 different scene types across a batch. Vary hook openings: a question, a bold claim, a myth, a number. Never reuse a hook sentence.
- HOOK: scene 1 must stop the scroll in 2 seconds: say the problem or a surprising claim, 8-12 words.
- Length 25-45 s, 5-7 scenes, one idea per scene, short sentences in `say`.
- Ending: last scene is `outro` ("Follow @techmendly"). Add a save/share nudge naturally when it fits ("Save this for later").
- Captions (`caption` field): 2-4 short lines of value beyond the video (the key command/steps as text, so it is worth saving), then "Follow @techmendly for a new tech tip every day.", then 8-10 relevant hashtags (always end with #techmendly). Emojis sparingly (1-4).
- If a Reel would need a screen recording of a real product's UI you can't reproduce faithfully, don't fake the UI: use steps/tip/compare scenes with text instead.
- AI-prompt tips should SHOW the prompt being typed: use the `chat` scene (typed user message + AI reply) like the best earlier Reel did. Don't make a new prompt tip that overlaps an already-used one (see topics.md); each AI tip needs a clearly different technique.
- Don't copy another creator's script or visuals. No music or clips from other sources (the renderer generates its own audio).
- The voice is synthetic; keep content honest and don't imply it is a real person.

## Scene types (see render_spec.py)
hook {text, hl[], sub, size}; myth_fact {myth, fact}; steps {title, items[3-4]}; compare {left{title,text}, right{title,text}}; stat {big, label}; tip {chip, title, code, body}; outro {text, sub}; chat {user, reply, hl[], title} (typed message then AI reply, user under ~120 chars, reply 2-5 short lines).
All scenes: `tag` (header pill, 1-3 words, optional), `say` (spoken sentence(s)), `shown` (optional caption text if it differs from `say`), `pad` (pause after, seconds). Keep text short: titles under ~50 chars, steps under ~40 chars each, compare text under ~70 chars.
Cover: `cover {lines[2-3 short lines], hl[line index to color], pill}`.
