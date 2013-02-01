set term png  size 1800,600
set out "results/result-0-1600-1y-net0.40-fixedlow-delay-5.png"
set style fill solid
set yrange [0:3500]
set y2range [0:0.20]
set xrange [2928:3672]
plot \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($3)               w filledcurve y1=0       lc rgb "#008000" title "Net metering power", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($5+$3+$7-$4)   w filledcurve y1=0       lc rgb "#FFFF00" title "Battery discharge", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($5+$3-$4)       w filledcurve y1=0       lc rgb "#FF8000" title "Battery charge", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($5+$3-$4-$6)   w filledcurve y1=0       lc rgb "#804000" title "Brown power", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($3>$11?$11:$3) w filledcurve y1=0       lc rgb "#00FF00" title "Green power used", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($3)               w lines lw 1             lc rgb "#00FF00" title "Green power available", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($8/10)            w lines lw 1             lc rgb "#FF0000" title "Battery level", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($9)               w lines lw 1             lc rgb "#800000" title "Workload", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($11)              w lines lw 1             lc rgb "#000000" title "Executed load", \
"results/result-0-1600-1y-net0.40-fixedlow-delay.log" using ($1/3600):($2)               w histeps axes x1y2 lw 3 lc rgb "#0000FF" title "Brown energy price"
