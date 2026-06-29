# Contributing

Thanks for improving Mraprguild Termux Website Firewall.

Accepted contributions:

- Defensive security rule improvements
- Bug fixes
- Documentation improvements
- Termux compatibility fixes
- False positive reductions
- Logging improvements

Not accepted:

- Offensive attack tooling
- Bypass instructions
- Exploit automation against real targets
- Credential theft
- Malware behavior

## Local test

```bash
bash demo_backend.sh
bash start.sh
bash security_test.sh
```

## Pull request checklist

- Code is defensive
- README updated if needed
- Security tests pass
- No secrets/API keys included
- No harmful payload automation beyond local safe tests
