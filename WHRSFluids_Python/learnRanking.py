#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

import csv
import numpy as np
from Rank import linearRank,multiBatchAUC
from sklearn.model_selection import KFold
from sklearn.svm import LinearSVC
from sklearn.model_selection import GridSearchCV

import matplotlib.pyplot as plt


from expertsModel import getExperts,getFileModel


# WithPreOrdered=True
WithPreOrdered=False

experts=getExperts()
fileModel=getFileModel()

def readOrderedPairs(fcsvName,initialQId=1):
    X=[]
    Y=[]
    cQId=initialQId
    with open(fcsvName,'rt') as f:
        csvreader=csv.reader(f, delimiter=',')
        header=csvreader.__next__()
        User=len(header)==7
        for row in csvreader:
            for ir in range(6):
                row[ir]=float(row[ir])
            if User:
                if row[6]=='X':
                    continue   # Skip pairs marked as X
            X.append(row[0:3]) # Tuple A
            X.append(row[3:6]) # Tuple B
            if User:
                vA=1 if row[6]=='A' else 0 # Depends on the user answer
            else:
                vA=1 # Tuple A is allways better than Tuple B
            Y.append([vA,cQId])
            Y.append([1-vA,cQId])
            
            cQId=cQId+1
    print('Read {} pairs from {}'.format(int(len(X)/2),fcsvName))
    return [X,Y,cQId,header]

def calculateInfluence(X,W):
    M=np.mean(X,0) # Mean of each attribute
    DifMM=abs(X-np.array(M)).mean(0)  # Mean of the distance 1 between mean and value
    Influ=DifMM*abs(np.array(W)) 
    print(Influ)
    Influ=Influ/sum(Influ)# Get the proportion
    return [Influ,DifMM]

# Experts' preferences
cQId=1
Xe=[]
Ye=[]
for e in experts:
    [X1,Y1,cQId,header]=readOrderedPairs('OrderedPairs/UserOrderedPairs_{}_esp_{}.csv'.format(e[1],e[0]),cQId)
    Xe=Xe+X1
    Ye=Ye+Y1
# [X1,Y1,cQId,header]=readOrderedPairs('OrderedPairs/UserOrderedPairs_2480_esp_NOELIA.csv',cQId)

# All Experts Pairs
NEPrefs=len(Xe)

# Reading pairs
[XPreAll,YPreAll,cQId,header]=readOrderedPairs('OrderedPairs/PreOrderedPairs_2480.csv')

# NEPrefs2=int(len(XPreAll)/4)*2
NEPrefs2=NEPrefs

XPre=XPreAll[:NEPrefs2]
YPre=YPreAll[:NEPrefs2]
XPreTe=XPreAll[NEPrefs2:]
YPreTe=YPreAll[NEPrefs2:]


if WithPreOrdered:
    ChartSuf='WithPreOrdered'
else:
    XPre=[]
    YPre=[]
    ChartSuf='WithOUTPreOrdered'

# All pairs
X=XPre+Xe
Y=YPre+Ye

# Learn and Overwrite
mySVC=LinearSVC(C=1,fit_intercept=False,max_iter=100000)
baseLearn=GridSearchCV(mySVC,{'C':[0.0001, 0.001, 0.01, 0.1, 1, 10, 100,1000,10000]},verbose=0)
# baseLearn=GridSearchCV(mySVC,{'C':[ 0.00001]},verbose=0)

RankSys=linearRank(LinealClass=baseLearn,verbose=0)
print('Learning from {} pairs'.format(int(len(X)/2)))
RankSys.fit(X,Y)
Model=RankSys.LinealClass.best_estimator_
W=Model.coef_[0].tolist()
print('Rank Model:{}'.format(W))
P=RankSys.predict(Xe)

[Influ,DifMM]=calculateInfluence(X,W) # Calculte the influence

# Plot Influence and sign
colors=['#3070B8','#E3B445','#EA3323']
sw=0.5
Xbar=['$CO_2$ reduc.','$\Psi_E$$_X$','EPC']
InfluPlot=[Influ[1],Influ[0],Influ[2]]
WPlot=[W[1],W[0],W[2]]
signs=(np.sign(WPlot)*sw).tolist()
fig = plt.figure(figsize=[4,3],dpi=300,layout='tight')
plt.bar(Xbar,InfluPlot,color=colors[0])
plt.text(-0.35+0,-0.10,'{:5.2f}%'.format(Influ[1]*100),color=colors[0])
plt.text(-0.35+1,-0.10,'{:5.2f}%'.format(Influ[0]*100),color=colors[0])
plt.text(-0.35+2,-0.10,'{:5.2f}%'.format(Influ[2]*100),color=colors[0])
ax1=fig.get_axes()[0]
ax1.set_yticks([0,0.25,0.5,0.75,1],labels=['0%','25%','50%','75%','100%'],color=colors[0])
plt.ylabel('RI',color=colors[0])
plt.ylim(-0.75,1)
ax2=ax1.twinx()
ax2.plot(signs,'d',color=colors[2])
ax2.set_yticks([-1*sw,+1*sw],['Negative','Positive'],color=colors[2])
plt.ylim([-0.75,1])
plt.ylabel('Sign',color=colors[2])
plt.title('$rf_{}$ explanation'.format(2 if WithPreOrdered else 1))
plt.savefig('ModelExplaInfluence{}.pdf'.format(ChartSuf))


# Print and write to file model 
with open('OrderedPairs/{}'.format(fileModel),'wt') as f:
    # Write Header
    for ii in range(len(W)):
        print('{:16} W={:+7.4f} Influence={:6.3f}%'.format(header[ii],W[ii],Influ[ii]*100))
        f.write('{}{}'.format(',' if ii>0 else '',header[ii]))
    f.write(' # rows: W influence DiffMM')
    f.write('\n')
    for ii in range(len(W)):
        f.write('{}{}'.format(',' if ii>0 else '',W[ii]))
    f.write('\n')
    for ii in range(len(Influ)):
        f.write('{}{}'.format(',' if ii>0 else '',Influ[ii]))
    f.write('\n')
    for ii in range(len(DifMM)):
        f.write('{}{}'.format(',' if ii>0 else '',DifMM[ii]))
    f.write('\n')
print('Model wrote to {}'.format(fileModel))

# Measure Quality
PropPairsOK=multiBatchAUC(Ye,P)
print('Overwrite: Proportion of user pairs correctly ranked: {:g}%'.format(PropPairsOK*100)) 

# Predicting on unseen preordered pairs
upP=RankSys.predict(XPreTe)
upPropPairsOK=multiBatchAUC(YPreTe,upP)
print('Test: Proportion of unseen preordered pairs correctly ranked: {:g}%'.format(upPropPairsOK*100)) 


# Estimating accuracy for not seen examples
FoldMaker=KFold(n_splits=10,shuffle=True, random_state=2480) # Folds for Cross Validation
NUserPairs=int(len(Xe)/2)

FIndex=list(FoldMaker.split([[1,1]]*NUserPairs)) # Only matter the index not the values

# Train / Test each fold

def getFoldData(f,X,Y):
    Xf=[]
    Yf=[]
    for i in f:
        ix=i*2 # Pair i correspond with example i*2 and i*2+1
        Xf.append(X[ix])
        Yf.append(Y[ix])
        Xf.append(X[ix+1])
        Yf.append(Y[ix+1])
    return [Xf,Yf]
    
    
PCOP=[] # Proportion Of Corrected Ordered Pairs
for ifi in range(len(FIndex)):
    fi=FIndex[ifi]
    [XTr,YTr]=getFoldData(fi[0],Xe,Ye)
    [XTe,YTe]=getFoldData(fi[1],Xe,Ye)
    RankSys.fit(XPre+XTr,YPre+YTr) # Learning with Pre Ordered + User
    P=RankSys.predict(XTe)         # Evaluating only User
    PropPairsOK=multiBatchAUC(YTe,P)
    PCOP.append(PropPairsOK)
    print('Fold {} Pairs OK={:g}%'.format(ifi,PropPairsOK*100))
print('Average corrected ordered pairs={:g}%'.format(100*sum(PCOP)/len(PCOP)))


