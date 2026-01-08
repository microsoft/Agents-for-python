# Sample: Data-Driven Testing

Example of YAML-based declarative testing.

## Files

- `greetings.yaml` - Greeting test scenarios
- `questions.yaml` - Q&A test scenarios  
- `error_handling.yaml` - Error case scenarios

## Running

### Single File

```bash
aclip --env_path ../../.env ddt greetings.yaml -v
```

### All Files

```bash
#!/bin/bash
for file in *.yaml; do
  echo "Running: $file"
  aclip --env_path ../../.env ddt "$file" -v
done
```

## What This Sample Shows

✅ YAML test file structure  
✅ Different assertion types  
✅ Multiple test scenarios  
✅ Error handling patterns  
✅ CLI execution  

## Customization

Edit YAML files to match your agent's:
- Input messages
- Expected responses
- Different assertion types

## See Also

- [DATA_DRIVEN_TESTING.md](../../guides/DATA_DRIVEN_TESTING.md)
- [CLI_TOOLS.md](../../guides/CLI_TOOLS.md)
