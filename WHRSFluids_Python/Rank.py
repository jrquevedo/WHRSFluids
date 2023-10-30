#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: quevedo
"""

import numpy as np
from sklearn.svm import LinearSVC
from sklearn.base import BaseEstimator
from sklearn.metrics import roc_auc_score


#%% linearRank class
class linearRank(BaseEstimator):
    """
    Class that learns a linear model that generates a global ranking from 
     batchs of partial ranks.
    """
    def __init__(self,LinealClass=None,verbose=0):
        """
        Params:
            LinealClass : sklearn linear classificator. 
                          Method LinealClass.decision_function must be defined
                          Default=sklearn.svm.LinearSVC(C=1,fit_intercept=False)
            verbose     : integer. if 0 no verbosity.
            
        """
        if LinealClass!=None:
            self.LinealClass=LinealClass
        else:
            self.LinealClass=LinearSVC(C=1,fit_intercept=False)
            
        self.verbose=verbose
    
    def fit(self,X,Y):
        """
        Learns a linear model using the partial ranks of X defined by Y.
        Params:
            X : list of examples. An example is a list of values.
            Y : if Y is a list of values:
                   These values are used to compare examples. The examples with
                   the same value are not compared.
                if Y is a list of lists of two values.
                   The first value is used to campare examples in the batch.
                   The second value is the batchId. All examples with the same bathcId
                    own to the same batch. Each example will be only compared to
                    the examples of their batch.
        """
        
        # Calculate batchs Indices
        [batchs,oneBatch]=_getBatchsInd(Y)

        if self.verbose>=1:
            print('There are {} batchs of length:'.format(len(batchs)),end='')
            for b in batchs:
                print(' {}'.format(len(b)),end='')
                if self.verbose>=2:
                    print('(indices:',end='')
                    for bi in b:
                        print(' {}'.format(bi),end='')
                    print(')',end='')
            print()
        
        # Generate comparisons
        cX=[]
        cY=[]
        for bInd in batchs:  # for each batch
            if self.verbose>=3:
                print('Batch indices:',end='')
                for b in bInd:
                    print(' {}'.format(b))
                print('')
            for i in range(len(bInd)-1): # for each pair (i,j) of examples in batch
                xi=X[i]
                yi=Y[i] if oneBatch else Y[i][0]
                for j in range(i,len(bInd)):
                    xj=X[j]
                    yj=Y[j] if oneBatch else Y[j][0]
                    if yi!=yj: # There is a comparation
                        cX.append(np.subtract(xi,xj))
                        cY.append(np.sign(yi-yj))
                        cX.append(np.subtract(xj,xi))
                        cY.append(np.sign(yj-yi))
                        if self.verbose>=3:
                            print('  Generated pair (Y[{}]={},Y[{}]={}'
                                  .format())
        if self.verbose>=1:
            print('Generated {} pairs of comparisons'.format(int(len(cX)/2)))
            
        # Learn the model
        self.LinealClass.fit(cX,cY)
        if self.verbose>=1:
            print('Model learned from {} examples.'.format(len(cX)),end='')
            if self.verbose>=2:
                print(' W=',end='')
                for wv in self.LinealClass.coef_[0]:
                    print(' {:6.4f}'.format(wv),end='')
            print()
            
        return self
    
    def predict(self,X):
        """
        Predicts X using the learned model in fit.
        Params:
            X : list of examples. An example is a list of values.
            
        Returns:
            P : list of predictions. Each prediction is a numeric value.
                If example A has a prediction greater than example B 
                 then A is preferred to (ordered before than) B.
        """            
        P=self.LinealClass.decision_function(X)
        if self.verbose>=1:
            print('Predicted {} examples'.format(len(X)))
        return P
    


#%% multiBatchAUC
def multiBatchAUC(Y,P):
    """
    Calculates an AUC measure for each batch in Y.
    
    Params
        Y : see linearRank.fit, Y param
        P : list of values, predictions.
        
    Returns
        average of each Batch's AUC
    """
    [batchs,oneBatch]=_getBatchsInd(Y)
    if not oneBatch:
        Y=list(map(lambda x:x[0],Y))# Take the ranker values
    AUC=0
    for bInd in batchs:
        # Get the batch's Y and P
        bY=[Y[i] for i in bInd]
        bP=[P[i] for i in bInd]
        bAUC=roc_auc_score(bY,bP)
        AUC=AUC+bAUC
    AUC=AUC/len(batchs)
    return AUC

#%% CIndex(Y,P)
def CIndex(Y,P):
    """
    Calculates a C-index (concordance index) measure 
    C-index is calculated as the proportion of corrected ordered pair of examples
    https://proceedings.neurips.cc/paper/2007/file/33e8075e9970de0cfea955afd4644bb2-Paper.pdf
    
    Params
        Y : list of values, real values.
        P : list of values, predictions.
        
    Returns
        C-Index value. The proportion of all ordered pairs in Y that concordance
         (same order) in P
        If Y is void or all values or Y are the same (no ordered pairs) None is returned 
    """ 
    E=len(Y) # number of examples
    Ci=0
    nPairs=0
    for i in range(E-1):
        for j in range(i,E):
            if Y[i]!=Y[j]: # There is a pair that is ordered
                nPairs=nPairs+1
                if P[i]==P[j]:  # If tie
                    Ci=Ci+0.5 # half sucess (0.5 of 1)
                elif np.sign(P[i]-P[j])==np.sign(Y[i]-Y[j]): # Same order
                    Ci=Ci+1 # Full sucess (1 of 1)
    if nPairs==0:
        return None
    else:
        return Ci/nPairs
    
    
#%% multiBatchCIndex
def multiBatchCIndex(Y,P):
    """
    Calculates a C-index (concordance index) measure for each batch in Y.
    
    Params
        Y : see linearRank.fit, Y param
        P : list of values, predictions.
        
    Returns
        Average of each Batch's C-index. If a C-Index is None it will not be used 
         in the evarage
        If all batchs have a None C-Index None is returned 
    """  
    [batchs,oneBatch]=_getBatchsInd(Y)
    if not oneBatch:
        Y=list(map(lambda x:x[0],Y))# Take the ranker values
    Ci=0
    validBatchs=0
    for bInd in batchs:
        # Get the batch's Y and P
        bY=[Y[i] for i in bInd]
        bP=[P[i] for i in bInd]

        bCi=CIndex(bY,bP)
        if bCi!=None:
            Ci=Ci+bCi
            validBatchs=validBatchs+1
    
    if validBatchs>0:
        return Ci/validBatchs
    else:
        return None

#%% _getBatchsInd function
def _getBatchsInd(Y):
    if type(Y[0]) not in (list,np.ndarray): # There are no batch Ids
        batchs=[list(range(len(Y)))] # There are only one batch
        oneBatch=True
        return [batchs,oneBatch]
        
    # There are batch Ids
    Bn=np.array(list(map(lambda p:p[1],Y))) # Batchs numbers
    B=np.unique(Bn) # Different batchs
    
    batchs=[]
    for b in B:
        batchs.append(np.where(Bn==b)[0].tolist())
    
    oneBatch=False
    return [batchs,oneBatch]

#%% Example of use
# X=[[1,2],[3,4],[5,4],[8,9],[4,7]]
# Y=[1,1,0,1,0]
# Y=[[1,0],[1,0],[0,1],[1,1],[0,0]]

# Ranker=linearRank(verbose=2)
# Ranker.fit(X,Y)
# P=Ranker.predict(X)
# print('AUC={:6.4f}'.format(multiBatchAUC(Y,P)))
