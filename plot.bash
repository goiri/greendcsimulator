#!/bin/bash

# Usage: bash plot.bash $input $output $start $end

# Input/output files
INPUTFILE="results.log"
INPUTFILE="test.log"
OUTPUTFILE="plot.png"

# Plot time range
let START=6*30*24-4*24
let END=$START+4*24

# Parse arguments
if [ $# -ge 2 ]; then
	INPUTFILE=$1
	OUTPUTFILE=$2
fi
if [ $# -ge 4 ]; then
	START=$3
	END=$4
fi

echo "set term png  size 1800,600" > plot.plot
echo "set out \"$OUTPUTFILE\"" >> plot.plot

echo "set style fill solid" >> plot.plot
echo "set yrange [0:3500]" >> plot.plot
echo "set y2range [0:0.20]" >> plot.plot

echo "set xrange [$START:$END]" >> plot.plot

# 1 Time
# 2 BPrice
# 3 Green
# 4 NetMet
# 5 Brown
# 6 BatChar
# 7 BatDisc
# 8 BatLevel
# 9 Worload
# 10 Cooling
# 11 ExLoad
# 12 PrLoad
echo "plot \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$3)               w filledcurve y1=0       lc rgb \"#008000\" title \"Net metering power\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$5+\$3+\$7-\$4)   w filledcurve y1=0       lc rgb \"#FFFF00\" title \"Battery discharge\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$5+\$3-\$4)       w filledcurve y1=0       lc rgb \"#FF8000\" title \"Battery charge\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$5+\$3-\$4-\$6)   w filledcurve y1=0       lc rgb \"#804000\" title \"Brown power\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$3>\$11?\$11:\$3) w filledcurve y1=0       lc rgb \"#00FF00\" title \"Green power used\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$3)               w lines lw 1             lc rgb \"#00FF00\" title \"Green power available\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$8/10)            w lines lw 1             lc rgb \"#FF0000\" title \"Battery level\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$9)               w lines lw 1             lc rgb \"#800000\" title \"Workload\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$11)              w lines lw 1             lc rgb \"#000000\" title \"Executed load\", \\" >> plot.plot
echo "\"$INPUTFILE\" using (\$1/3600):(\$2)               w histeps axes x1y2 lw 3 lc rgb \"#0000FF\" title \"Brown energy price\"" >> plot.plot

# Backup lines
#$INPUTFILE using ($1/3600):($4)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FFFF00" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#$INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#$INPUTFILE using ($1/3600):($3-$4-$6)      w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \
#$INPUTFILE using ($1/3600):($3<=$11?$3:$3-$4-$6)       w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \

# Generate figure
gnuplot plot.plot
