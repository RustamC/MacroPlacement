########################## Details to use this script ##########################
# Author: Rustam Chochaev    email: rchochaev@gmail.com
# Date: 11-22-2022
# This script creates DEF file from initial DEF and plc file using OpenROAD.
# Follow the below steps to create DEF file in the
# OpenROAD shell:
#   1. read_lef <tech lef>
#   2. read_lef <standard cell and macro lef one by one>
#   3. read_def <design def file>
#   4. source <This script file>
#   5. gen_updated_def <path of the output def>
################################################################################

### Procedure Find Mid Point ###
proc find_mid_point { rect } {
  set xmin [$rect xMin]
  set ymin [$rect yMin]
  set dx [$rect dx]
  set dy [$rect dy]
  set pt_x [expr $xmin + $dx/2]
  set pt_y [expr $ymin + $dy/2]
  return [list $pt_x $pt_y]
}

### Helper to convert Orientation format ###
proc get_orient { tmp_orient } {
  set orient "R0"
  if { $tmp_orient == "N"} {
    set orient "R0"
  } elseif { $tmp_orient == "S" } {
    set orient "R180"
  } elseif { $tmp_orient == "W" } {
    set orient "R90"
  } elseif { $tmp_orient == "E" } {
    set orient "R270"
  } elseif { $tmp_orient == "FN" } {
    set oreint "MY"
  } elseif { $tmp_orient == "FS" } {
    set oreint "MX"
  } elseif { $tmp_orient == "FW" } {
    set orient "MX90" 
  } elseif { $tmp_orient == "FE" } {
    set orient "MY90"
  }
  return $orient
}

#### Procedure to Update Macros ####
proc update_macro {macro_ptr} {
  set origin_x [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] xMin]]
  set origin_y [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] yMin]]

  ### Attribute: name ###
  set name [dict get $macro_ptr name]

  set macro [[ord::get_db_block] findInst "$name"]
  if {$macro == "NULL"} {
    puts stderr "$name is not found in LEF/DEF database!"
    exit 1
  }

  ### Attribute: X ###
  set x [dict get $macro_ptr x]
  set x [ord::microns_to_dbu [expr $x + $origin_x]]

  ### Attribute: Y ###
  set y [dict get $macro_ptr y]
  set y [ord::microns_to_dbu [expr $y + $origin_y]]

  ### Attribute: Orient ###
  set orient [get_orient [dict get $macro_ptr orient]]

  $macro setLocation $x $y
  $macro setLocationOrient $orient
  # element cannot be moved by a placer:
  $macro setPlacementStatus FIRM
}

#### Procedure to Update Std-cell ###
proc update_stdcell {inst_ptr} {
  set origin_x [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] xMin]]
  set origin_y [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] yMin]]

  ### Attribute: name ###
  set name [dict get $inst_ptr name]

  set inst [[ord::get_db_block] findInst "$name"]
  if {$inst == "NULL"} {
    puts stderr "$name is not found in LEF/DEF database!"
    exit 1
  }

  ### Attribute: X ###
  set x [dict get $inst_ptr x]
  set x [ord::microns_to_dbu [expr $x + $origin_x]]

  ### Attribute: Y ###
  set y [dict get $inst_ptr y]
  set y [ord::microns_to_dbu [expr $y + $origin_y]]

  ### Attribute: Orient ###
  set orient [get_orient [dict get $inst_ptr orient]]

  #$inst setPlacementStatus PLACED
  $inst setLocation $x $y
  $inst setLocationOrient $orient
}

#### Generate def format plc ####
proc gen_updated_def { {file_name ""} {plc_ports {}} {plc_cells {}} {plc_cells_pins {}} } {
  set db [ord::get_db]
  set block [ord::get_db_block]
  set design [$block getName]

  if { $file_name != "" } {
    set out_file ${file_name}
  } else {
    set out_file "${design}.ct.def"
  }

  foreach inst_ptr [$block getInsts] {
    ### Macro ###
    set the_inst [lsearch -index 1 -inline $plc_cells [${inst_ptr} getName]]
    
    if { $the_inst != "" } {
      if { [${inst_ptr} isBlock] } {
        update_macro $the_inst
      } elseif { [${inst_ptr} isCore] } {
        ### Standard Cells ###
        update_stdcell $the_inst
      }
    }
  }

  puts "Output def: $out_file"
  write_def $out_file
}
