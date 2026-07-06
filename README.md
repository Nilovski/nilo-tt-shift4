![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# 4-bit Universal Shift Register — Tiny Tapeout TTSKY26c

A 74194-style universal shift register designed in Verilog, carried through the
full RTL-to-GDSII flow (OpenLane/LibreLane, SkyWater Sky130), and submitted for
fabrication on the Tiny Tapeout TTSKY26c shuttle.

**[📄 Datasheet page](docs/info.md) · [🔬 Results & GDS viewer](https://nilovski.github.io/nilo-tt-shift4/)**

## What it does

A single 4-bit register `Q` with four synchronous modes selected by `MODE[1:0]`:

| MODE | Operation     | Next state              |
|------|---------------|-------------------------|
| `00` | Hold          | `Q <= Q`                |
| `01` | Shift right   | `Q <= {SER_IN_R, Q[3:1]}` |
| `10` | Shift left    | `Q <= {Q[2:0], SER_IN_L}` |
| `11` | Parallel load | `Q <= D[3:0]`           |

Serial-out pins (`SER_OUT_R` = `Q[0]`, `SER_OUT_L` = `Q[3]`) allow chaining
multiple chips into wider registers in either direction. Full pinout is in
[`info.yaml`](info.yaml).

## Verification

The design was verified two independent ways before tapeout:

- **Simulation** — a six-test [cocotb](https://www.cocotb.org/) suite
  (Icarus Verilog) covering reset, all four modes, and 500 randomized
  cycles checked against a Python golden model. The same suite runs
  gate-level against the post-synthesis netlist in CI.
- **Formal verification** — [SymbiYosys](https://github.com/YosysHQ/sby)
  with the Z3 SMT solver: bounded model checking plus an **unbounded
  induction proof** of five properties (reset, hold, both shift
  directions, parallel load). The properties hold for all reachable
  states, not just simulated cases. See [`formal/shift4.sby`](formal/shift4.sby)
  and the `FORMAL` block in [`src/project.v`](src/project.v).

Run them locally:

```bash
cd test && make                    # simulation
cd formal && sby -f shift4.sby     # formal (requires yosys, sby, z3)
```

## About Tiny Tapeout

[Tiny Tapeout](https://tinytapeout.com) is an educational project that makes
it easier and cheaper than ever to get digital and analog designs manufactured
on a real chip.

---

*Şahpar Nil Özer · Vanderbilt University ECE*
