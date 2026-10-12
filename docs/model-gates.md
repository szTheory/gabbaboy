# Model gates

Decision D-08 requires every behaviour that differs between the original Game Boy (DMG) and Game Boy
Color (CGB) to be declared in the source and in this table, and requires CI to prove the two agree.
`tests/scripts/verify-model-gates.py` reads `src/core/gabbaboy.c` and the table below; it never
writes to either.

## Tag grammar

A tag is a C comment:

```
MODEL: CLASS GATE-NN [GUARD=token] [basis=ref] [research:N] [expected-failure:reason] [-- prose]
```

- `CLASS` is `DMG_ONLY`, `CGB_ONLY`, `BOTH` or `UNKNOWN`.
- `ref` and `reason` are a bare word or a double-quoted string.
- A function tag sits in the comment block directly above the definition (no blank line between).
  A branch tag sits inside a function, directly above the guarded code.
- Table cells repeat the tag: class, `GUARD` token or `-`, and the resolution items in the order
  `basis=`, `research:`, `expected-failure:` (or `-` when there are none).

## Rules

1. **R1** Every top-level function definition carries a `MODEL` tag in the comment block above it.
2. **R2** Code tags and the table rows are a bijection by `GATE` id with identical class, guard and
   resolution. Rows are in ascending id order. An empty table or missing marker pair fails.
3. **R3** `UNKNOWN` needs `research:N` or `expected-failure:reason`. Under `--release` every
   `research:` `UNKNOWN` fails.
4. **R4** `DMG_ONLY` and `CGB_ONLY` need their `GUARD` token in code within the 12 code lines after
   the tag.
5. **R5** A `BOTH` tag without `basis=` fails if the 12 code lines after a branch tag (or the whole
   body of a function tag) contain a hazard token: a `0xFF40` to `0xFF7F` literal, `stopped`,
   `halt_bug`, `dma_`, `apu_power`, `ppu_mode`, or a `return 0xFFu`.

## GATE-00

`GATE-00` is the single shared id for model-neutral function tags (OQ4). It is accepted only with
class `BOTH` and a `basis=`, may repeat in code, and has exactly one row here. Every other `GATE-NN`
occurs exactly once in code and once in the table.

<!-- model-gates-begin -->
| Gate | Class | Guard | Resolution | Site | Note |
| --- | --- | --- | --- | --- | --- |
| GATE-00 | BOTH | - | basis="model-neutral function; see its branch gates" | any function | shared id for model-neutral function tags |
<!-- model-gates-end -->
