## How it works

This project is a 4-bit **universal shift register**, modeled on the classic
74194: a single 4-bit state register `Q` with four synchronous operating
modes selected by `MODE[1:0]`:

| MODE | Operation | Next state |
|------|-----------|------------|
| `00` | Hold | `Q <= Q` |
| `01` | Shift right | `Q <= {SER_IN_R, Q[3:1]}` |
| `10` | Shift left | `Q <= {Q[2:0], SER_IN_L}` |
| `11` | Parallel load | `Q <= D[3:0]` |

Reset (`rst_n`, active-low, synchronous) clears the register. `SER_OUT_R`
mirrors `Q[0]` and `SER_OUT_L` mirrors `Q[3]`, so multiple chips can be
chained into wider registers in either direction.

The design was verified two ways before submission:

1. **cocotb simulation** — six tests including 500 randomized cycles
   checked against a Python golden model (Icarus Verilog).
2. **Formal verification** — SymbiYosys with the z3 SMT solver. Bounded
   model checking plus an unbounded induction proof of five properties:
   reset behavior, hold, both shift directions, and parallel load. All
   properties are proven for all reachable states, not just simulated ones.

## How to test

1. Hold `rst_n` low for a few clocks, then release. `Q` (uo[3:0]) reads 0.
2. Set `MODE=11` and a value on `D[3:0]` (ui[7:4]); clock once. `Q` shows `D`.
3. Set `MODE=01` and toggle `SER_IN_R`; each clock shifts the register right,
   with the new bit entering at `Q[3]` and old bits exiting via `SER_OUT_R`.
4. Set `MODE=10` for the mirror-image left shift via `SER_IN_L`/`SER_OUT_L`.
5. Set `MODE=00`; the register holds its value regardless of other inputs.

On the demo board, map `Q[3:0]` to LEDs and drive the mode/data pins from
the DIP switches; single-step the clock to watch bits walk across the
register.

## External hardware

None required. LEDs on the output PMOD are convenient for visualizing `Q`.
