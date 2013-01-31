INPUTFILE="results.log"
INPUTFILE="test.log"

set term png  size 1000,600
set out "plot.png"

set style fill solid
set yrange [0:3500]
set y2range [0:0.20]

# Plot time range
START = 6*30*24 - 4*24
END   = START + 4*24

set xrange [START:END]

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

plot \
INPUTFILE using ($1/3600):($3)            w filledcurve y1=0       lc rgb "#008000" title "Net metering power", \
INPUTFILE using ($1/3600):($5+$3+$7-$4)   w filledcurve y1=0       lc rgb "#FFFF00" title "Battery discharge", \
INPUTFILE using ($1/3600):($5+$3-$4)      w filledcurve y1=0       lc rgb "#FF8000" title "Battery charge", \
INPUTFILE using ($1/3600):($5+$3-$4-$6)   w filledcurve y1=0       lc rgb "#804000" title "Brown power", \
INPUTFILE using ($1/3600):($3>$11?$11:$3) w filledcurve y1=0       lc rgb "#00FF00" title "Green power used", \
INPUTFILE using ($1/3600):($3)            w lines lw 2             lc rgb "#00FF00" title "Green power available", \
INPUTFILE using ($1/3600):($8/10)         w lines lw 2             lc rgb "#FF0000" title "Battery level", \
INPUTFILE using ($1/3600):($9)            w lines lw 2             lc rgb "#800000" title "Workload", \
INPUTFILE using ($1/3600):($11)           w lines lw 2             lc rgb "#000000" title "Executed load", \
INPUTFILE using ($1/3600):($2)            w histeps axes x1y2 lw 3 lc rgb "#0000FF" title "Brown energy price"

# Backup lines
#INPUTFILE using ($1/3600):($4)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FFFF00" title "Auxiliary", \
#INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#INPUTFILE using ($1/3600):($5)           w lines lw 2       lc rgb "#FF0000" title "Auxiliary", \
#INPUTFILE using ($1/3600):($6)           w lines lw 2       lc rgb "#0000FF" title "Auxiliary 2", \

#INPUTFILE using ($1/3600):($3-$4-$6)      w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \
#INPUTFILE using ($1/3600):($3<=$11?$3:$3-$4-$6)       w filledcurve y1=0 lc rgb "#00FF00" title "Green power used", \

