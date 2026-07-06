/*
 * tt_um_nilovski_shift4 — 4-bit universal shift register (74194-style)
 * Author: Şahpar Nil Özer
 * Target: Tiny Tapeout TTSKY26c · SkyWater Sky130
 *
 * Pin map
 *   ui_in[1:0]  mode   00=hold  01=shift right  10=shift left  11=load
 *   ui_in[2]    serial input for shift-right (enters at Q[3])
 *   ui_in[3]    serial input for shift-left  (enters at Q[0])
 *   ui_in[7:4]  parallel load data D[3:0]
 *
 *   uo_out[3:0] register contents Q[3:0]
 *   uo_out[4]   serial out, right (Q[0])
 *   uo_out[5]   serial out, left  (Q[3])
 *   uo_out[7:6] unused (0)
 *
 * Reset: rst_n, synchronous, active-low, clears Q to 0.
 */

`default_nettype none

module tt_um_nilovski_shift4 (
    input  wire [7:0] ui_in,    // dedicated inputs
    output wire [7:0] uo_out,   // dedicated outputs
    input  wire [7:0] uio_in,   // bidirectional: input path
    output wire [7:0] uio_out,  // bidirectional: output path
    output wire [7:0] uio_oe,   // bidirectional: enable (1=output)
    input  wire       ena,      // high when design is powered/selected
    input  wire       clk,
    input  wire       rst_n     // active-low reset
);

    // ---- decode inputs -------------------------------------------------
    wire [1:0] mode  = ui_in[1:0];
    wire       sin_r = ui_in[2];      // shift-right serial in
    wire       sin_l = ui_in[3];      // shift-left  serial in
    wire [3:0] d     = ui_in[7:4];    // parallel load data

    localparam [1:0] MODE_HOLD = 2'b00,
                     MODE_SHR  = 2'b01,
                     MODE_SHL  = 2'b10,
                     MODE_LOAD = 2'b11;

    // ---- state ---------------------------------------------------------
    reg [3:0] q;

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= 4'b0000;
        end else begin
            case (mode)
                MODE_HOLD: q <= q;
                MODE_SHR:  q <= {sin_r, q[3:1]};   // MSB in, toward LSB
                MODE_SHL:  q <= {q[2:0], sin_l};   // LSB in, toward MSB
                MODE_LOAD: q <= d;
            endcase
        end
    end

    // ---- drive outputs ---------------------------------------------------
    assign uo_out[3:0] = q;
    assign uo_out[4]   = q[0];   // serial out for right-shift chaining
    assign uo_out[5]   = q[3];   // serial out for left-shift chaining
    assign uo_out[7:6] = 2'b00;

    // unused bidirectional pins: tie off
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // silence unused-signal lint
    wire _unused = &{ena, uio_in, 1'b0};

    // ---- formal properties ----------------------------------------------
`ifdef FORMAL
    reg f_past_valid = 1'b0;
    always @(posedge clk) f_past_valid <= 1'b1;

    always @(posedge clk) begin
        if (f_past_valid) begin
            // P1: synchronous reset clears the register
            if (!$past(rst_n))
                assert (q == 4'b0000);

            if ($past(rst_n)) begin
                // P2: hold preserves state
                if ($past(mode) == MODE_HOLD)
                    assert (q == $past(q));

                // P3: shift right — serial bit enters at MSB
                if ($past(mode) == MODE_SHR)
                    assert (q == {$past(sin_r), $past(q[3:1])});

                // P4: shift left — serial bit enters at LSB
                if ($past(mode) == MODE_SHL)
                    assert (q == {$past(q[2:0]), $past(sin_l)});

                // P5: parallel load
                if ($past(mode) == MODE_LOAD)
                    assert (q == $past(d));
            end
        end
    end

    // outputs are pure functions of state
    always @(*) begin
        assert (uo_out[3:0] == q);
        assert (uo_out[4] == q[0]);
        assert (uo_out[5] == q[3]);
        assert (uio_oe == 8'b0);
    end

    // cover: reachability of an all-ones register via left shifts
    always @(posedge clk)
        cover (q == 4'b1111 && $past(mode) == MODE_SHL);
`endif

endmodule
