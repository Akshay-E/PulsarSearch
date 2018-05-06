# A separate function to extract and plot
# heimdall candidate 
# This script is a modified version of the heimdall plotting scipt 'trans_freq_time.py' 
# 


import os,sys,math
import numpy as np
import glob
from itertools import chain
from os.path import basename
from itertools import tee, izip

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def plotParaCalc(snr,filter,dm,fl,fh,tint):
        #Extract block factor plot in seconds
        extimefact = 2.0

        # Total extract time Calc
        # Extract according to the DM delay    
        cmd = 'dmsmear -f %f -b %f -n 2048 -d ' % (fl+(fh-fl)/2,fh-fl) + str(dm) + " -q 2>&1 "
        p = os.popen(cmd)
        cand_band_smear = p.readline().strip()
        p.close()
        extime=extimefact*float(cand_band_smear)
        if extime < 1.0: extime = 1.0

        # Tbin calc
        # For Filter widths startting from 2^0 to 2^12=4096
        #widths = [2048,2048,2048,1024,1024,512,512,256,256,128,128,64,32]
        #tbin = widths[filter]
        bin_width = tint * (2 ** filter)
        tbin = int(extime / bin_width)
        if tbin < 16:
            tbin = 16

        #Fbin Calc
        fbin = int(round(math.pow(float(snr)/4.0,2)))
        if fbin < 2:
            fbin = 2
        fbin_base2 = int(round(math.log(fbin,2)))
        fbin = pow(2,fbin_base2)
        if fbin > 512:
            fbin = 512

        # Fraction of extraction to plot each time calc
        if tbin>1024:
            frac = np.linspace(0,1,np.ceil(tbin/1024.0))    
        else:
            frac = np.array([0,1])

        return tbin,fbin,extime,frac  

def extractPlotCand(fil_file,frb_cands,noplot,fl,fh,tint,kill_time_range,kill_chans,source_name):
        
        # Half of this time will be subtracted from the Heimdall candidate time
        extimeplot = 1.0

        if(noplot is not True):
                if(frb_cands.size >= 1):
                        if(frb_cands.size>1):
                                frb_cands = np.sort(frb_cands)
                                frb_cands[:] = frb_cands[::-1]
                        if(frb_cands.size==1): frb_cands = [frb_cands]
                        for indx,frb in enumerate(frb_cands):
                                time = frb['time']
                                dm = frb['dm']

                                tbin,fbin,extime,frac=plotParaCalc(frb['snr'],frb['filter'],dm,fl,fh,tint)
                                print tbin,fbin,extime,frac
        
                                stime = time-(extimeplot/2)
                                if(stime<0): stime = 0
                                #if(any(l<=stime<=u for (l,u) in kill_time_ranges)):
                                if(any(l<=time<=u for (l,u) in kill_time_range)):
                                        print "Candidate inside bad-time range"
                                else:
                                        if(indx<300):
                                                candname = '%04d' % (indx) + "_" + '%.3f' % (time) + "sec_DM" + '%.2f' % (dm) 
                                                cmd = "dspsr -cepoch=start -N uGMRTcand" + \
                                                        " -b " + str(tbin) +   \
                                                        " -S " + str(stime) +  \
                                                        " -c " + str(extime) + \
                                                        " -T " + str(extime) + \
                                                        " -D " + str(dm) + \
                                                        " -O " + candname + " -e ar " + \
                                                        fil_file + \
                                                        " -j \'F " + str(fbin) + "\'" 
                                                print cmd        
                                                os.system(cmd)                 
                                                # If no kill_chans, do an automatic smoothing
                                                temp = ""
                                                if kill_chans:
                                                    for k in kill_chans:
                                                        if(k!=2048): temp = temp +" "+str(k)
                                                        temp = "paz -z \"" + temp       + "\" -m *.ar"
                                                        print temp
                                                        os.system(temp)
                                                #os.system("paz -r -b -L -m *.ar")
                                                for i,j in pairwise(frac):
                                                    cmd = "psrplot -p F -j 'D' " + \
                                                          " -c x:unit=ms -c above:c='' " + \
                                                          " -c 'x:range=(%f,%f)' " % (i,j) + \
                                                          " -c 'freq:cmap:map=alien'" + \
                                                          " -D %s_%.2f.ps/cps %s.ar" % (candname,i,candname)
                                                    print cmd
                                                    os.system(cmd)
                                                    
                        cmd = "psjoin *sec*DM*.ps > %s_FRB_cand.ps" % (source_name)
                        os.system(cmd)
                        print cmd
                    
                else:
                        print "No candidate found"
                        return

if __name__ == "__main__":

    fil_file = sys.argv[1]
    frb_cands = np.loadtxt("FRBcand",dtype={'names': ('snr','time','samp_idx','dm','filter','prim_beam'),'formats': ('f4', 'f4', 'i4','f4','i4','i4')})
    fl = 301
    fh = 500
    noplot=0
    tint=0.000128
    kill_time_range=[]
    kill_chans=[]
    source_name="Fake"

    extractPlotCand(fil_file,frb_cands,noplot,fl,fh,tint,kill_time_range,kill_chans,source_name)
