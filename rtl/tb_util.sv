// ROIC TTB. 
// Global TB param package.

`timescale 1ns/1ps

package tb_util;

    `define ADD_PROBE_WIRE(unit, prefix, probe) \
        wire ``prefix``probe; \
        assign ``prefix``probe = ``unit``.probe;

    `define ADD_PROBE_BUS(unit, prefix, probe, width) \
        wire [width-1:0] ``prefix``probe; \
        assign ``prefix``probe = ``unit``.probe;

    `define ADD_PROBE_UNPACKED_ARR(unit, prefix, probe, width, n)\
        generate\
            wire [width:0] ``prefix``probe[n];\
            for (ii = 0; ii < n; ii++)\
                begin\
                    assign ``prefix``probe[ii] = ``unit``.probe[ii*width +: width];\
                end\
        endgenerate


    `define PRINT_ARR(print_arr_foo) \
        $display("\n[LOG] [PRINT_ARR] Sizeof %s[] = %0d", `"print_arr_foo`", print_arr_foo.size()); \
        foreach (print_arr_foo[i]) \
            begin \
                if (0 == i%10) $write("[LOG] %s[%0d..]\t", `"print_arr_foo`", i); \
                $write("0x%0h ", print_arr_foo[i]); \
                if (9 == i%10) $display(); \
            end \
            $display("\n"); \


   `define PRINT_HASH_ARR(print_arr_foo) \
        $display("\n[LOG] [PRINT_HASH_ARR] Sizeof %s[] = %0d", `"print_arr_foo`", print_arr_foo.size()); \
        $write("[LOG] "); \
        foreach (print_arr_foo[i]) \
            $write("0x%0h: 0x%0h ", i, print_arr_foo[i]); \
        $display("\n"); \

    // Terminate simulation after given time period(to handle potential hang out)
    task automatic timeout_sim(input time tme, step=0);
        if (step == 0)
            begin
                #(tme);
            end
        else
            begin
                int n_iter = tme/step;
                for (int i = 0; i < n_iter; i++)
                    #(step) log_debug($sformatf("Sim checkpoint #%0d of %0d", i, n_iter));
            end

        $error("[LOG] Time off. Simulation terminated");
        $finish();
    endtask

    function void log_debug(string foo="", logic en = 1'b1);
        if (en)
            $display("%s\t\tat %0t", $sformatf("[LOG] %s", foo), $realtime);
    endfunction : log_debug

// CRC impl
    ////////////////////////////////////////////////////////////////////////////////
    // Copyright (C) 1999-2008 Easics NV.
    // This source file may be used and distributed without restriction
    // provided that this copyright statement is not removed from the file
    // and that any derivative work contains the original copyright notice
    // and the associated disclaimer.
    //
    // THIS SOURCE FILE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS
    // OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
    // WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
    //
    // Purpose : synthesizable CRC function
    //   * polynomial: x^12 + x^10 + x^7 + x^4 + x^3 + x^2 + x^1 + 1
    //   * data width: 12
    //
    // Info : tools@easics.be
    //        http://www.easics.com
    ////////////////////////////////////////////////////////////////////////////////

    // polynomial: x^12 + x^10 + x^7 + x^4 + x^3 + x^2 + x^1 + 1
    // data width: 12
    // convention: the first serial bit is D[11]
    function [11:0] nextCRC12_D12;
    input [11:0] Data;
    input [11:0] crc;
    reg [11:0] d;
    reg [11:0] c;
    reg [11:0] newcrc;
        begin
            d = Data;
            c = crc;
            newcrc[0] = d[11] ^ d[10] ^ d[6] ^ d[5] ^ d[4] ^ d[2] ^ d[0] ^ c[0] ^ c[2] ^ c[4] ^ c[5] ^ c[6] ^ c[10] ^ c[11];
            newcrc[1] = d[10] ^ d[7] ^ d[4] ^ d[3] ^ d[2] ^ d[1] ^ d[0] ^ c[0] ^ c[1] ^ c[2] ^ c[3] ^ c[4] ^ c[7] ^ c[10];
            newcrc[2] = d[10] ^ d[8] ^ d[6] ^ d[3] ^ d[1] ^ d[0] ^ c[0] ^ c[1] ^ c[3] ^ c[6] ^ c[8] ^ c[10];
            newcrc[3] = d[10] ^ d[9] ^ d[7] ^ d[6] ^ d[5] ^ d[1] ^ d[0] ^ c[0] ^ c[1] ^ c[5] ^ c[6] ^ c[7] ^ c[9] ^ c[10];
            newcrc[4] = d[8] ^ d[7] ^ d[5] ^ d[4] ^ d[1] ^ d[0] ^ c[0] ^ c[1] ^ c[4] ^ c[5] ^ c[7] ^ c[8];
            newcrc[5] = d[9] ^ d[8] ^ d[6] ^ d[5] ^ d[2] ^ d[1] ^ c[1] ^ c[2] ^ c[5] ^ c[6] ^ c[8] ^ c[9];
            newcrc[6] = d[10] ^ d[9] ^ d[7] ^ d[6] ^ d[3] ^ d[2] ^ c[2] ^ c[3] ^ c[6] ^ c[7] ^ c[9] ^ c[10];
            newcrc[7] = d[8] ^ d[7] ^ d[6] ^ d[5] ^ d[3] ^ d[2] ^ d[0] ^ c[0] ^ c[2] ^ c[3] ^ c[5] ^ c[6] ^ c[7] ^ c[8];
            newcrc[8] = d[9] ^ d[8] ^ d[7] ^ d[6] ^ d[4] ^ d[3] ^ d[1] ^ c[1] ^ c[3] ^ c[4] ^ c[6] ^ c[7] ^ c[8] ^ c[9];
            newcrc[9] = d[10] ^ d[9] ^ d[8] ^ d[7] ^ d[5] ^ d[4] ^ d[2] ^ c[2] ^ c[4] ^ c[5] ^ c[7] ^ c[8] ^ c[9] ^ c[10];
            newcrc[10] = d[9] ^ d[8] ^ d[4] ^ d[3] ^ d[2] ^ d[0] ^ c[0] ^ c[2] ^ c[3] ^ c[4] ^ c[8] ^ c[9];
            newcrc[11] = d[10] ^ d[9] ^ d[5] ^ d[4] ^ d[3] ^ d[1] ^ c[1] ^ c[3] ^ c[4] ^ c[5] ^ c[9] ^ c[10];
            nextCRC12_D12 = newcrc;
        end
    endfunction

endpackage : tb_util



