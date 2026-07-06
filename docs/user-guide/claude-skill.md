# Claude Code Skill

slurm-cli ships a [Claude Code](https://claude.com/claude-code) skill that teaches Claude how to construct correct `slurm-cli` invocations — verbs/resources, filter syntax, output formats, and caching flags — without re-deriving them from source each time.

## Installation

Copy [`slurm-cli-skill.md`](https://github.com/zhum/slurm-cli/blob/main/slurm-cli-skill.md) from the repository root into your project's or user's skills directory:

```bash
# Project-local (checked into a specific repo)
mkdir -p .claude/skills
cp slurm-cli-skill.md .claude/skills/slurm-cli.md

# User-wide (available in every project)
mkdir -p ~/.claude/skills
cp slurm-cli-skill.md ~/.claude/skills/slurm-cli.md
```

Claude Code picks up skills automatically from either location — no restart or registration step required.

## Usage

Once installed, just ask Claude to work with your Slurm cluster in natural language, e.g.:

- "show me all running jobs for user john"
- "drain the gpu partition except nodes reserved for maintenance"
- "list qos entries sorted by priority as json"

Claude will invoke the skill to build the right `slurm-cli` command (correct verb/resource, filter syntax, `not:` exclusions, `--profile`/`--json` flags, and `--force-update` after mutations) instead of guessing.

The same content lives at `.claude/skills/slurm-cli.md` in this repository, so it's already active when working inside this repo with Claude Code.
