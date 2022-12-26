import os
import sys
import argparse
import json
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
        line += 'set plc_ports {}' + '\n'
        line += 'set plc_cells {}' + '\n'
        line += 'set plc_cells_pins {}' + '\n'
        
        # Here magic begins
        # for mod_idx in sorted(self.hard_macro_indices + self.soft_macro_indices + self.port_indices):
        self.restore_placement(plc_pth=plc_file, ifInital=False, ifValidate=True, ifReadComment = False)

        for mod_idx in sorted(self.hard_macro_indices + self.soft_macro_indices):
            # [name] [x] [y] [orientation]
            mod = self.modules_w_pins[mod_idx]
            mod_name = mod.get_name()

            h = mod.get_height()
            w = mod.get_width()
            x, y = mod.get_pos()
            orient = mod.get_orientation()

            line += 'lappend plc_cells [dict create name "{}" x {:g} y {:g} orient "{}"]'.format(mod_name, x, y, orient) + '\n'

            # Hard macro
            #if not self.is_node_soft_macro(mod_idx):
            #    if mod_name in self.hard_macros_to_inpins.keys():
            #        pin_names = self.hard_macros_to_inpins[mod_name]
            #    else:
            #        print("[ERROR UPDATE CONNECTION] MACRO pins not found")
            #        continue
            # Soft macro
            #elif self.is_node_soft_macro(mod_idx):
            #    if mod_name in self.soft_macros_to_inpins.keys():
            #        pin_names = self.soft_macros_to_inpins[mod_name]
            #    else:
            #        print("[ERROR UPDATE CONNECTION] macro pins not found")
            #        continue
            
            # [name] [x] [y] [x_offset] [y_offset]
            #for pin_name in pin_names:
            #    pin = self.modules_w_pins[self.mod_name_to_indices[pin_name]]
            #    x, y = pin.get_pos()
            #    x_offset, y_offset = pin.get_offset()
            #
            #    line += 'lappend plc_cells_pins [dict create name "{}" x "{}" y "{}" x_offset "{}" y_offset "{}"]'.format(pin_name, x, y, x_offset, y_offset) + '\n'

        #for mod_idx in sorted(self.port_indices):
        #    # [name] [x] [y] [orientation] [side]
        #    mod = self.modules_w_pins[mod_idx]
        #
        #    h = mod.get_height()
        #    w = mod.get_width()
        #    x, y = mod.get_pos()
        #    orient = mod.get_orientation()
        #    
        #    side = mod.side
        #    line += 'lappend plc_ports [dict create name "{}" x {:g} y {:g} orient "{}" side "{}"]'.format(mod.get_name(), x, y, orient, side) + '\n'

        # Here magic ends

        line += 'source gen_def.tcl' + '\n'
        line += 'gen_updated_def "" $plc_ports $plc_cells $plc_cells_pins' + '\n'
        line += 'exit' + '\n'

        with open(file_name, 'w') as f: 
            f.write(line)
            f.close()

        cmd = self.openroad_exe + ' ' + file_name
        os.system(cmd)

        #cmd = "rm " + file_name
        #os.system(cmd)

class LefDef2ProBufFormat:

    def __init__(self, lef_list, def_file, design, openroad_exe, net_size_threshold):
        self.lef_list = lef_list
        self.def_file = def_file
        self.design = design
        self.openroad_exe = openroad_exe
        self.net_size_threshold = net_size_threshold

    def convert_to_proto(self, pb_netlist):
        file_name = 'to_proto.tcl'
        line = ''
        line += 'set ALL_LEFS "' + '\n'
        for lef in self.lef_list:
            line += '    ' + lef + '\n'
        line += '"\n'

        line += 'set site "unithd"' + '\n'

        line += 'foreach lef_file ${ALL_LEFS} {' + '\n'
        line += '    read_lef $lef_file' + '\n'
        line += '}' + '\n'

        line += 'read_def ' + self.def_file + '\n'
        line += 'source gen_pb_or.tcl' + '\n'
        line += 'gen_pb_netlist ' + pb_netlist + '\n'
        line += 'exit'

        with open(file_name, 'w') as f: 
            f.write(line)
            f.close()

        cmd = self.openroad_exe + ' ' + file_name
        os.system(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Protobuf to DEF convertor")
    parser.add_argument('config', type=str)
    
    args = vars(parser.parse_args())

    with open(args['config'], 'r') as f:
        data = json.load(f)

    update_def = data['UPDATE_DEF']

    if update_def == True:
        design = data['DESIGN']
        netlist = data['NETLIST']
        def_file = data['DEF']
        lef_list = data['LEFS']
        lib_list = data['LIBS']
        pb_file = data['PB_FILE']
        plc_file = data['PLC_FILE']
        openroad_exe = data['OPENROAD_EXE']
    
        tolerance = 0.05
        halo_width = 0.05

        convertor = ProBufFormat2LefDef(lef_list, def_file, design, netlist, lib_list, openroad_exe, pb_file, tolerance, halo_width)
        convertor.convert_to_lefdef(plc_file)
    else:
        design = data['DESIGN']
        def_file = data['DEF']
        lef_list = data['LEFS']
        pb_file = data['PB_FILE']
        openroad_exe = data['OPENROAD_EXE']
        net_size_threshold = 300

        output_file = design + '.pb.txt'

        convertor = LefDef2ProBufFormat(lef_list, def_file, design, openroad_exe, net_size_threshold)
        convertor.convert_to_proto(pb_file)
