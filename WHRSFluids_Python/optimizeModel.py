#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo@uniovi.es
"""

import csv
from WHRS import WHRS
from WHRSOptimizer.WHRSskoptBayesian import WHRSskoptBayesian
import time
import matplotlib.pyplot as plt
import numpy as np

import warnings
warnings.filterwarnings("ignore")

# Shared params
from expertsModel import getFileModel
fileModel=getFileModel()


LoadRange=[60,100] # Modified Load range
LoadStep=5
LoadStepInterval=0.5 # numeric value in [0,0.5]. 
                     #If 0 no Load interval, 
                     #If 0.5 the intervals overlay all the values in LoadRange

# defaultFluid=1 # Cyclohexane
# defaultFluid=14 # NOVEC649
# defaultFluid=15 # SES36
fluids=[6,14,15] # R1233zd(E) NOVEC649 SES36

# Bayesian Optimizer params
nIter=20
initRandP=1
OptimizerName='Bayesian'


# Plot params
VNames1=['P_{ORC}\quad [kW]','CO_2\ reduction','EPC']
VRanges=[[350,550]          ,[14,18]          , [0.22,0.35]]
VYTics =[list(range(VRanges[0][0],VRanges[0][1]+1,25)),
         list(range(VRanges[1][0],VRanges[1][1]+1,1)),
         [0.22,0.24,0.26,0.28,0.30,0.32,0.34]]
colors=['#CC79A7','#000000','#009E73']
markers=['s','d','v']
markerfacecolor='white'
fillstyle='full'#'none')
fontsize=11#plt.rcParams['font.size']+1
plt.rcParams.update({'font.size': fontsize})
figTitle=False   # If the figures have title or not
figsize=[4.5,3]#[4.5,3.5]#[8/2.54,6.22/2.54]
def myLegend(): # How to define the legends of the plots
    plt.legend(labelspacing=0.1,frameon=False,borderpad=0)#,borderaxespad=0.2)



def getLoadInterval(Load,LoadStep,LoadStepInterval):
    return [Load-LoadStep*LoadStepInterval,Load+LoadStep*LoadStepInterval]


# # Influence variation
# InfluVar=list(range(0,100+1,5))

# Util for save to csv
def saveCSV(f,rows):
    for row in rows:
        first=True
        for v in row:
            if first:
                first=False
            else:
                f.write(',')
            f.write('{}'.format(v))
        f.write('\n')


#%% Load model and create a WHRS Object

def loadModel(fileModel):
    with open(fileModel,'rt') as f:
        csvReader=csv.reader(f,delimiter=',',quoting=csv.QUOTE_MINIMAL)
        header=csvReader.__next__()
        for ih in range(len(header)):
            header[ih]=header[ih].split(' ')[0]
        W=csvReader.__next__()
        inlfu=csvReader.__next__()
        DifMM=csvReader.__next__()
    for ii in range(len(W)):
        W[ii]=float(W[ii])
        inlfu[ii]=float(inlfu[ii])
        DifMM[ii]=float(DifMM[ii])
    print('Model read from {}: '.format(fileModel),end='')
    for ii in range(len(W)):
        print('{:+7.4f}*{}'.format(W[ii],header[ii]),end='')
    print('')
    print('Influence:')
    for ii in range(len(inlfu)):
        print('  {:16}:{:+6.2f}%'.format(header[ii],inlfu[ii]*100))
    print('')    
    return [W,inlfu,DifMM,header]

def evalModel(W,WHRS_cycle_output,CO2_red,EPC):
    return WHRS_cycle_output*W[0]+CO2_red*W[1]+EPC*W[2]

[W,Influ,DifMM,header]=loadModel(fileModel)
LoadMaxFluids=[] # LoadMax for each fluid
NamesFluids=[]
for defaultFluid in fluids:
    
    WHRSObj=WHRS(PropsSIStore='memory',verbose=1)
    WHRSObj.params_range['Load']=LoadRange
    WHRSObj.setDefaultFluid(defaultFluid)
    
    #%% Best for each variable
    VW1s=[[1,0,0],[0,1,0],[0,0,-1]]
             
    LoadMax1s=[]
    for iv in range(len(VW1s)):
        W1=VW1s[iv]
        VName=VNames1[iv]
        print('Optimizing: {}({})'.format(VName,W1))
        LoadMax=[]
        for Load in range(LoadRange[0],LoadRange[1]+1,LoadStep):
            print('\nOptimize for Load={}'.format(Load))
            # WHRSObj=WHRS()
            WHRSObj.params_range['Load']=getLoadInterval(Load,LoadStep,LoadStepInterval)
            opt=WHRSskoptBayesian(WHRSObj,W1,nIter=nIter,initRandP=initRandP)
            vals=opt.maximize()
            print('WHRS_cycle_output={:7.4f}'.format(opt.WHRS_cycle_output))
            print('CO2_red          ={:7.4f}'.format(opt.CO2_red))
            print('EPC              ={:7.4f}'.format(opt.EPC))
            print('RankEvaluation   ={:7.4f}'.format(opt.target))
            print('Opt. time        ={:5.2f}'.format(opt.getOptTime()))
            LoadMax.append(opt.getMaxValues())
        with open('{}_Best_{}.csv'.format(WHRSObj.getDefaultFluidCode(),VName),'wt') as f:
            saveCSV(f,[opt.getMaxNames()])
            saveCSV(f,LoadMax)
        LoadMax1s.append(LoadMax)
        
    #%% Plot Variable for its best and others' best
    X=list(range(LoadRange[0],LoadRange[1]+1,LoadStep))

    title='Fluid: {}'.format(WHRSObj.getDefaultFluidName())
    for ivr in range(len(VW1s)): # Variable to represent
        VName =VNames1[ivr]
        VRange=VRanges[ivr]
        VYTic=VYTics  [ivr]
        pos=8+ivr # Position in LoadMax
        plt.figure(figsize=[4.5,3.5],tight_layout=True)
        plt.ylabel(r'${}$'.format(VName))
        for ivo in range(len(VW1s)): # Variable to optimize
            LoadMax=LoadMax1s[ivo]
            Y=[]
            for il in range(len(LoadMax)):
                Y.append(LoadMax[il][pos])
            plt.plot(X,Y,label=r'Optimizing ${}$'.format(VNames1[ivo]),
                     color=colors[ivo],marker=markers[ivo],
                     markerfacecolor=markerfacecolor,
                     fillstyle=fillstyle)
        plt.xlabel('Load')
        plt.xticks(X)
        plt.yticks(VYTic)
        plt.ylim(bottom=VRange[0],top=VRange[1])
        myLegend()
        if figTitle:
            plt.title(title)
        plt.savefig('{}_{}_forLoadIntervalWhenOptimizingSelfAndOthers.pdf'.format(WHRSObj.getDefaultFluidCode(),VName))
        
    
    #%% Global Best
    # WHRSObj=WHRS(PropsSIStore='memory')
    WHRSObj.params_range['Load']=LoadRange
    opt=WHRSskoptBayesian(WHRSObj,W,nIter=nIter,initRandP=initRandP)
    opt.maximize()
    print('WHRS_cycle_output={:7.4f}'.format(opt.WHRS_cycle_output))
    print('CO2_red          ={:7.4f}'.format(opt.CO2_red))
    print('EPC              ={:7.4f}'.format(opt.EPC))
    print('RankEvaluation   ={:7.4f}'.format(opt.target))
    print('Opt. time        ={:5.2f}'.format(opt.getOptTime()))
    GlobalMax=opt.getMaxValues()
    names=opt.getMaxNames()
    for i in range(len(GlobalMax)):
        print('{:15}={}'.format(names[i],GlobalMax[i]))
    plt.figure(figsize=figsize)
    if figTitle:
        plt.title(title)
    opt.plot('{}_{}_GlobalMax.pdf'.format(WHRSObj.getDefaultFluidCode(),OptimizerName))
    
    #%% Change the Load using the Global Best
    LoadGlobal=[]
    for Load in range(LoadRange[0],LoadRange[1]+1,LoadStep):
        print('\nChange Load={}'.format(Load))
        (WHRS_cycle_output,CO2_red,EPC)=WHRSObj(Load,GlobalMax[1],GlobalMax[2],GlobalMax[3],GlobalMax[4],GlobalMax[5],GlobalMax[6],GlobalMax[7])
        print('WHRS_cycle_output={:7.4f}'.format(WHRS_cycle_output))
        print('CO2_red          ={:7.4f}'.format(CO2_red))
        print('EPC              ={:7.4f}'.format(EPC))
        LoadGlobal.append([Load,GlobalMax[1],GlobalMax[2],GlobalMax[3],GlobalMax[4],GlobalMax[5],GlobalMax[7],GlobalMax[7],WHRS_cycle_output,CO2_red,EPC,evalModel(W,WHRS_cycle_output,CO2_red,EPC),0])
    
    #%% Best for each Load
    LoadMax=[]
    for Load in range(LoadRange[0],LoadRange[1]+1,LoadStep):
        WHRSObj.params_range['Load']=getLoadInterval(Load,LoadStep,LoadStepInterval)
        opt=WHRSskoptBayesian(WHRSObj,W,nIter=nIter,initRandP=initRandP)
        vals=opt.maximize()
        print('WHRS_cycle_output={:7.4f}'.format(opt.WHRS_cycle_output))
        print('CO2_red          ={:7.4f}'.format(opt.CO2_red))
        print('EPC              ={:7.4f}'.format(opt.EPC))
        print('RankEvaluation   ={:7.4f}'.format(opt.target))
        print('Opt. time        ={:5.2f}'.format(opt.getOptTime()))
        LoadMax.append(opt.getMaxValues())
    LoadMaxFluids.append(LoadMax)
    NamesFluids.append(WHRSObj.getDefaultFluidName())
    #%% Save to csv

    fcsvOLName='{}_{}_OptimizeLoad.csv'.format(WHRSObj.getDefaultFluidCode(),OptimizerName)
    with open(fcsvOLName,'wt') as fcsv:
        saveCSV(fcsv,[opt.getMaxNames(),GlobalMax])
        saveCSV(fcsv,LoadMax)
    print('Writed optimizations'' output to {}'.format(fcsvOLName))
    
    fcsvCLName='{}_{}_ChangedLoad.csv'.format(WHRSObj.getDefaultFluidCode(),OptimizerName)
    with open(fcsvCLName,'wt') as fcsv:
        saveCSV(fcsv,[opt.getMaxNames(),GlobalMax])
        saveCSV(fcsv,LoadGlobal)
    print('Writed optimizations'' output to {}'.format(fcsvCLName))
    
    #%% Plot optimize Load
    
    def plotAxe(X,LoadMax,col,MName,title,xlabel='Load',Range=[None,None],VYTic=[None]):
        Y=np.array(LoadMax)[:,col].tolist()
        plt.plot(X,Y,color=colors[2],marker='o',markerfacecolor=markerfacecolor,fillstyle=fillstyle)
        plt.ylabel(r'${}$'.format(MName))
        plt.xlabel(r'${}$'.format(xlabel))
        if Range[0]!=None:
            plt.ylim(bottom=Range[0],top=Range[1])
        if VYTic[0]!=None:
            plt.yticks(VYTic)
            
        if figTitle:
            plt.title(title)
    
    
    X=list(range(LoadRange[0],LoadRange[1]+1,LoadStep))
    Xtics=list(range(LoadRange[0],LoadRange[1]+1,5))
    
    
    Names=[VNames1[0],VNames1[1],VNames1[2],'Rank\ value']
    fNames=['PO','CO2','EPC','Rank']
    Ranges=[VRanges[0],VRanges[1],VRanges[2],[None,None]]
    YTics=[VYTics[0],VYTics[1],VYTics[2],[None]]
    print(Ranges)
    for f in range(4):
        fig=plt.figure(figsize=figsize,tight_layout=True)    
        plt.xticks(Xtics)
        plotAxe(X,LoadMax, 8+f,Names[f],title,Range=Ranges[f],VYTic=YTics[f])
        fig.savefig('{}_{}_{}_Load.pdf'.format(WHRSObj.getDefaultFluidCode(),OptimizerName,fNames[f]),dpi=300)



#%% Compare outputs v1
outputs=[8,9,10,11]

# Plot all the values in a graph
for io in range(len(outputs)):
    o=outputs[io]
    name=Names[io]
    Range=Ranges[io]
    VYTic=YTics[io]
    
    
    fig=plt.figure(figsize=[4,3],tight_layout=True)  
    plt.xticks(Xtics)
    plt.ylabel(r'${}$'.format(name))
    plt.xlabel(r'${}$'.format('Load'))
    if Range[0]!=None:
        plt.ylim(bottom=Range[0],top=Range[1])
    if VYTic[0]!=None:
        plt.yticks(VYTic)
            
    for idf in range(len(fluids)):
        # fvalues=np.array(LoadMaxFluids[0])[:,8].tolist()
        fvalues=np.array(LoadMaxFluids[idf])[:,o].tolist()
        fluidName=NamesFluids[idf]  
        plt.plot(Xtics,fvalues,label=fluidName,
                 color=colors[idf],marker=markers[idf],
                 markerfacecolor=markerfacecolor,
                 fillstyle=fillstyle)
        

        
    myLegend()
    plt.savefig('{}_CompareFluids_{}.pdf'.format(OptimizerName,fNames[io]))

# Plot all the values-mean in a graph
for io in range(len(outputs)):
    o=outputs[io]
    name=Names[io]
    
    fig=plt.figure(figsize=figsize,tight_layout=True)  
    plt.xticks(Xtics)
    plt.ylabel(r'${}-mean$'.format(name))
    plt.xlabel(r'${}$'.format('Load'))
    vMean=[]
    for idf in range(len(fluids)):
        fvalues=np.array(LoadMaxFluids[idf])[:,o]
        if vMean==[]:
            vMean=fvalues
        else:
            vMean=vMean+fvalues
    vMean=vMean/len(fluids)
        
    for idf in range(len(fluids)):
        fvalues=np.array(LoadMaxFluids[idf])[:,o]-vMean
        fluidName=NamesFluids[idf]  
        plt.plot(Xtics,fvalues,label=fluidName,
                 color=colors[idf],marker=markers[idf],
                 markerfacecolor=markerfacecolor,
                 fillstyle=fillstyle)
    myLegend()
    plt.savefig('{}_CompareFluidsMean_{}.pdf'.format(OptimizerName,fNames[io]))


