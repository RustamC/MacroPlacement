########################## Details to use this script ##########################
# Author: Rustam Chochaev    email: rchochaev@gmail.com
# Based on gen_pb_or.tcl by Sayak Kundu (email: sakundu@ucsd.edu)
# Date: 12-27-2022
# This script converts LEF / DEF format to Placement format using OpenROAD.
# Follow the below steps to generate Placement file from LEF / DEF in the
# OpenROAD shell:
#   1. read_lef <tech lef>
#   2. read_lef <standard cell and macro lef one by one>
#   3. read_def <design def file>
#   4. source <This script file>
#   5. gen_plc <path of the output placement file>
################################################################################
#### Print the design header ####
proc print_header { fp } {
  set design [[ord::get_db_block] getName]
  set user [exec whoami]
  set date [exec date]
  set run_dir [exec pwd]
  set canvas_width [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] dx]]
  set canvas_height [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] dy]]

  puts $fp "# User: $user"
  puts $fp "# Date: $date"
  puts $fp "# Run area: $run_dir"
  puts $fp "# Block : $design"
  puts $fp "# FP bbox: {0.0 0.0} {$canvas_width $canvas_height}"
  ## Add dummy Column and Row info ##
  puts $fp "# Columns : 10  Rows : 10"
}

### Helper to convert Orientation format ###
proc get_orient { tmp_orient } {
  set orient "N"
  if { $tmp_orient == "R0"} {
    set orient "N"
  } elseif { $tmp_orient == "R180" } {
    set orient "S"
  } elseif { $tmp_orient == "R90" } {
    set orient "W"
  } elseif { $tmp_orient == "R270" } {
    set orient "E"
  } elseif { $tmp_orient == "MY" } {
    set oreint "FN"
  } elseif { $tmp_orient == "MX" } {
    set oreint "FS"
  } elseif { $tmp_orient == "MX90" } {
    set orient "FW" 
  } elseif { $tmp_orient == "MY90" } {
    set orient "FE"
  }
  return $orient
}

### Procedure Find Mid Point ###
proc find_mid_point_bbox { rect } {
  set xmin [$rect xMin]
  set ymin [$rect yMin]
  set dx [$rect getDX]
  set dy [$rect getDY]
  set pt_x [expr $xmin + $dx/2]
  set pt_y [expr $ymin + $dy/2]
  return [list $pt_x $pt_y]
}

#### Procedure to write Macros ####
proc write_node_macro { macro_idx macro_ptr fp } {

  set inst_box [$macro_ptr getBBox]
  set pts [find_mid_point_bbox $inst_box]
  set origin_x [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] xMin]]
  set origin_y [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] yMin]]

  ### Attribute: X ###
  set X [ord::dbu_to_microns [lindex $pts 0]]
  set X [expr $X - $origin_x]

  ### Attribute: Y ###
  set Y [ord::dbu_to_microns [lindex $pts 1]]
  set Y [expr $Y - $origin_y]
  
  ### Attribute: Orient ###
  set tmp_orient [${macro_ptr} getOrient]
  set orient [get_orient $tmp_orient]

  ### Attribute: isFixed ###
  # set isFixed [$macro_ptr isFixed]
  set isFixed 0

  ### Print ###
  puts $fp [format "%u %.2f %.2f %s %u" $macro_idx $X $Y $orient $isFixed]
}

#### Procedure to Write Std-cell ###
proc write_node_stdcell { inst_idx inst_ptr fp } {

  set inst_box [$inst_ptr getBBox]
  set pts [find_mid_point_bbox $inst_box]
  set origin_x [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] xMin]]
  set origin_y [ord::dbu_to_microns [[[ord::get_db_block] getCoreArea] yMin]]

  ### Attribute: X ###
  set X [ord::dbu_to_microns [lindex $pts 0]]
  set X [expr $X - $origin_x]

  ### Attribute: Y ###
  set Y [ord::dbu_to_microns [lindex $pts 1]]
  set Y [expr $Y - $origin_y]

  ### Attribute: Orient ###
  set tmp_orient [${inst_ptr} getOrient]
  set orient [get_orient $tmp_orient]

  ### Attribute: isFixed ###
  # set isFixed [$inst_ptr isFixed]
  set isFixed 0

  ### Print ###
  puts $fp [format "%u %.2f %.2f %s %u" $inst_idx $X $Y $orient $isFixed]
}

#### Generate protobuff format netlist ####
proc gen_plc { {file_name ""} } {
  set block [ord::get_db_block]
  set design [$block getName]
  
  if { $file_name != "" } {
    set out_file ${file_name}
  } else {
    set out_file "${design}.plc"
  }
  
  set plc_idx 0
  set fp [open $out_file w+]

  print_header $fp

  incr plc_idx [llength [$block getBTerms]]

  foreach inst_ptr [$block getInsts] {
    ### Macro ###
    if { [${inst_ptr} isBlock] } {
      write_node_macro $plc_idx $inst_ptr $fp
      incr plc_idx
      foreach macro_pin_ptr [${inst_ptr} getITerms] {
        if {[${macro_pin_ptr} isInputSignal] || [${macro_pin_ptr} isOutputSignal]} {
          incr plc_idx
        }
      }
    } elseif { [${inst_ptr} isCore] } {
      ### Standard Cells ###
      write_node_stdcell $plc_idx $inst_ptr $fp
      incr plc_idx
    }
  }
  close $fp
  puts "Output netlist: $out_file"
}
