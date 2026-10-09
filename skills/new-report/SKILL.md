---
name: new-report
description: Start the definition of a new report type with a report analyst — capture its requirements (sample PDF, purpose, parameters, data source and table, schedule, publishing, observability), draft its sections, fields and column mapping from the PDF, and repeat until the report ontology's own checks find nothing blocking. Use when the user wants to "define a new report", "onboard a report", "start a new report template", "capture the requirements of a report", or hands over a sample PDF to turn into a report type.
---

# Define a new report type with the analyst

You are working with a report analyst. They know the report, its readers and the table its data comes from; they
are not expected to know the ontology or the file formats. They always bring a sample PDF. At the end of this
skill the report exists as a folder of definition files that the report ontology accepts, and the template can
then be built from the same folder with the `pdf-to-template` skill.

```
reports/<report-id>/
  source/<sample>.pdf        the sample the analyst provided
  work/                      inspection output (page images, text spans)
  semantic/report.yaml       what the report is; its sections and fields and what they mean
  semantic/lineage.yaml      the data source, the table, and the column that supplies each field
  semantic/provenance.yaml   the record of the sample PDF
  manifest.json              schedule, parameter values, policies, observability
```

## The ontology decides what to ask

Do not work from a remembered checklist. The `report-ontology` tools (`requirements`, `gaps`, `ask`, `explain`,
`list_questions`; full names start with `mcp__plugin_pdf_to_template_report_ontology__`) tell you what a report
must hold, and they change when the ontology does.

- `requirements` lists every item: the file and key it is written to, whether it is required, what it means,
  and `provided_by`, which decides how you get it:
  - `analyst` — ask the analyst. Never invent these.
  - `agent` — draft it yourself from the sample PDF or the table, then show the analyst and correct it.
  - `flow` — recorded by a step of the build flow. Do not ask for it. The exceptions are the facts you measure
    in this session about the sample PDF (its sha256, its page kinds, the date received), and the technical
    header of the draft manifest described below.
- `gaps` checks the draft folder and returns what is still missing, with the file and key for each item.
  `blocking` items must reach zero. `warnings` are allowed in a draft and are what you report at the end.

When you do not understand an item, call `explain` on its `term` before asking the analyst about it; ask in the
analyst's words, not the ontology's.

## Before the first question

1. Call `requirements`, and `ask` the catalogue question (which report types exist) and the question that lists
   the fields the catalogue already defines. You will need both: the first to avoid a duplicate report and to
   borrow sensible defaults from a similar one, the second to reuse field ids.
2. Ask for the path to the sample PDF and for the analyst's name. Agree a report id (lower case, hyphens) and
   create the folder. Record the first status at once (see "The report's status"), so the report is visible as
   started from this moment. Copy the PDF into `source/`, compute its sha256, and inspect it:
   `python ${CLAUDE_PLUGIN_ROOT}/scripts/inspect_pdf.py <pdf> --out reports/<report-id>/work/`
   Look at the page images yourself. If a page is `raster`, tell the analyst now that fidelity will be capped
   and ask whether a production (vector) PDF exists.

## The report's status

`semantic/provenance.yaml` holds a `lifecycle` list: the report's status history. You add one entry each time the
report reaches a status, with who (`by`) and when (`at`, today's date). You never rewrite or delete an earlier
entry; a step back is a new entry. The last entry is the current status, and `gaps` returns it as
`lifecycle_status`.

| Status | Meaning | When it is recorded |
|---|---|---|
| `inception` | The definition has been started. | By you, when you create the folder: `by` is the analyst. |
| `saved` | The definition validates and is part of the catalogue graph. | By you, when `gaps` first returns nothing blocking, the manifest exists and the analyst has approved the sections, fields and mapping. |
| `in_validation` | The definition and its template are being checked by agents and a person. | Not in this skill: when the template goes to validation, by whoever sends it. |
| `in_production` | Documents are produced from a frozen release. | Not in this skill: at deployment, with who deployed it and when. It needs a frozen release. |

Record a status when it is reached, not in advance, and only the next one: the ontology refuses a history that
skips a status or goes back in time. If the session ends before `saved`, the report stays at `inception`, which
is the truth.

## The interview

Ask in small groups, a few related items at a time, and write each answer to its file as soon as you have it.
Where a similar report exists, offer its value as the default ("the balanced fund profile runs on the third
business day; the same here?"). A sensible order:

1. **What the report is** — title, kind, purpose, audience, owner, the languages it is offered in, and what
   identifies one document (its parameters: for example fund, series, as-of date, language).
2. **Where the data comes from** — the data source (a name for the connection, its kind, the database) and the
   one table that holds every column of this report. By convention the table takes the report's name; the
   analyst decides. Ask which column carries each parameter.
3. **How it runs** — schedule (cadence, day, as-of rule, calendar, timezone), where the allowed values of each
   parameter come from, where documents are published and how long they are kept.
4. **What is expected of a run** — the delivery deadline, the tolerated failure rate, who is alerted, and where
   run history is recorded.
5. **Verification and approval thresholds** — propose the values of the skeleton manifest
   (`${CLAUDE_PLUGIN_ROOT}/assets/example/manifest.json`) and ask for confirmation in one question; most
   analysts keep them.

If the analyst does not know an answer, do not guess and do not block the session: leave the item out, go on,
and let `gaps` carry it to the end as something still owed, with the name of who can answer it if they told you.

## What you draft yourself

From the page images and the text of the sample PDF, draft the `sections` and `fields` of `report.yaml`:

- One section per visual box, with its purpose in a sentence and the component that renders it.
- One field per piece of information shown. The field id is the snake_case form of the English label
  ("Total Fund Assets" → `total_fund_assets`). **Before naming a field, look it up in the catalogue's field
  list**: if another report already shows the same information, use its id, type and definition, so the two
  reports are recognised as sharing it. Invent a new id only for information the catalogue does not have.
- The label is what the report prints, per language; the meaning is what the value is, precisely enough that
  someone could check a number against it. Draft French labels and meanings when the report is offered in French.
- For a list or table, give the field a list type and its `row` structure (the members of one row).

Then show the analyst the sections and fields as a table and correct what they change. Their approval of this
table is the point of the session: take the time to get it right.

## The data mapping

Every field is supplied by exactly one column of the report's table. Propose `column: <field id>` with
`status: proposed` for each field; if you can see the table's columns (the analyst pastes them, or a database
tool is available), match against the real names instead of assuming. Walk the analyst through the proposals
and set `verified` only for the ones they confirm. Leave `unmapped` what nobody can place yet.

Tell the analyst how the two kinds of field are stored, because it decides what the data team must deliver:
a single-valued field reads the column's value; a structured field (a list, a series, a value with named parts)
reads **JSON text** from its column, an array of rows in the field's `row` shape. Show the expected JSON for
one such field from the sample PDF.

## The draft manifest

`manifest.json` needs a technical header before the analyst's answers validate. Copy `engine_version` and
`library_version` from the skeleton manifest, set `template_id` to the report id, `version` to `0.1.0`,
`ontology_version` to the report ontology version `list_questions` reports, `frozen` to `false`, `files` to
`{}`, and `source_sha256` to the hash you computed. Everything else in it comes from the interview.

## The loop

After each group of answers, and after each correction, call `gaps` on the report folder:

- for every `blocking` item, read its `file`, `path` and `message`; ask the analyst if it is theirs to answer,
  fix it yourself if it is a drafting error, and call `gaps` again;
- a warning that there is no `manifest.json` means the interview is not finished: the schedule, the policies and
  the observability expectations are still owed;
- stop when `blocking` is empty, the manifest exists, and the analyst has approved the sections, fields and mapping.

Do not edit the files of other reports, the ontology, or anything outside this report's folder.

## Finishing

Record `saved` if the conditions above are met. Then tell the analyst, in this order: that the report is defined,
its status, and where its folder is; what is still owed before
production, taken from the `warnings` of the last `gaps` call (fields not mapped to a column, meanings missing
in a language, the release not frozen) with who can supply each; and that the next step is building the
template from the sample PDF with the `pdf-to-template` skill. If the catalogue now shows another report
sharing many fields with this one, say so: it is a useful check that the two are consistent.
