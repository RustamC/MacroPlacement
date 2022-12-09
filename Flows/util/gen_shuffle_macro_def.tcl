# This script was written and developed by ABKGroup students at UCSD. However, the underlying commands and reports are copyrighted by Cadence. 
# We thank Cadence for granting permission to share our research to help promote and foster the next generation of innovators.
source lib_setup.tcl
source design_setup.tcl
set handoff_dir $::env(SYN_HANDOFF)

set netlist ${handoff_dir}/${DESIGN}.v
set sdc ${handoff_dir}/${DESIGN}.sdc 
source mmmc_setup.tcl

setMultiCpuUsage -localCpu 16
set util 0.3

# default settings
set init_pwr_net VDD
set init_gnd_net VSS

# default settings
set init_verilog "$netlist"
set init_design_netlisttype "Verilog"
set init_design_settop 1
set init_top_cell "$DESIGN"
set init_lef_file "$lefs"

# MCMM setup
init_design -setup {WC_VIEW} -hold {BC_VIEW}
set_power_analysis_mode -leakage_power_view WC_VIEW -dynamic_power_view WC_VIEW

set_interactive_constraint_modes {CON}
setAnalysisMode -reset
setAnalysisMode -analysisType onChipVariation -cppr both

clearGlobalNets
globalNetConnect VDD -type pgpin -pin VDD -inst * -override
globalNetConnect VSS -type pgpin -pin VSS -inst * -override
globalNetConnect VDD -type tiehi -inst * -override
globalNetConnect VSS -type tielo -inst * -override


setOptMode -powerEffort low -leakageToDynamicRatio 0.5
setGenerateViaMode -auto true
generateVias

# basic path groups
createBasicPathGroups -expanded

## Generate the floorplan ##

if {[info exist ::env(DEF_FILE)] && $::env(DEF_FILE) != ""} {
    defIn $::env(DEF_FILE) 
} else {
    defIn ${handoff_dir}/${DESIGN}.def
}

#### Unplace the standard cells ###
dbset [dbget top.insts.cell.subClass core -p2 ].pStatus unplaced

source ../../../../util/shuffle_macro.tcl
shuffle_macros $::env(SEED)

dbset [dbget top.insts.cell.subClass block -p2 ].pStatus fixed
defOut -floorplan ./${DESIGN}_fp_shuffled_macros.def

exit
