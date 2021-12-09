// probes. Contain probes to internal signals

import tb_util::*;

module probes ();
    genvar ii;
    bit  [255:0] 	wr_info, rd_info;
    int 			i;

    `define UNIT cocotb_rock_ttb.dtop_dut.u_spi_if
    `define PREFIX SPI_IF_
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_mce)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_sclk)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_cs_n)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_mosi)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, o_miso)


    `define UNIT cocotb_rock_ttb.dtop_dut.u_reg_file
    `define PREFIX REG_

    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_clk_125)

    `ADD_PROBE_BUS(`UNIT, `PREFIX, i_chip_addr, 3)

    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_spi_wr_req)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_spi_rd_req)
    `ADD_PROBE_BUS(`UNIT, `PREFIX, 	i_spi_addr, 8)
    `ADD_PROBE_BUS(`UNIT, `PREFIX, 	i_spi_wr_data, 16)
    `ADD_PROBE_BUS(`UNIT, `PREFIX, 	o_spi_rd_data, 16)
    `ADD_PROBE_WIRE(`UNIT, `PREFIX, i_en_wr_spi_error)
    `ADD_PROBE_BUS(`UNIT, `PREFIX, 	i_spi_error_type, 4)

endmodule

