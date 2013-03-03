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

# Check if the directory exists
if [ ! -d `dirname /tmp/$OUTPUTFILE.plot` ]; then
	mkdir -p `dirname /tmp/$OUTPUTFILE.plot`
fi

INPUTFILEDATA=$INPUTFILE

# Create plot file
echo "set term png  size 1800,600" > /tmp/$OUTPUTFILE.plot
echo "set out \"$OUTPUTFILE\"" >>    /tmp/$OUTPUTFILE.plot

echo "set style fill solid" >>       /tmp/$OUTPUTFILE.plot
echo "set yrange [0:3200]" >>        /tmp/$OUTPUTFILE.plot
# echo "set yrange [0:6000]" >>        /tmp/$OUTPUTFILE.plot
echo "set y2range [0:0.20]" >>       /tmp/$OUTPUTFILE.plot

echo "set xrange [$START:$END]" >>   /tmp/$OUTPUTFILE.plot

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
echo "plot \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$3)               w filledcurve y1=0       lc rgb \"#008000\" title \"Net metering power\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$5+\$3+\$7-\$4)   w filledcurve y1=0       lc rgb \"#FFFF00\" title \"Battery discharge\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$5+\$3-\$4)       w filledcurve y1=0       lc rgb \"#FF8000\" title \"Battery charge\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$5+\$3-\$4-\$6)   w filledcurve y1=0       lc rgb \"#804000\" title \"Brown power\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$3>\$11+\$10?\$11+\$10:\$3) w filledcurve y1=0       lc rgb \"#00FF00\" title \"Green power used\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$3)               w lines lw 1             lc rgb \"#00FF00\" title \"Green power available\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$8/10)            w lines lw 1             lc rgb \"#FF0000\" title \"Battery level\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$9)               w lines lw 1             lc rgb \"#800000\" title \"Workload\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$11)              w lines lw 2             lc rgb \"#000000\" title \"Executed load\", \\" >> /tmp/$OUTPUTFILE.plot
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$11+\$10)         w lines lw 1             lc rgb \"#555555\" title \"Executed load + Cooling\", \\" >> /tmp/$OUTPUTFILE.plot
# Debugging
# echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$4)              w lines lw 1             lc rgb \"#000000\" title \"Aux net neter\", \\" >> /tmp/$OUTPUTFILE.plot
# echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$12)              w lines lw 1             lc rgb \"#0000FF\" title \"Previous load\", \\" >> /tmp/$OUTPUTFILE.plot
# echo "\"$INPUTFILEDATA\" using (\$1/3600):(32000/10)          w lines lw 2             lc rgb \"#0000FF\" title \"Max battery\", \\" >> /tmp/$OUTPUTFILE.plot
# echo "\"$INPUTFILEDATA\" using (\$1/3600):(32000*0.8/10)      w lines lw 2             lc rgb \"#0000FF\" title \"Min battery\", \\" >> /tmp/$OUTPUTFILE.plot
# Final line
echo "\"$INPUTFILEDATA\" using (\$1/3600):(\$2)               w histeps axes x1y2 lw 3 lc rgb \"#0000FF\" title \"Brown energy price\"" >> /tmp/$OUTPUTFILE.plot
echo "" >> /tmp/$OUTPUTFILE.plot

# Backup lines
#$INPUTFILE using ($1/3600):($4)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FFFF00" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#$INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#$INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#$INPUTFILE using ($1/3600):($3-$4-$6)      w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \
#$INPUTFILE using ($1/3600):($3<=$11?$3:$3-$4-$6)       w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \

# Generate figure
gnuplot /tmp/$OUTPUTFILE.plot
