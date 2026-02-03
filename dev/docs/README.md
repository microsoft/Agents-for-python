# Microsoft Agents Testing Framework - Complete Documentation

Welcome to the comprehensive documentation for the Microsoft Agents Testing Framework!

## 📚 Documentation Structure

### Main Index
- **[TESTING_FRAMEWORK.md](./TESTING_FRAMEWORK.md)** - Start here! Overview, features, and navigation

### 📖 Detailed Guides (11 Guides)

| Guide | Purpose | Audience |
|-------|---------|----------|
| [QUICK_START.md](./guides/QUICK_START.md) | Get started in 5 minutes | New users |
| [INSTALLATION.md](./guides/INSTALLATION.md) | Complete setup instructions | All users |
| [CORE_COMPONENTS.md](./guides/CORE_COMPONENTS.md) | Understand the framework architecture | Developers |
| [INTEGRATION_TESTING.md](./guides/INTEGRATION_TESTING.md) | Write comprehensive tests | Test engineers |
| [DATA_DRIVEN_TESTING.md](./guides/DATA_DRIVEN_TESTING.md) | YAML-based declarative testing | All levels |
| [CLI_TOOLS.md](./guides/CLI_TOOLS.md) | Command-line tools guide | DevOps/Testers |
| [ASSERTIONS.md](./guides/ASSERTIONS.md) | Advanced assertions | Developers |
| [AUTHENTICATION.md](./guides/AUTHENTICATION.md) | Azure Bot Service auth | Developers |
| [PERFORMANCE_TESTING.md](./guides/PERFORMANCE_TESTING.md) | Benchmarking and load testing | Performance engineers |
| [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md) | Testing patterns and recommendations | Experienced users |
| [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md) | Common issues and solutions | All users |
| [API_REFERENCE.md](./guides/API_REFERENCE.md) | Complete API documentation | Developers |

### 🎯 Sample Projects (4 Samples)

| Sample | Purpose | Files |
|--------|---------|-------|
| [basic_agent_testing](./samples/basic_agent_testing/) | Simple test examples | test_basic_agent.py |
| [data_driven_testing](./samples/data_driven_testing/) | YAML test scenarios | *.yaml files |
| [advanced_patterns](./samples/advanced_patterns/) | Real-world patterns | test_advanced_patterns.py, conftest.py |
| [performance_benchmarking](./samples/performance_benchmarking/) | Load testing examples | payload_*.json files |

## 🚀 Getting Started

### Path 1: New User (5 minutes)
1. Read: [QUICK_START.md](./guides/QUICK_START.md)
2. Try: [basic_agent_testing sample](./samples/basic_agent_testing/)
3. Run: `pytest test_basic_agent.py -v`

### Path 2: Setup for Team (15 minutes)
1. Read: [INSTALLATION.md](./guides/INSTALLATION.md)
2. Follow: Project structure setup
3. Create: `.env` file
4. Try: First test

### Path 3: Deep Dive (1-2 hours)
1. [CORE_COMPONENTS.md](./guides/CORE_COMPONENTS.md) - Understand architecture
2. [INTEGRATION_TESTING.md](./guides/INTEGRATION_TESTING.md) - Write tests
3. [DATA_DRIVEN_TESTING.md](./guides/DATA_DRIVEN_TESTING.md) - YAML tests
4. [PERFORMANCE_TESTING.md](./guides/PERFORMANCE_TESTING.md) - Benchmarking
5. [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md) - Patterns

## 📋 Quick Reference

### Most Common Tasks

**Writing your first test?**
→ [QUICK_START.md](./guides/QUICK_START.md) (5 min) + [basic_agent_testing sample](./samples/basic_agent_testing/)

**Setting up in a project?**
→ [INSTALLATION.md](./guides/INSTALLATION.md) (10 min)

**Need integration tests?**
→ [INTEGRATION_TESTING.md](./guides/INTEGRATION_TESTING.md)

**Prefer YAML tests?**
→ [DATA_DRIVEN_TESTING.md](./guides/DATA_DRIVEN_TESTING.md)

**Running CLI tools?**
→ [CLI_TOOLS.md](./guides/CLI_TOOLS.md)

**Debugging tests?**
→ [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)

**Looking up API?**
→ [API_REFERENCE.md](./guides/API_REFERENCE.md)

**Need advanced patterns?**
→ [advanced_patterns sample](./samples/advanced_patterns/)

**Performance testing?**
→ [PERFORMANCE_TESTING.md](./guides/PERFORMANCE_TESTING.md)

## 🗂️ File Organization

```
docs/
├── TESTING_FRAMEWORK.md              # Main index (START HERE!)
├── guides/                            # 12 detailed guides
│   ├── QUICK_START.md
│   ├── INSTALLATION.md
│   ├── CORE_COMPONENTS.md
│   ├── INTEGRATION_TESTING.md
│   ├── DATA_DRIVEN_TESTING.md
│   ├── CLI_TOOLS.md
│   ├── ASSERTIONS.md
│   ├── AUTHENTICATION.md
│   ├── PERFORMANCE_TESTING.md
│   ├── BEST_PRACTICES.md
│   ├── TROUBLESHOOTING.md
│   └── API_REFERENCE.md
└── samples/                           # 4 sample projects
    ├── basic_agent_testing/          # Simple examples
    ├── data_driven_testing/          # YAML scenarios
    ├── advanced_patterns/            # Real-world patterns
    └── performance_benchmarking/     # Load testing
```

## 📚 Documentation by Topic

### Getting Started
- [Quick Start](./guides/QUICK_START.md)
- [Installation](./guides/INSTALLATION.md)

### Core Concepts
- [Core Components](./guides/CORE_COMPONENTS.md)
- [Integration Testing](./guides/INTEGRATION_TESTING.md)
- [API Reference](./guides/API_REFERENCE.md)

### Test Types
- [Integration Testing](./guides/INTEGRATION_TESTING.md)
- [Data-Driven Testing](./guides/DATA_DRIVEN_TESTING.md)
- [Performance Testing](./guides/PERFORMANCE_TESTING.md)

### Tools & Features
- [CLI Tools](./guides/CLI_TOOLS.md)
- [Assertions](./guides/ASSERTIONS.md)
- [Authentication](./guides/AUTHENTICATION.md)

### Best Practices
- [Best Practices](./guides/BEST_PRACTICES.md)
- [Troubleshooting](./guides/TROUBLESHOOTING.md)

### Examples
- [Basic Agent Testing](./samples/basic_agent_testing/)
- [Data-Driven Testing](./samples/data_driven_testing/)
- [Advanced Patterns](./samples/advanced_patterns/)
- [Performance Benchmarking](./samples/performance_benchmarking/)

## 🎓 Learning Paths

### For Test Engineers
1. [QUICK_START.md](./guides/QUICK_START.md)
2. [INTEGRATION_TESTING.md](./guides/INTEGRATION_TESTING.md)
3. [basic_agent_testing sample](./samples/basic_agent_testing/)
4. [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md)

### For QA/Non-Developers
1. [QUICK_START.md](./guides/QUICK_START.md)
2. [DATA_DRIVEN_TESTING.md](./guides/DATA_DRIVEN_TESTING.md)
3. [data_driven_testing sample](./samples/data_driven_testing/)
4. [CLI_TOOLS.md](./guides/CLI_TOOLS.md)

### For DevOps/Automation
1. [INSTALLATION.md](./guides/INSTALLATION.md)
2. [CLI_TOOLS.md](./guides/CLI_TOOLS.md)
3. [PERFORMANCE_TESTING.md](./guides/PERFORMANCE_TESTING.md)
4. [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)

### For Architects/Developers
1. [CORE_COMPONENTS.md](./guides/CORE_COMPONENTS.md)
2. [INTEGRATION_TESTING.md](./guides/INTEGRATION_TESTING.md)
3. [advanced_patterns sample](./samples/advanced_patterns/)
4. [API_REFERENCE.md](./guides/API_REFERENCE.md)
5. [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md)

## 📌 Key Topics at a Glance

### Setting Up
- Environment variables
- Installation
- Configuration
- Project structure

### Writing Tests
- Integration tests (Python)
- Data-driven tests (YAML)
- Custom fixtures
- Assertions

### Running Tests
- With pytest
- With CLI tools
- With performance benchmarks
- CI/CD integration

### Troubleshooting
- Connection issues
- Configuration problems
- Test failures
- Performance issues

## 🔗 Cross-References

Each guide includes "Related Guides" and "Next Steps" sections for easy navigation.

### Common Transitions

**After QUICK_START**
→ [INTEGRATION_TESTING](./guides/INTEGRATION_TESTING.md) or [DATA_DRIVEN_TESTING](./guides/DATA_DRIVEN_TESTING.md)

**After INSTALLATION**
→ [QUICK_START](./guides/QUICK_START.md) or [CORE_COMPONENTS](./guides/CORE_COMPONENTS.md)

**After INTEGRATION_TESTING**
→ [BEST_PRACTICES](./guides/BEST_PRACTICES.md) or [PERFORMANCE_TESTING](./guides/PERFORMANCE_TESTING.md)

**When Stuck**
→ [TROUBLESHOOTING](./guides/TROUBLESHOOTING.md) or [BEST_PRACTICES](./guides/BEST_PRACTICES.md)

## 💡 Pro Tips

### Quick Reference Cards
- **CLI Commands**: See [CLI_TOOLS.md](./guides/CLI_TOOLS.md#summary)
- **Assertion Types**: See [DATA_DRIVEN_TESTING.md](./guides/DATA_DRIVEN_TESTING.md#assertion-types)
- **API Classes**: See [API_REFERENCE.md](./guides/API_REFERENCE.md#classes)

### Real Examples
- **Python**: [advanced_patterns sample](./samples/advanced_patterns/test_advanced_patterns.py)
- **YAML**: [data_driven_testing samples](./samples/data_driven_testing/)
- **Config**: [advanced_patterns conftest.py](./samples/advanced_patterns/conftest.py)

### Checklists
- **Setup**: [INSTALLATION.md](./guides/INSTALLATION.md#file-structure-setup)
- **First Test**: [QUICK_START.md](./guides/QUICK_START.md#step-3-create-your-first-test-2-minutes)
- **Best Practices**: [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md#summary-of-best-practices)

## 📞 Getting Help

### By Problem Type

**Installation Issues**
→ [INSTALLATION.md](./guides/INSTALLATION.md#troubleshooting-installation) or [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md#installation-problems)

**Test Failures**
→ [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md) or [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md#debugging-tips)

**Slow Tests**
→ [PERFORMANCE_TESTING.md](./guides/PERFORMANCE_TESTING.md) or [TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md#performance-optimization)

**API Questions**
→ [API_REFERENCE.md](./guides/API_REFERENCE.md) or [CORE_COMPONENTS.md](./guides/CORE_COMPONENTS.md)

**Design Questions**
→ [BEST_PRACTICES.md](./guides/BEST_PRACTICES.md) or [advanced_patterns sample](./samples/advanced_patterns/)

## 🎯 Start Here!

**New to the framework?**
→ Open [TESTING_FRAMEWORK.md](./TESTING_FRAMEWORK.md)

**Want to write your first test?**
→ Go to [QUICK_START.md](./guides/QUICK_START.md)

**Setting up in your project?**
→ Follow [INSTALLATION.md](./guides/INSTALLATION.md)

**Need to understand the architecture?**
→ Study [CORE_COMPONENTS.md](./guides/CORE_COMPONENTS.md)

## 📖 Documentation Statistics

- **Total Pages**: 13 comprehensive guides + 4 sample projects
- **Code Examples**: 100+ working examples
- **YAML Samples**: 4 sample test suites
- **Coverage**: Installation, Core Concepts, Testing Patterns, CLI, Performance, Troubleshooting, API Reference

---

**Happy Testing! 🚀**

*For the most up-to-date information, always check the main [TESTING_FRAMEWORK.md](./TESTING_FRAMEWORK.md) file.*
