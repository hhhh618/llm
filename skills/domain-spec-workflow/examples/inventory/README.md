# Inventory planning example

This is an illustrative draft, not an inventory implementation or acceptance record.
Confirm the domain meanings and scope before confirming its rules, US, AC or TC.
It demonstrates many-to-many US–AC–TC links. Automation, implementation links and
execution records are deliberately absent; no test has been claimed to pass.

From the repository root:

```sh
python3 skills/domain-spec-workflow/scripts/spec_workflow.py check skills/domain-spec-workflow/examples/inventory/spec.json --require-coverage
python3 skills/domain-spec-workflow/scripts/spec_workflow.py render skills/domain-spec-workflow/examples/inventory/spec.json --output /tmp/inventory-generated.md
```

The first command checks structural link coverage, not the meaning or correctness
of the inventory rules. The generated Markdown shows missing execution evidence.
It can be refreshed only when the existing output is this tool's generated view
for the same source file. Keep handwritten rationale in a separate file.

Start a real project with a new manifest file:

```sh
python3 skills/domain-spec-workflow/scripts/spec_workflow.py init specs/inventory/spec.json --purpose 'Clarify reservation ownership and behavior'
```

Add the scope, contexts, concepts and rules first. Empty story/case arrays are
valid while the domain is being clarified. When linking real code and artifacts,
use paths relative to an explicitly supplied `--project-root`. Execution records
must bind the exact spec digest, case revision and code commit. Their `command`
field is documentary and is never executed by this tool.
