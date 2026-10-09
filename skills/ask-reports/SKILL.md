---
name: ask-reports
description: Answer questions about the report catalogue from the report knowledge graph — which report types exist, what sections and fields a report shows and what they mean, which data source, table and column each value comes from, when a report runs and under which policies, which reports share fields or components, what a term of the ontology means, and how the build and run flow works. Use when the user asks "what reports do we have", "what does this report show", "where does this data come from", "when does it run", "which reports are similar", "what does <term> mean", or any question about a report definition.
---

# Answer questions from the report knowledge graph

The answers live in a knowledge graph compiled from each report's own files. You reach it through the
`report-ontology` tools this plugin provides: `list_questions`, `ask`, `explain`, `requirements`, `gaps`
(full names start with `mcp__plugin_pdf_to_template_report_ontology__`). They are read-only.

The graph answers a fixed set of competency questions. That is deliberate: each answer is a query someone wrote
and tested, so it is the same answer every time and it can say what is missing. Your job is to match what the
person asked to the right question, run it, and report the result faithfully.

## How to answer

1. **Find the question.** Call `list_questions` once per conversation; do not rely on a remembered list, because
   the ontology adds questions over time. Pick the question whose wording covers what the person asked. Several
   may be needed: "tell me about this report" is the catalogue entry, its sections, its data and its schedule.
2. **Fill its parameters.** Each question names the parameters it needs (`report`, `field`, `column`,
   `component`). If the person named a report loosely ("the balanced fund sheet"), run the catalogue question
   first and match against the ids and titles it returns. If two reports fit, ask which one.
3. **Run it with `ask`** and read `status`:
   - `answered` — report the rows.
   - `gap` — the rows are real, and the graph also knows something is missing. Give the answer **and** the gaps,
     in plain words ("30 of 35 fields are not mapped to a column yet"). Never fill a gap from your own knowledge.
   - `empty` — the graph holds nothing for this. Say so. An empty answer is a fact about the catalogue, not a
     failure to cover up.
4. **Say where the answer came from**: the question id, and the report it concerns. If `skipped` lists a report,
   tell the person that report is currently left out because its files fail validation, and why.

## Questions about meaning

When the person asks what a class, a relationship or a property means ("what is lineage status", "what does
'sourced from' connect"), call `explain` with the name or label. It returns the definition, what the edge links,
which questions read it and the file it is written in. `explain` with no term lists every class.

## Questions about the flow

Questions about how reports are built and run (steps, checks, thresholds, what happens on failure) are the
`flow:` questions. They need a flow folder; when the tool answers that none is configured, tell the person that
`FLOW_ROOT` must point at the folder holding `flow/flow.json`.

## When no question fits

Do not improvise an answer from file contents or general knowledge and present it as coming from the graph.
Say that the graph has no question for this yet, then:

- if a nearby question answers part of it, offer that part and name what it leaves out;
- write the person's question, as they asked it, as a new line in `reports/UNANSWERED.md` (create the file if
  needed) with today's date. That file is how a missing question reaches the ontology's owner: a new property
  or question always starts there, as a competency question.

## Presenting answers

Lead with the answer in a sentence, then the rows as a short table when there are several. Use the report's
titles and the fields' labels where the rows give them; keep ids in code formatting so the person can reuse
them. Translate statuses and codes into words the first time (`business_day:3` is "the third business day").
