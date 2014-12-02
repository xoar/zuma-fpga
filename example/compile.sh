# include base and VTR directories
. ../toolpaths
pwd

#move configuration files to python source folder
cp zuma_config.py $ZUMA_DIR/source/

#move to build folder to collect build related files
cd build
#generate vpr architecture and other files needes during build process
python $ZUMA_DIR/source/generate_buildfiles.py ./ $ZUMA_DIR/source/templates

#run odin, abc and vpr
$VTR_DIR/ODIN_II/odin_II.exe -V ../test.v
$VTR_DIR/abc_with_bb_support/abc < abccommands
sh vpr.sh

#run the zuma generation scripts
#python $ZUMA_DIR/source/run_zuma_all.py ./ ../generated/
python $ZUMA_DIR/source/zuma_build.py -graph_file 'rr_graph.echo' -blif_file 'abc_out.blif' -place_file 'place.p' -route_file 'route.r' -net_file 'netlist.net' -bit_file '../output.hex' -blif_out_file 'zuma_out.blif' -verilog_file '../ZUMA_custom_generated.v'

 echo 'cec abc_out.blif zuma_out.blif' | $VTR_DIR/abc_with_bb_support/abc