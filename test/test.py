# SPDX-License-Identifier: Apache-2.0
# cocotb test suite for tt_um_nilovski_shift4

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

MODE_HOLD = 0b00
MODE_SHR = 0b01
MODE_SHL = 0b10
MODE_LOAD = 0b11


def pack(mode, sin_r=0, sin_l=0, d=0):
    """Assemble ui_in from fields."""
    return (mode & 0x3) | ((sin_r & 1) << 2) | ((sin_l & 1) << 3) | ((d & 0xF) << 4)


def q_of(dut):
    return dut.uo_out.value.to_unsigned() & 0xF


async def reset(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)


async def step(dut):
    """One clock edge, then settle so flop outputs are stable to read."""
    await ClockCycles(dut.clk, 1)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_reset(dut):
    """Reset clears the register."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())  # 10 MHz
    # scribble state, then reset
    dut.rst_n.value = 1
    dut.ena.value = 1
    dut.uio_in.value = 0
    dut.ui_in.value = pack(MODE_LOAD, d=0xA)
    await ClockCycles(dut.clk, 2)
    await reset(dut)
    assert q_of(dut) == 0, f"expected 0 after reset, got {q_of(dut):#x}"


@cocotb.test()
async def test_parallel_load(dut):
    """Every value 0..15 loads correctly."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    await reset(dut)
    for val in range(16):
        dut.ui_in.value = pack(MODE_LOAD, d=val)
        await step(dut)
        assert q_of(dut) == val, f"load {val:#x}: got {q_of(dut):#x}"


@cocotb.test()
async def test_hold(dut):
    """Hold preserves state across many cycles."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    await reset(dut)
    dut.ui_in.value = pack(MODE_LOAD, d=0x9)
    await step(dut)
    dut.ui_in.value = pack(MODE_HOLD, sin_r=1, sin_l=1, d=0xF)  # noise on other pins
    await ClockCycles(dut.clk, 20)
    assert q_of(dut) == 0x9, f"hold lost state: got {q_of(dut):#x}"


@cocotb.test()
async def test_shift_right(dut):
    """Serial-in right: bit enters at Q[3], exits at Q[0] / uo_out[4]."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    await reset(dut)
    pattern = [1, 0, 1, 1]
    for bit in pattern:
        dut.ui_in.value = pack(MODE_SHR, sin_r=bit)
        await step(dut)
    # after shifting [1,0,1,1] MSB-first: q = {b3,b2,b1,b0} = {1,1,0,1}
    assert q_of(dut) == 0b1101, f"got {q_of(dut):#04b}"
    # serial-out right mirrors Q[0]
    assert (dut.uo_out.value.to_unsigned() >> 4) & 1 == q_of(dut) & 1


@cocotb.test()
async def test_shift_left(dut):
    """Serial-in left: bit enters at Q[0], exits at Q[3] / uo_out[5]."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    await reset(dut)
    for bit in [1, 1, 0, 1]:
        dut.ui_in.value = pack(MODE_SHL, sin_l=bit)
        await step(dut)
    # q = {b0,b1,b2,b3} shifted left each time -> q = 4'b1101
    assert q_of(dut) == 0b1101, f"got {q_of(dut):#04b}"
    assert (dut.uo_out.value.to_unsigned() >> 5) & 1 == (q_of(dut) >> 3) & 1


@cocotb.test()
async def test_randomized_golden_model(dut):
    """500 random cycles against a Python golden model."""
    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())
    await reset(dut)
    random.seed(1907)
    model = 0
    for _ in range(500):
        mode = random.randint(0, 3)
        sin_r = random.randint(0, 1)
        sin_l = random.randint(0, 1)
        d = random.randint(0, 15)
        dut.ui_in.value = pack(mode, sin_r, sin_l, d)
        await step(dut)
        if mode == MODE_SHR:
            model = (sin_r << 3) | (model >> 1)
        elif mode == MODE_SHL:
            model = ((model << 1) & 0xF) | sin_l
        elif mode == MODE_LOAD:
            model = d
        # MODE_HOLD: unchanged
        assert q_of(dut) == model, (
            f"mismatch: mode={mode:02b} dut={q_of(dut):#x} model={model:#x}"
        )
