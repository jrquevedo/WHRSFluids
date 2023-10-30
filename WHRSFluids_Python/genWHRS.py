#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

import random
import csv
from sklearn.cluster import MiniBatchKMeans
from WHRS import WHRS

# Generation's parameters
LoadRange=[60,100] # Modified Load range
NO=500             # Number of output tuples
EP=50              # Number of pairs to be ordered by (expert) user
seed=2480          # Seed for random values

# WHRS Generator
rs=WHRS()
# prange=rs.params_range
rs.params_range['Load']=LoadRange

def betterOutput(tA,tB):
    """
    if tA is better than tB returns +1
    if tB is better that tB returns -1
    if is not possible to determine returns 0
    """
    # tuple: (Exergy_eff_WHRS,CO2_red,EPC)
    #         max            ,max    ,min
        
    if tA==tB:
        return 0
    
    if (tA[0]>=tB[0] and tA[1]>=tB[1] and tA[2]<=tB[2]): # tA is better than tB 
        return +1

    if (tA[0]<=tB[0] and tA[1]<=tB[1] and tA[2]>=tB[2]): # tB is better than tA 
        return -1

    return 0 # Can not decide

def uniformDist(RG,interval):
    return RG.uniform(interval[0],interval[1])

def beta22Dist(RG,interval):
    vrange=interval[1]-interval[0]
    return RG.betavariate(2,2)*vrange+interval[0]

def genRandomInput(RG,prange):
    Load         =beta22Dist(RG,prange['Load'])
    JW_pump      =uniformDist(RG,prange['JW_pump'])
    RC_Superheat =uniformDist(RG,prange['RC_Superheat'])
    RC_Subcool   =uniformDist(RG,prange['RC_Subcool'])
    ORC_Superheat=uniformDist(RG,prange['ORC_Superheat'])
    ORC_Subcool  =uniformDist(RG,prange['ORC_Subcool'])
    ORC_Pump     =uniformDist(RG,prange['ORC_Pump'])
    P_chamber    =uniformDist(RG,prange['P_chamber'])
    fluid        =RG.randrange(prange['Fluid'][1])
    
    return (Load,JW_pump,
     RC_Superheat,RC_Subcool,
     ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber,fluid)
#%% Generating output tuples
RG=random.Random()
RG.seed(seed)

rs=WHRS()
OTuples=[None]*NO
print('Generating {} output tuples'.format(NO))
# _BestRankVal=0
for it in range(NO):
    (Load,JW_pump,
     RC_Superheat,RC_Subcool,
     ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber,fluidId)=genRandomInput(RG,rs.params_range)
    rs.setDefaultFluid(fluidId)
    t=rs(Load,JW_pump,
          RC_Superheat,RC_Subcool,
          ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber)
    # _RankVal=t[0]*2.62320416454897+t[1]*1.13926897697577+t[2]*(-0.179630751811639)
    # if _RankVal>_BestRankVal:
        # print('Params',Load,JW_pump,
        #  RC_Superheat,RC_Subcool,
        #  ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber)
        # print('Outputs',t)
        # print('Eval',_RankVal)
        # _BestRankVal=_RankVal
    OTuples[it]=t
    if it % int(NO/10)==0 and it>0:
        print('{:3}% of {} output tuples'.format(int(it*100/NO),NO))
print('100% of {} output tuples'.format(NO))

#%% Generating pairs
PreOrderedPairs=[]
UserOrdererdPairs=[]
totalPairs=int((NO*(NO+1))/2)
oPairs=0
print('Ordening {} pairs'.format(totalPairs))
for it1 in range(0,NO-1):
    t1=OTuples[it1]
    for it2 in range(it1+1,NO):
        t2=OTuples[it2]
        comp=betterOutput(t1,t2)
        if comp==0:
            UserOrdererdPairs.append(t1+t2)
        elif comp==+1:
            PreOrderedPairs.append(t1+t2)
        else:
            PreOrderedPairs.append(t2+t1)
        if (oPairs % int(totalPairs/10))==0 and oPairs>0:
            print('{:3}% of {} pair of tuples. Ordered:{:5}  User:{:6}'
                  .format(int(oPairs*100/totalPairs),totalPairs,len(PreOrderedPairs),len(UserOrdererdPairs)))
        oPairs=oPairs+1    
print('100% of {} pair of tuples. Ordered:{:5}  User:{:6}'.format(totalPairs,len(PreOrderedPairs),len(UserOrdererdPairs)))

#%% Select EP pairs to user
ClusMeth=MiniBatchKMeans(n_clusters=EP,n_init=1,random_state=seed)
ClusMeth.fit(UserOrdererdPairs)
SelectedUserOrdererdPairs=ClusMeth.cluster_centers_
print('Selected {} pairs to be ordered by experts'.format(len(SelectedUserOrdererdPairs)))


#%% Write to csv files
header=['WHRS_cycle_output','CO2_red','EPC','WHRS_cycle_output','CO2_red','EPC']
def writeCSV(fName,pairs):
    with open(fName,'wt') as f:
        csvwriter = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(header)
        for pair in pairs:
            csvwriter.writerow(pair)
    print('Writed {} pairs to {}'.format(len(pairs),fName))
   
writeCSV('OrderedPairs/PreOrderedPairs_{}.csv'.format(seed),PreOrderedPairs)
writeCSV('OrderedPairs/UserOrderedPairs_{}.csv'.format(seed),SelectedUserOrdererdPairs)



