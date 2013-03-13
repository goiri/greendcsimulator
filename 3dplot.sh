#!/bin/bash

# Usage: bash plot.bash $input $output

# Input/output files
INPUTFILE="3d.data"
OUTPUTFILE="results/3d.svg"
BASECOST=0

# Parse arguments
if [ $# -ge 2 ]; then
	INPUTFILE=$1
	OUTPUTFILE=$2
fi
if [ $# -ge 3 ]; then
	BASECOST=$3
fi

# Check if the directory exists
if [ ! -d `dirname /tmp/$OUTPUTFILE.plot` ]; then
	mkdir -p `dirname /tmp/$OUTPUTFILE.plot`
fi

# Input data
INPUTFILEDATA=$INPUTFILE
# Read the base cost
if [ $BASECOST != "0" ]; then
	BASECOST=`head -2 $INPUTFILEDATA | tail -1 | awk '{print $3}'`
fi

SCALE=1000000

# Create plot file
echo "set term svg  size 1280,800" > /tmp/$OUTPUTFILE.plot
echo "set out \"$OUTPUTFILE\"" >>    /tmp/$OUTPUTFILE.plot

echo "set dgrid3d" >> /tmp/$OUTPUTFILE.plot
echo "set lmargin 0" >> /tmp/$OUTPUTFILE.plot
echo "set rmargin 0" >> /tmp/$OUTPUTFILE.plot
echo "set tmargin 0" >> /tmp/$OUTPUTFILE.plot
echo "set bmargin 0" >> /tmp/$OUTPUTFILE.plot
echo "set zrange [0:]" >> /tmp/$OUTPUTFILE.plot
if [ $BASECOST != "0" ]; then
	echo "set zrange [0:$BASECOST/$SCALE]" >> /tmp/$OUTPUTFILE.plot
fi
echo "set xlabel \"Solar (MW)\"" >> /tmp/$OUTPUTFILE.plot
echo "set ylabel \"Battery (MWh)\" offset -5,0" >> /tmp/$OUTPUTFILE.plot
echo "set zlabel \"Total cost 12 years (M$)\" rotate by 90 right offset +12,0" >> /tmp/$OUTPUTFILE.plot
echo "set ticslevel 0" >> /tmp/$OUTPUTFILE.plot

echo  "splot \\" >> /tmp/$OUTPUTFILE.plot
i=3
LOCATIONS="Newark Quito"
for LOCATION in $LOCATIONS; do
	echo "\"$INPUTFILEDATA\" using (\$1/$SCALE):(\$2/$SCALE):(\$$i/$SCALE) w lines title \"Non-deferrable ($LOCATION)\",\\" >> /tmp/$OUTPUTFILE.plot
	let i=$i+1
	echo "\"$INPUTFILEDATA\" using (\$1/$SCALE):(\$2/$SCALE):(\$$i/$SCALE) w lines title \"Deferrable ($LOCATION)\",\\" >> /tmp/$OUTPUTFILE.plot
	let i=$i+1
done
# Line with the base cost
# echo "$BASECOST lc rgb \"#000000\" title \"Base cost\"">> /tmp/$OUTPUTFILE.plot
echo "0 lc rgb \"#000000\" title \"\"">> /tmp/$OUTPUTFILE.plot

# Generate figure
gnuplot /tmp/$OUTPUTFILE.plot
