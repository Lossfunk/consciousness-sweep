# consciousness-sweep

This repository is an auditable, multi-agent literature-sweep package for asking whether awareness of a particular content **X** changes whether, or how well, a downstream cognitive process **Y** can use X.

The atomic scientific record is a **paper × experiment × X→Y comparison**. Independent agents follow the same frozen protocol, preserve every search and screening decision, and produce deterministic comparison-level outputs for later adjudication.

> **Current status:** pre-freeze. The protocol is not yet preregistered, required search configuration is deliberately incomplete, and the literature sweep should not be started yet.

## Intended use

1. Calibrate the remaining scientific and search decisions.
2. Freeze and version `PROTOCOL.md`, configuration, queries, seeds, schemas, and tools.
3. Run independent, isolated sweeps under separate `RUN_ID` values.
4. Record papers, comparisons, discoveries, missing texts, and decisions continuously.
5. Validate each checkpoint and regenerate derived outputs mechanically.
6. Compare and adjudicate independent runs only after they finish.

`PROTOCOL.md` defines the scientific rules. `AGENTS.md` defines execution, provenance, validation, and run-isolation rules.

## Commands

Install the small Python dependency set:

```sh
python -m pip install -r requirements.txt
```

Audit the current draft without authorizing a run:

```sh
python tools/preflight.py --mode pre-freeze
```

After the package is frozen, initialize or resume an independent run with:

```sh
python tools/init_run.py --run-id <RUN_ID> --run-mode start --agent-harness <HARNESS>
python tools/init_run.py --run-id <RUN_ID> --run-mode resume --agent-harness <HARNESS>
```

At checkpoints:

```sh
python tools/derive_outputs.py --run-id <RUN_ID>
python tools/validate_run.py --run-id <RUN_ID>
```

See `PROTOCOL.md` and `AGENTS.md` before executing a registered sweep.
