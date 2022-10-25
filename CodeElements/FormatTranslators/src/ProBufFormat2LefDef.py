import os
import sys
from typing import Text
sys.path.append('../../Plc_client')

from plc_client_os import PlacementCost

class ProBufFormat2LefDef(PlacementCost):

    def __init__(self,
                 lef_list,
                 def_file: str,
                 design: str,
                 netlist: str,
                 lib_list,
                 openroad_exe: str,
                 pb_file: Text,
                 macro_macro_x_spacing: float = 0.0,
                 macro_macro_y_spacing: float = 0.0,
                 tolerance: float = 0.05,
                 halo_width: float = 0.05) -> None:
        """
        Creates a ProBufFormat2LefDef object.
        """
        self.lef_list = lef_list
        self.def_file = def_file
        self.design = design
        self.netlist = netlist
        self.lib_list = lib_list
        self.openroad_exe = openroad_exe

        super(ProBufFormat2LefDef, self).__init__(pb_file, macro_macro_x_spacing, macro_macro_y_spacing)

    def convert_to_lefdef(self, plc_file):
        self.restore_placement(plc_file, False, True, False)

        file_name = 'update_def.tcl'
        line = 'set top_design ' + self.design + '\n'
        line += 'set netlist ' + self.netlist + '\n'
        line += 'set def_file ' + self.def_file + '\n'

        line += 'set ALL_LEFS "' + '\n'
        for lef in self.lef_list:
            line += '    ' + lef + '\n'
        line += '"\n'

        line += 'set LIB_BC "' + '\n'
        for lib in self.lib_list:
            line += '    ' + lib + '\n'
        line += '"\n'

        line += 'set site "unithd"' + '\n'

        line += 'foreach lef_file ${ALL_LEFS} {' + '\n'
        line += '    read_lef $lef_file' + '\n'
        line += '}' + '\n'

        line += 'foreach lib_file ${LIB_BC} {' + '\n'
        line += '    read_liberty $lib_file' + '\n'
        line += '}' + '\n'

        line += 'read_def ' + self.def_file + '\n'

        line += 'set plc_macro_list {}' + '\n'
        line += 'set plc_core_list {}' + '\n'
        
        # Here magic begins
        self.restore_placement(plc_pth=plc_file, ifInital=False, ifValidate=True, ifReadComment = False)
        for mod_idx in sorted(self.hard_macro_indices + self.soft_macro_indices + self.port_indices):
            # [node_index] [x] [y] [orientation] [fixed]
            mod = self.modules_w_pins[mod_idx]

            if mod.get_type() == "MACRO":
                h = mod.get_height()
                w = mod.get_width()
                x, y = mod.get_pos()

                x = x - w / 2
                y = y - h / 2
                orient = mod.get_orientation()

                line += 'lappend plc_macro_list [dict create name "{}" x {:g} y {:g} orient "{}"]'.format(mod.get_name(), x, y, orient) + '\n'

                #print("MACRO: {} {:g} {:g} {} {}".format(
                #    mod.get_name(),
                #    x, y,
                #    mod.get_orientation() if mod.get_orientation() else "-",
                #    "FIXED" if mod.get_fix_flag() else "NONFIXED"
                #))
            elif mod.get_type() == "STDCELL":

                h = mod.get_height()
                w = mod.get_width()
                x, y = mod.get_pos()

                x = x - w / 2
                y = y - h / 2
                orient = mod.get_orientation()
                line += 'lappend plc_core_list [dict create name "{}" x {:g} y {:g} orient "{}"]'.format(mod.get_name(), x, y, orient) + '\n'

                
                #print("STDCELL: {} {:g} {:g} {} {}".format(
                #    mod.get_name(),
                #    x, y,
                #    mod.get_orientation() if mod.get_orientation() else "-",
                #    "FIXED" if mod.get_fix_flag() else "NONFIXED"
                #))
        # Here magic ends

        line += 'set db [::ord::get_db]' + '\n'
        line += 'set dbu_per_uu [[$db getTech] getDbUnitsPerMicron]' + '\n'
        line += 'set block [[$db getChip] getBlock]' + '\n'
        line += 'set or_convertor [dict create N "R0" S "R180" W "R90" E "R270" FN "MY" FS "MX" FW "MX90" FE "MY90"]' + '\n'

        line += 'puts "DBU: $dbu_per_uu"' + '\n'

        line += 'foreach macro $plc_macro_list {' + '\n'
        line +='    set macro_name [dict get $macro name]' + '\n'
        line +='    set mx [expr int($dbu_per_uu * [dict get $macro x])]' + '\n'
        line +='    set my [expr int($dbu_per_uu * [dict get $macro y])]' + '\n'
        line +='    set morient [dict get $or_convertor [dict get $macro orient]]' + '\n'
        line +='    set the_macro [$block findInst "$macro_name"]' + '\n'
        line +='    if {$the_macro == "NULL"} {' + '\n'
        line +='        puts stderr "$macro_name is not found in LEF/DEF database!"' + '\n'
        line +='        exit 1' + '\n'
        line +='    }' + '\n'
        line +='    $the_macro setPlacementStatus PLACED' + '\n'
        line +='    $the_macro setLocation $mx $my' + '\n'
        line +='    $the_macro setLocationOrient $morient' + '\n'
        line +='    $the_macro setPlacementStatus FIRM' + '\n'
        line +='}' + '\n'

        line += 'foreach core $plc_core_list {' + '\n'
        line +='    set core_name [dict get $core name]' + '\n'
        line +='    set mx [expr int($dbu_per_uu * [dict get $core x])]' + '\n'
        line +='    set my [expr int($dbu_per_uu * [dict get $core y])]' + '\n'
        line +='    set morient [dict get $or_convertor [dict get $core orient]]' + '\n'
        line +='    set the_core [$block findInst "$core_name"]' + '\n'
        line +='    if {$the_core == "NULL"} {' + '\n'
        line +='        puts stderr "$core_name is not found in LEF/DEF database!"' + '\n'
        line +='        exit 1' + '\n'
        line +='    }' + '\n'
        line +='    $the_core setPlacementStatus PLACED' + '\n'
        line +='    $the_core setLocation $mx $my' + '\n'
        line +='    $the_core setLocationOrient $morient' + '\n'
        line +='    $the_core setPlacementStatus FIRM' + '\n'
        line +='}' + '\n'

        line += 'set def_outdir [file dirname ' + self.def_file + ']' + '\n'
        line += 'set def_filename [file rootname [file tail ' + self.def_file + ']]' + '\n'
        line += 'set def_file "$def_outdir/$def_filename.new.def"' + '\n'
        line += 'write_def ' + '$def_file' + '\n'
        line += 'exit\n'
        f = open(file_name, 'w')
        f.write(line)
        f.close()

        cmd = self.openroad_exe + ' ' + file_name
        os.system(cmd)

        cmd = "rm " + file_name
        os.system(cmd)



if __name__ == '__main__':
    design = ""
    lef_list = ["", ""]
    def_file = ""
    netlist = ""
    lib_list = [""]
    pb_file = ""
    plc_file = ""
    openroad_exe = "../utils/openroad"
    
    tolerance = 0.05
    halo_width = 0.05

    convertor = ProBufFormat2LefDef(lef_list, def_file, design, netlist, lib_list, openroad_exe, pb_file, tolerance, halo_width)
    convertor.convert_to_lefdef(plc_file)
