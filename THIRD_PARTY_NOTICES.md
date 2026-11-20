# Third-party notices and copyright assessment

This project is a local workflow/configuration layer for novel writing on top of Basic Memory. It is released under the MIT License.

## Sources reviewed

| Source repository | Commit reviewed | Upstream license | Copyright notice | What was used |
|---|---|---|---|---|
| https://github.com/basicmachines-co/basic-memory | `de9adb8ccb227a6e70ee7a21f740c23571244564` | AGPL-3.0 | See upstream `LICENSE` | Architecture and documented MCP/note-format conventions only. No Basic Memory source code is copied into this repository. |
| https://github.com/lzk112233/dsh-self-memory | `eb06c42a91b9c765954b79b45b10d86c8a161bb6` | MIT | Copyright (c) 2026 lzk112233 | Method idea: keep memory out of the prompt by default and retrieve on demand. No source code is copied. |
| https://github.com/csyangwen/dsh-memory-evolve | `44b6b3eb65a1d50ceba0afb2c13acdd4a8b81423` | MIT | Copyright (c) 2026 dsh-external | Trigger/flow idea only: boundary events, scoped review, evidence, suggestion queue, user confirmation. No source code is copied. |

## Why this project can use MIT

- The upstream clones are **not part of this repository** and are excluded by `.gitignore`.
- This repository contains original documentation, schemas, workflow templates, a small DSH host plugin, and an external `lifecycle_extension/` Python module written for this project.
- Ideas, interfaces, documented formats, and workflow patterns are not copyrightable expression. No verbatim source files from the three upstream projects are redistributed here.
- `lifecycle_extension/` is a pure add-on: it imports no Basic Memory code, does not modify Basic Memory files, database tables, its Markdown parser/renderer, or its MCP tool registry. It only reads/writes frontmatter keys in user notes and re-ranks results returned by Basic Memory's own API. Because it is not a derivative work of Basic Memory's code, it does not inherit AGPL-3.0.
- Upstream project names and repository URLs are retained for attribution only.

## AGPL-3.0 boundary — Basic Memory

Basic Memory is AGPL-3.0. To avoid AGPL obligations on this MIT project:

- Do not copy Basic Memory Python source into this repository.
- Do not vendor its license-protected code, assets, or modified derivatives here.
- Do not publish the cloned `basic-memory/` directory as part of this repository.
- This project only documents how to use Basic Memory as a separate tool/MCP server and relies on its published interoperability conventions.

If someone later copies Basic Memory source into this repository, the MIT license claim would no longer be valid for the combined work; AGPL-3.0 obligations would need to be followed.

## MIT upstream boundary — dsh-self-memory and dsh-memory-evolve

Both MIT-licensed projects permit reuse with attribution when copying or distributing their software or substantial portions. This project does not copy their source code; it credits them as conceptual sources. If substantial code is copied later, retain the respective upstream copyright and permission notices.

## Attribution

This project was informed by:

- Basic Memory — https://github.com/basicmachines-co/basic-memory
- dsh-self-memory — https://github.com/lzk112233/dsh-self-memory
- dsh-memory-evolve — https://github.com/csyangwen/dsh-memory-evolve

See also each upstream repository's own `LICENSE` file for authoritative terms.
