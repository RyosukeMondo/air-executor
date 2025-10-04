# Pre-Commit Hook Integration Architecture

## Execution Flow

```mermaid
flowchart TD
    Start([Autonomous Fixing Start]) --> Setup0[SETUP Phase 0: Configure Pre-Commit Hooks]

    Setup0 --> CheckHooks{Hooks exist?}
    CheckHooks -->|Yes| CacheHooks[Cache hook configuration]
    CheckHooks -->|No| ConfigHooks[AI configures hooks]

    ConfigHooks --> InstallJS[JavaScript: husky + lint-staged]
    ConfigHooks --> InstallPy[Python: pre-commit framework]
    ConfigHooks --> InstallNative[Flutter/Go: native .git/hooks]

    InstallJS --> VerifyHooks[Verify hooks work]
    InstallPy --> VerifyHooks
    InstallNative --> VerifyHooks
    CacheHooks --> Setup1

    VerifyHooks --> Setup1[SETUP Phase 1: Test Discovery]
    Setup1 --> P1[P1: Static Analysis]

    P1 --> P1Pass{P1 Passed?}
    P1Pass -->|No| FixP1[Fix static issues]
    FixP1 --> TryCommit1[Try git commit]

    TryCommit1 --> HooksRun1[Pre-commit hooks run]
    HooksRun1 --> HooksPass1{Hooks pass?}

    HooksPass1 -->|No| BlockCommit1[❌ Commit blocked]
    HooksPass1 -->|Yes| CommitSuccess1[✅ Commit succeeds]

    BlockCommit1 --> FixMore1[Fix remaining issues]
    FixMore1 --> TryCommit1

    CommitSuccess1 --> P1
    P1Pass -->|Yes| P2[P2: Tests]

    P2 --> P2Pass{P2 Passed?}
    P2Pass -->|No| FixP2[Fix test failures]
    FixP2 --> TryCommit2[Try git commit]

    TryCommit2 --> HooksRun2[Pre-commit hooks run]
    HooksRun2 --> HooksPass2{Hooks pass?}

    HooksPass2 -->|No| BlockCommit2[❌ Commit blocked]
    HooksPass2 -->|Yes| CommitSuccess2[✅ Commit succeeds]

    BlockCommit2 --> FixMore2[Fix remaining issues]
    FixMore2 --> TryCommit2

    CommitSuccess2 --> P2
    P2Pass -->|Yes| Success([Success!])

    style Setup0 fill:#ff9999,stroke:#333,stroke-width:2px
    style HooksRun1 fill:#99ccff,stroke:#333,stroke-width:2px
    style HooksRun2 fill:#99ccff,stroke:#333,stroke-width:2px
    style BlockCommit1 fill:#ffcccc,stroke:#333,stroke-width:2px
    style BlockCommit2 fill:#ffcccc,stroke:#333,stroke-width:2px
    style CommitSuccess1 fill:#ccffcc,stroke:#333,stroke-width:2px
    style CommitSuccess2 fill:#ccffcc,stroke:#333,stroke-width:2px
    style Success fill:#90EE90,stroke:#333,stroke-width:4px
```

## Pre-Commit Hook Quality Gates

```mermaid
graph LR
    subgraph "JavaScript/TypeScript"
        JS1[Code Changes] --> JS2[git commit]
        JS2 --> JS3[.husky/pre-commit]
        JS3 --> JS4{tsc --noEmit}
        JS4 -->|Fail| JSFail[❌ Block]
        JS4 -->|Pass| JS5{eslint}
        JS5 -->|Fail| JSFail
        JS5 -->|Pass| JS6{npm test}
        JS6 -->|Fail| JSFail
        JS6 -->|Pass| JS7{coverage ≥60%}
        JS7 -->|Fail| JSFail
        JS7 -->|Pass| JSSuccess[✅ Commit]
    end

    subgraph "Python"
        PY1[Code Changes] --> PY2[git commit]
        PY2 --> PY3[pre-commit hooks]
        PY3 --> PY4{mypy}
        PY4 -->|Fail| PYFail[❌ Block]
        PY4 -->|Pass| PY5{pylint}
        PY5 -->|Fail| PYFail
        PY5 -->|Pass| PY6{pytest}
        PY6 -->|Fail| PYFail
        PY6 -->|Pass| PY7{coverage ≥60%}
        PY7 -->|Fail| PYFail
        PY7 -->|Pass| PYSuccess[✅ Commit]
    end

    style JSFail fill:#ffcccc
    style PYFail fill:#ffcccc
    style JSSuccess fill:#ccffcc
    style PYSuccess fill:#ccffcc
```

## Comparison: Old vs New Approach

```mermaid
graph TB
    subgraph "OLD: Prompt-Based (Fragile)"
        O1[AI receives prompt] --> O2["Prompt: Please run eslint"]
        O2 --> O3{AI decides}
        O3 -->|Follows| O4[Runs eslint]
        O3 -->|Ignores| O5[Skips check]
        O4 --> O6[Sees errors]
        O6 --> O7{AI decides}
        O7 -->|Good| O8[Fixes code]
        O7 -->|Bad| O9[Uses --no-verify]
        O8 --> O10[git commit]
        O9 --> O10
        O5 --> O10
    end

    subgraph "NEW: Hook-Based (Robust)"
        N1[AI receives prompt] --> N2["Prompt: Fix code to pass hooks"]
        N2 --> N3[Fixes code]
        N3 --> N4[git commit]
        N4 --> N5[Hooks run automatically]
        N5 --> N6{All checks pass?}
        N6 -->|No| N7[❌ Commit blocked]
        N6 -->|Yes| N8[✅ Commit succeeds]
        N7 --> N9[Must fix issues]
        N9 --> N3
    end

    style O5 fill:#ffcccc,stroke:#333,stroke-width:2px
    style O9 fill:#ffcccc,stroke:#333,stroke-width:2px
    style N7 fill:#ffffcc,stroke:#333,stroke-width:2px
    style N8 fill:#ccffcc,stroke:#333,stroke-width:2px
```

## Configuration Architecture

```mermaid
graph TB
    subgraph "Configuration Sources"
        Prompts[config/prompts.yaml]
        PreCommit[config/prompts-precommit.yaml]
    end

    subgraph "Cache Layer"
        Cache[config/precommit-cache/]
        Cache1[warps-hooks.yaml]
        Cache2[my-api-hooks.yaml]
        Cache --> Cache1
        Cache --> Cache2
    end

    subgraph "Runtime Components"
        Fixer[IssueFixer]
        Engine[IterationEngine]
    end

    subgraph "Project Hooks"
        Husky[.husky/pre-commit]
        PreCommitYAML[.pre-commit-config.yaml]
        Native[.git/hooks/pre-commit]
    end

    Prompts --> Fixer
    PreCommit -.->|Reference| Prompts
    Fixer --> Engine

    Engine -->|SETUP 0| ConfigureHooks[configure_precommit_hooks]
    ConfigureHooks --> Husky
    ConfigureHooks --> PreCommitYAML
    ConfigureHooks --> Native

    ConfigureHooks --> Cache1
    ConfigureHooks --> Cache2

    Husky -.->|Enforces| QualityGates[Quality Gates]
    PreCommitYAML -.->|Enforces| QualityGates
    Native -.->|Enforces| QualityGates

    style Prompts fill:#e1f5ff
    style QualityGates fill:#ccffcc,stroke:#333,stroke-width:4px
```

## Integration with Existing System

### Before (Prompt-Only)

```
SETUP → P1 (AI runs linters manually) → P2 (AI runs tests manually) → Success
```

### After (Hook-Enforced)

```
SETUP 0: Configure Hooks
    ↓
SETUP 1: Test Discovery
    ↓
P1 (Hooks enforce linting)
    ↓
P2 (Hooks enforce tests + coverage)
    ↓
Success
```

## Benefits Summary

| Aspect | Old (Prompts) | New (Hooks) |
|--------|--------------|-------------|
| **Reliability** | AI might skip checks | Git enforces checks |
| **Bypass** | `--no-verify` possible | Forbidden by prompts |
| **Consistency** | Varies per execution | Same every time |
| **Speed** | AI decides when to check | Automatic on commit |
| **Learning** | AI interprets prompts | AI reads hook config |
| **Trust** | Relies on AI behavior | Relies on git |

## Key Design Decisions

### 1. SETUP Phase 0 (Before everything)
- **Why:** Hooks must exist before P1/P2 phases need them
- **When:** First time project is processed
- **Cache:** 7-day TTL (hooks don't change often)

### 2. Prompt Updates (Respect hooks)
- **Why:** AI must know hooks exist and respect them
- **How:** Check for hooks, never use `--no-verify`
- **Enforcement:** Prompts explicitly forbid bypassing

### 3. Cache Strategy
- **Location:** `config/precommit-cache/`
- **Format:** YAML (human-readable)
- **Content:** Hook config, tools used, verification status
- **TTL:** 7 days (can be reconfigured)

### 4. Fallback Behavior
- **If hook config fails:** Continue without hooks (log warning)
- **If hooks don't exist:** AI tries to configure them
- **If can't configure:** Fall back to manual checks (old way)

## See Also

- [Main Architecture Diagrams](./autonomous-fixing-diagrams.md)
- [Pre-Commit Hooks Strategy](../PRE_COMMIT_HOOKS.md)
- [Prompt Configuration](../../config/prompts.yaml)
