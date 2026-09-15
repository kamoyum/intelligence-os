# Developer Alpha Release Checklist

A release is not “good” because it has more features.

## Required before packaging
- [ ] compile passes
- [ ] full regression suite passes
- [ ] Kernel benchmark passes
- [ ] Red Team benchmark passes
- [ ] Development Governance benchmark passes
- [ ] version sync passes
- [ ] no secrets/DB/tokens/cache in archive
- [ ] capability registry updated
- [ ] new authority boundaries <= 1
- [ ] no unresolved privacy/safety regression

## Required before authority expansion
- [ ] explicit capability gate result reviewed
- [ ] rollback exists and was tested
- [ ] relevant Red Team cases exist
- [ ] observation window complete where required
- [ ] real-device evidence exists
- [ ] real-world evidence exists for external-write capabilities
- [ ] human authority model remains explicit

## Release language
Say what is **implemented**, what is **simulated**, what is **live-tested**, and what is **not verified**. Do not collapse these into “works.”
