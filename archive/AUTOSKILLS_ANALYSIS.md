# autoskills Analysis

## Repository cloned
- Cloned into `/home/anirband/perceptron/autoskills`
- The main CLI package lives in `packages/autoskills`
- The repository includes a website shell at root and the actual CLI implementation in the package folder

## Purpose
`autoskills` is a project that detects a developer project stack and automatically selects and installs AI agent skills from `skills.sh`.

Primary value:
- auto-detect technologies from package manifests, config files, workspace setups, and source tree heuristics
- map detected tech to curated skills
- install the selected skills in parallel
- optionally generate a `CLAUDE.md` summary for Claude Code consumption

## Core components

### `packages/autoskills/main.ts`
- CLI entry point for `npx autoskills`
- parses flags: `-y/--yes`, `--dry-run`, `-v/--verbose`, `-a/--agent`
- runs detection, prints tech summary and skill install list
- drives installation through `installer.ts`
- supports agent-specific install modes and dry-run

### `packages/autoskills/lib.ts`
- contains the detection logic and the skill registry export
- resolves workspaces for pnpm/Node/Deno workspaces
- scans files, package.json, config files, Gradle and .NET project layouts
- detects combos and frontend presence
- exports `detectTechnologies(projectDir)` and `detectAgents(home)`

### `packages/autoskills/skills-map.ts`
- contains the main `SKILLS_MAP` and `COMBO_SKILLS_MAP`
- defines tech `id`, `name`, `detect` rules, and skill markdown references
- supports package dependencies, config files, file content patterns, Gradle/.NET scans
- is effectively the "knowledge base" for what skills should be installed for a project

### `packages/autoskills/installer.ts`
- resolves whether `skills` CLI exists locally or falls back to `npx skills`
- builds install command arguments and runs installs in parallel
- provides terminal-friendly progress rendering and failure reporting
- safe fallback for non-TTY environments

### `packages/autoskills/README.md`
- confirms the design: local detection, zero config, install curated skills, generate `CLAUDE.md`
- documents supported technologies and combos
- positions the tool as a one-command skill stack installer

## How autoskills works
1. `detectTechnologies(projectDir)` scans the project root and workspace packages
2. it finds package deps, config files, workspace manifests, and file heuristics
3. detected tech entries are mapped to curated skill identifiers
4. combo skills are also enabled when multiple related techs appear
5. the CLI prints detected tech and candidate skills
6. installer adds skills through `skills add` or `npx skills add`
7. when `claude-code` is targeted, a `CLAUDE.md` summary is generated from installed markdown skills

## Why this is useful for our skills design
### Strong patterns to adopt
- tech detection as first-class behavior: keep a clean `SKILLS_MAP` with `detect` rules and skill references
- workspace-aware scanning: detect monorepos and packages, not just root package.json
- combo detection: install specialized skills for specific stack combinations
- agent-specific install modes: support installing skill bundles for different harnesses
- local `CLAUDE.md` generation for Markdown-based assistant summaries
- graceful CLI fallback and parallel install logic

### What we can reuse directly
- skill detection architecture from `lib.ts`
- curated mapping format in `skills-map.ts`
- the concept of pairing detected tech with skill markdown packages
- the installer pattern for local tooling vs CLI fallback
- the idea of a separate `skills` registry source

### What needs adaptation
- `autoskills` is built around `skills.sh` and an external CLI workflow
- for our coding agent, we likely want an internal registry or embedded skill metadata, not necessarily `npx skills`
- autoskills is JavaScript/TypeScript heavy; we should generalize detection logic for agents and local model targets
- the generated `CLAUDE.md` summary is useful, but our own system should also support other agent formats and custom skill manifests

## Can this be adopted for our skills part?
Yes — especially for the skill discovery and selection layer.
- Use its detection-weighted tech map as a template for our skill catalog
- Build our own `skills` registry that returns skill bundles, not external package installs
- Keep the idea of "installing" or enabling skills based on project stack
- Consider a separate thin CLI or project initializer that auto-attaches recommended skills

This repo is less a direct one-to-one implementation and more a strong architectural reference for a skills automation layer.

## ECC-specific insight: Legacy command shims and git automation
### Why ECC has 72 legacy command shims
ECC provides shell-like wrappers around agent capabilities to make the system feel familiar and scriptable.
- each shim maps a command to an agent or task
- this gives users a stable CLI surface even as underlying agents evolve
- it supports backward compatibility and automation scripts
- it lets the team expose agent actions through traditional developer tooling

### Why ECC has extensive git hooks and automation
Because ECC is designed as a production-ready coding system, it treats Git actions as quality and maintenance checkpoints.
- pre-commit, post-merge, pre-push hooks enforce linting, tests, security, formatting, and doc updates
- automation keeps agent-generated code aligned with repo policies
- it reduces drift between manual changes and AI-driven changes
- it also enables continuous learning / diagnostics during normal developer workflow

### Recommendation for our project
Yes, we should plan for extensive Git automation if we want our coding assistant to be robust:
- use hooks to verify code before commit/push
- run targeted AI checks on changed files
- optionally trigger skill install/update workflows after merges
- keep command shim UX for core agent actions if we want a familiar CLI layer
