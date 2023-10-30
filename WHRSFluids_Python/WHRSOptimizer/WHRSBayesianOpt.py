#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

from bayes_opt import BayesianOptimization # https://github.com/fmfn/BayesianOptimization
from WHRSOptimizer.WHRSOptimizerBase import WHRSOptimizerBase
import matplotlib.pyplot as plt

class WHRSBayesianOpt(WHRSOptimizerBase):
    
    def __init__(self,WHRSObject,RS=2480,nIter=100,initRandP=10):
        """
        Params:
            WHRSObject : see WHRSOptimizerBase.__init__
            RS         : see WHRSOptimizerBase.__init__
            nIter      : Iterations in the Bayesian Optimization (BO).
                         Default=100
            initRandP  : Number of random points to initialize the BO.
                         Default=10
                         
            The number of total iterations will be initRandP+nIter
        """
        # Call to father constructor 
        WHRSOptimizerBase.__init__(self,WHRSObject,RS)
        
        # Params
        self.nIter=nIter
        self.initRandP=initRandP
        
        # Model
        self.optimizer=None
    
    def _maximize(self):
        optimizer = BayesianOptimization(f=self.targetFun,pbounds=self.pbounds,
                                         random_state=self.RS,verbose=0)
        optimizer.maximize(init_points=self.initRandP,n_iter=self.nIter)
        
        if self.fixedLoad==None:
            Load=optimizer.max['params']['Load']
        else:
            Load=self.fixedLoad
        self.setMaxValues(Load,
                     optimizer.max['params']['JW_pump'],
                     optimizer.max['params']['RC_Superheat'],
                     optimizer.max['params']['RC_Subcool'],
                     optimizer.max['params']['ORC_Superheat'],
                     optimizer.max['params']['ORC_Subcool'],
                     optimizer.max['params']['ORC_Pump'],
                     optimizer.max['params']['P_chamber'])
        
        self.optimizer=optimizer
        return optimizer

    def _plotOpt(self,fsave=None):
        randTarget=[None]*self.initRandP
        bayeTarget=[None]*self.nIter
        for i in range(self.initRandP):
            randTarget[i]=self.optimizer.res[i]['target']
        for i in range(self.nIter):
            bayeTarget[i]=self.optimizer.res[self.initRandP+i]['target']
        plt.plot(list(range(1,self.initRandP+1)),randTarget,label='random search',linestyle='',marker='.')
        plt.plot(list(range(self.initRandP+1,self.initRandP+self.nIter+1)),bayeTarget,label='bayesian search')
        plt.legend(loc='lower right')
        plt.xlabel('Iterations')
        plt.ylabel('Rank value')
        if fsave!=None:
            plt.savefig(fsave,dpi=300)
        plt.show()
        
        
        
    