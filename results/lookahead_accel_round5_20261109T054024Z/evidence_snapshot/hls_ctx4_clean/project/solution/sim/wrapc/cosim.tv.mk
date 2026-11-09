# ==============================================================
# Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
# Tool Version Limit: 2019.12
# Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
# ==============================================================
__SIM_FPO__ = 1
__SIM_MATHHLS__ = 1
__SIM_FFT__ = 1
__SIM_FIR__ = 1
__SIM_DDS__ = 1

override TARGET := $(if $(pc),cosim.pc.exe,cosim.tv.exe)

AUTOPILOT_ROOT := /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2
AUTOPILOT_MACH := lnx64

ifdef COSIM_M32
  AUTOPILOT_MACH := lnx32
  IFLAG += -m32
endif
ifdef AP_GCC_M32
  AUTOPILOT_MACH := Linux_x86
  IFLAG += -m32
endif
IFLAG += -fPIC
ifndef AP_GCC_PATH
  AP_GCC_PATH := /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/tps/lnx64/gcc-8.3.0/bin
endif
AUTOPILOT_TOOL = ${AUTOPILOT_ROOT}/${AUTOPILOT_MACH}/tools
AUTOPILOT_TECH = ${AUTOPILOT_ROOT}/common/technology
CCFLAG += -Werror=return-type
TOOLCHAIN += 

IFLAG += -g

IFLAG += -I "${AUTOPILOT_ROOT}/include"
IFLAG += -I "${AUTOPILOT_ROOT}/include/ap_sysc"
IFLAG += -I "${AUTOPILOT_ROOT}/common/technology/generic/SystemC"
IFLAG += -I "${AUTOPILOT_ROOT}/common/technology/generic/SystemC/AESL_FP_comp"
IFLAG += -I "${AUTOPILOT_ROOT}/common/technology/generic/SystemC/AESL_comp"
IFLAG += -I "${AUTOPILOT_ROOT}/${AUTOPILOT_MACH}/tools/auto_cc/include"
IFLAG += -I "/usr/include/x86_64-linux-gnu"
IFLAG += -D__VITIS_HLS__
IFLAG += -D__HLS_COSIM__
IFLAG += -D__SIM_FPO__
IFLAG += -D__SIM_FFT__
IFLAG += -D__SIM_FIR__
IFLAG += -D__SIM_DDS__
IFLAG += -D__DSP48E2__
IFLAG += $(pc)
IFLAG += -DUSE_BINARY_TV_FILE
IFLAG += -I/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects/results/lookahead_accel_round5_20261109T054024Z/hls_ctx4_clean/source_snapshot -std=c++14 -ffp-contract=off -fno-fast-math -DLA4_ENGINES=1 -DLA5_CONTEXTS=4 -DLA4_EARLY=1 -DLA4_DEPTH_ROW=2864 -DLA4_DEPTH_NODES=2864 -DLA4_DEPTH_EDGES=7928 -DLA4_DEPTH_COSTS=16 -DLA4_DEPTH_JOBS=16 -DLA4_DEPTH_CELLS=34352 -DLA4_DEPTH_OUTPUT=600 -DLA4_DEPTH_STATS=12 -Wno-unknown-pragmas
LFLAG += -lpthread
LFLAG += -L "${AUTOPILOT_ROOT}/${AUTOPILOT_MACH}/tools/clang-3.9-csynth/lib/clang/7.0.0/lib/linux" -lclang_rt.builtins-x86_64
IFLAG += -D__RTL_SIMULATION__
IFLAG += -D__xilinx_ip_top=
DFLAG += -DAESL_PIPELINE

include ./Makefile.rules

all : $(TARGET)

$(ObjDir)/tb5.cpp_pre.cpp.tb.o : tb5.cpp_pre.cpp.tb.cpp $(ObjDir)/.dir
	$(Echo) "   Compiling tb5.cpp_pre.cpp.tb.cpp" $(AVE_DIR_DLOG)
	$(Verb) $(CC) ${CCFLAG} ${TOOLCHAIN}  -fno-builtin-isinf -fno-builtin-isnan -c $(IFLAG) $(DFLAG) $< -o $@; \

$(ObjDir)/interleave5.cpp_pre.cpp.tb.o : interleave5.cpp_pre.cpp.tb.cpp $(ObjDir)/.dir
	$(Echo) "   Compiling interleave5.cpp_pre.cpp.tb.cpp" $(AVE_DIR_DLOG)
	$(Verb) $(CC) ${CCFLAG} ${TOOLCHAIN}  -fno-builtin-isinf -fno-builtin-isnan -c $(IFLAG) $(DFLAG) $< -o $@; \
