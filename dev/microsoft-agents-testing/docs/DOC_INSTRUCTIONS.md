# Documentation Standards for Microsoft Agents Testing Framework

This document defines the criteria, structure, and guidelines for creating documentation for each core module in the Microsoft Agents Testing Framework. All module READMEs should follow these standards to ensure consistency and usability for developers testing their agents with the M365 Agents SDK.

---

## Target Audience

**Primary audience**: Developers using the M365 Agents SDK who need to test their agents.

Assume the reader:
- Has working knowledge of Python and async programming
- Is familiar with the M365 Agents SDK basics
- Wants to quickly understand how to use the testing framework
- May need deeper understanding for advanced use cases

---

## Documentation Scope

### In Scope
- Public API: Classes, functions, and constants exposed via `__init__.py`
- Usage patterns and best practices
- Integration with other modules in the framework
- Practical examples and recipes
- Known limitations and potential improvements

### Out of Scope
- Internal implementation details
- Private classes, methods, or helper functions (prefixed with `_`)
- Low-level mechanics that may change between versions

---

## Required Document Structure

Each module's `README.md` must follow this structure:

### 1. Title and Overview
```markdown
# Module Name: Short Description

A 2-3 sentence description of what the module does and its primary use case.
```

**Criteria:**
- Title should be the module name followed by a colon and a concise descriptor
- Overview should answer: "What does this module help me do?"
- Avoid jargon; keep it accessible

---

### 2. Installation / Import
```markdown
## Installation

\```python
from microsoft_agents.testing.module_name import (
    PublicClass,
    public_function,
)
\```
```

**Criteria:**
- Show the exact import statement users need
- Only include public API exports
- Group related imports logically

---

### 3. Quick Start
```markdown
## Quick Start

A minimal, runnable example that demonstrates the core functionality.
```

**Criteria:**
- Should be copy-paste runnable (or nearly so)
- Demonstrates the "happy path" use case
- Takes no more than 10-15 lines of code
- Includes brief inline comments explaining key steps
- Should hook the reader by showing immediate value

**Example pattern:**
```markdown
## Quick Start

\```python
from microsoft_agents.testing.check import Check

# Define a check that validates response contains expected text
check = Check(
    name="greeting_check",
    condition=lambda response: "Hello" in response.text,
)

# Run the check against a response
result = check.evaluate(agent_response)
print(result.passed)  # True or False
\```
```

---

### 4. Core Concepts
```markdown
## Core Concepts

### Concept Name

Explanation of the concept with examples.
```

**Criteria:**
- Break down the module into 3-5 key concepts
- Each concept gets its own subsection
- Start with the simplest concept, build to more complex
- Use progressive examples that build on each other
- Include code snippets for each concept

---

### 5. API Reference
```markdown
## API Reference

### `ClassName`

Description of the class and its purpose.

#### Constructor

\```python
ClassName(param1: type, param2: type = default) -> ClassName
\```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param1` | `str` | Yes | Description |
| `param2` | `int` | No | Description (default: `0`) |

#### Methods

##### `method_name()`

\```python
def method_name(self, arg: type) -> ReturnType
\```

Description of what the method does.
```

**Criteria:**
- Document all public classes, functions, and constants
- Use consistent formatting for signatures
- Include type hints
- Use tables for parameters when there are 2+ parameters
- Document return types and possible exceptions
- Group related APIs together

---

### 6. Integration with Other Modules
```markdown
## Integration with Other Modules

### Using with `other_module`

Explanation of how this module works with other parts of the framework.
```

**Criteria:**
- Explain how the module connects to other framework modules
- Show practical examples of combined usage
- Link to the other module's documentation
- Focus on common integration patterns

**Required integrations to document (where applicable):**

| Module | Should Reference |
|--------|------------------|
| `agent_test` | `check`, `underscore`, `utils` |
| `check` | `underscore`, `agent_test` |
| `underscore` | `check`, `pipe` usage in checks |
| `utils` | `agent_test`, `check` |
| `cli` | All modules it orchestrates |

---

### 7. Common Patterns and Recipes
```markdown
## Common Patterns and Recipes

### Pattern Name

**Use case**: When you need to...

\```python
# Implementation
\```
```

**Criteria:**
- Include 3-5 practical patterns per module
- Each pattern should solve a real testing scenario
- Name patterns descriptively (e.g., "Validating Multiple Response Fields")
- Include a "Use case" line explaining when to use the pattern
- Can reference actual test files for more complex examples:
  ```markdown
  > See [`tests/check/test_check.py`](../tests/check/test_check.py) for more examples.
  ```

---

### 8. Limitations and Future Improvements
```markdown
## Limitations

- Current limitation 1
- Current limitation 2

## Potential Improvements

- Possible enhancement 1
- Possible enhancement 2
```

**Criteria:**
- Be honest about current limitations
- Frame limitations constructively (what it doesn't do, not what's "broken")
- List potential improvements as future possibilities, not promises
- This section helps set user expectations

---

### 9. See Also (Optional)
```markdown
## See Also

- [Related Module](../related_module/README.md) - Brief description
- [External Resource](https://example.com) - Brief description
```

---

## Writing Style Guidelines

### Tone
- Professional but approachable
- Direct and concise
- Avoid marketing language ("powerful", "revolutionary", "blazing fast")

### Code Examples
- Use realistic variable names (not `foo`, `bar`, `x`)
- Include output comments where helpful: `# → expected_output`
- Keep examples focused on one concept at a time
- Prefer complete, runnable snippets over fragments

### Formatting
- Use fenced code blocks with language hints (` ```python `)
- Use tables for structured data (parameters, options)
- Use horizontal rules (`---`) to separate major sections
- Use admonitions sparingly for important notes:
  ```markdown
  > **Note**: Important information here.
  
  > **Warning**: Critical warning here.
  ```

### Terminology
- Use consistent terms across all docs:
  | Preferred | Avoid |
  |-----------|-------|
  | "check" | "assertion", "validation" |
  | "agent response" | "bot response", "reply" |
  | "scenario" | "test case" (when referring to AgentScenario) |
  | "evaluate" | "run", "execute" (for checks) |

---

## Module-Specific Guidance

### `agent_test` Module
Focus areas:
- Setting up test scenarios
- Configuring agent connections
- Running tests and collecting responses
- Async patterns for agent testing

### `check` Module
Focus areas:
- Defining validation conditions
- Composing checks
- Quantifiers (all, any, none patterns)
- Using with underscore expressions

### `underscore` Module
Focus areas:
- Placeholder expressions as lambda alternatives
- Building readable check conditions
- Chaining and composition
- Integration with the check module

### `utils` Module
Focus areas:
- Data normalization utilities
- Template patterns for test data
- Model utilities for working with agent responses

### `cli` Module
Focus areas:
- Command-line interface usage
- Configuration options
- Running tests from command line
- Output formats and reporting

---

## Documentation Checklist

Before finalizing a module's documentation, verify:

- [ ] Title clearly describes the module's purpose
- [ ] Quick Start is under 15 lines and runnable
- [ ] All public API items are documented
- [ ] At least 3 common patterns/recipes included
- [ ] Integration with related modules explained
- [ ] Limitations section is present and honest
- [ ] No internal/private APIs are documented
- [ ] Code examples use realistic names and scenarios
- [ ] All code blocks have language hints
- [ ] Links to other module docs are correct
- [ ] Terminology is consistent with this guide

---

## File Naming and Location

```
docs/
├── DOC_INSTRUCTIONS.md      # This file
├── agent_test/
│   └── README.md            # agent_test module documentation
├── check/
│   └── README.md            # check module documentation
├── underscore/
│   └── README.md            # underscore module documentation
├── utils/
│   └── README.md            # utils module documentation
└── cli/
    └── README.md            # cli module documentation
```

---

## Template

A blank template following this structure is available below. Copy and adapt for each module.

```markdown
# [Module Name]: [Short Description]

[2-3 sentence overview of the module's purpose and primary use case.]

## Installation

\```python
from microsoft_agents.testing.[module] import (
    # Public exports
)
\```

## Quick Start

\```python
# Minimal example demonstrating core functionality
\```

## Core Concepts

### [Concept 1]

[Explanation with examples]

### [Concept 2]

[Explanation with examples]

### [Concept 3]

[Explanation with examples]

## API Reference

### `ClassName`

[Description]

#### Constructor

\```python
ClassName(param: type) -> ClassName
\```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|

#### Methods

##### `method_name()`

[Description and signature]

## Integration with Other Modules

### Using with `[other_module]`

[Explanation and examples]

## Common Patterns and Recipes

### [Pattern 1 Name]

**Use case**: [When to use this pattern]

\```python
# Implementation
\```

### [Pattern 2 Name]

**Use case**: [When to use this pattern]

\```python
# Implementation
\```

## Limitations

- [Limitation 1]
- [Limitation 2]

## Potential Improvements

- [Improvement 1]
- [Improvement 2]

## See Also

- [Related documentation links]
```