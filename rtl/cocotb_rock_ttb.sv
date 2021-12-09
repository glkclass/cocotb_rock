// CocoTB ROCK TTB.
// 1. Instantiate ROCK DUT, probes, waveform generation, timeout

`timescale 1ns/1ps

import "DPI-C" function string getenv(input string env_name);
import tb_util::timeout_sim;

module cocotb_rock_ttb ();

dtop dtop_dut ();

probes probes ();


//--------------------------------------------------------------------------
initial
    begin
        if ("1" == getenv("DUT_GENERATE_WAVE"))
            begin
                $shm_open("./sim_build");
                $shm_probe ("ACTFM");
            end

        $timeformat(-9, 3, " ns");
        timeout_sim(30ms, 1ms);
    end

//--------------------------------------------------------------------------
endmodule