ABC_EXE := vtr/build/abc/abc
ODIN_EXE := vtr/build/ODIN_II/odin_II
VPR := vtr/build/vpr/vpr
YOSYS_EXE := yosys/yosys

EXECUTABLES := $(ABC_EXE) $(ODIN_EXE) $(VPR) $(YOSYS_EXE)

all: $(EXECUTABLES)
default: $(EXECUTABLES)

abc: $(ABC_EXE)
odin: $(ODIN_EXE)
vpr: $(VPR)
yosys: $(YOSYS_EXE)

.PHONY: clean
clean:
	cd vtr   && make clean || echo "vtr not cleaned, or already clean"
	cd yosys && make clean || echo "yosys not cleaned, or already clean"

# Submodules have to be fetched
vtr/Makefile yosys/Makefile:
	cd $$(git rev-parse --show-toplevel) && git submodule update --init --recursive

# # ABC itself, depends on VTR
# $(ABC_EXE): vtr

# # Odin II itself, depends on VTR
# $(ODIN_EXE): vtr

# # VPR itself, depends on VTR
# $(VPR_EXE): vtr

# Complete VTR flow, depends on being downloaded
$(ABC_EXE) $(ODIN_EXE) $(VPR_EXE) vtr: vtr/Makefile
	@echo "Building VTR"
	cd vtr && make
	@echo "Done building VTR"

# Yosys itself, depends on being downloaded
$(YOSYS_EXE): yosys/Makefile
	@echo "Building Yosys"
	cd yosys && make config-gcc && make
	@echo "Done building Yosys"

