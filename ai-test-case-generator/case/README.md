# ai-test-case-generator case

Each run owns one task in `case/<case-name>/`. Task-level metadata is recorded once in `00-input.md` and the header of `04-test-cases.md`; confirmed test points expand into the actual `TC01`, `TC02`, and subsequent cases. The run also owns `04-historical-case-association.md`, and all shared implementation evidence is keyed to one commit when applicable.
