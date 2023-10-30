#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

from skopt import gp_minimize
from WHRSOptimizer.WHRSOptimizerBase import WHRSOptimizerBase
import matplotlib.pyplot as plt

class WHRSskoptBayesian(WHRSOptimizerBase):
    
    def __init__(self,WHRSObject,RankModel,RS=2480,nIter=100,initRandP=10):
        """
        Params:
            WHRSObject : see WHRSOptimizerBase.__init__
            RankModel  : see WHRSOptimizerBase.__init__
            RS         : see WHRSOptimizerBase.__init__
            nIter      : Iterations in the Bayesian Optimization (BO).
                         Default=100
            initRandP  : Number of random points to initialize the BO.
                         Default=10
                         
            The number of total iterations will be initRandP+nIter
        """
        # Call to father constructor 
        WHRSOptimizerBase.__init__(self,WHRSObject,RankModel,RS)
        
        # Params
        self.nIter=nIter
        self.initRandP=initRandP
        
        self.eps=1e-10
        
        # Model
        self.optimizer=None
        
        # Debug
        # self.iter=0
        
    def _negTargetFun(self,l):
        # print('_negTargetFun iter={}'.format(self.iter))
        # self.iter=self.iter+1
        return -self.targetFun(l[0],l[1],l[2],l[3],l[4],l[5],l[6],l[7])

    def _negTargetLoadFun(self,l):
        # print('_negTargetLoadFun iter={}'.format(self.iter))
        # self.iter=self.iter+1
        return -self.targetFun(l[0],l[1],l[2],l[3],l[4],l[5],l[6])
    
    def _maximize(self):
        # optimizer = BayesianOptimization(f=self.targetFun,pbounds=self.pbounds,
        #                                  random_state=self.RS,verbose=0)
        # optimizer.maximize(init_points=self.initRandP,n_iter=self.nIter)
        
        # Function to minimize
        
        # pbounds
        if self.fixedLoad==None:
            minFself=self._negTargetFun
            pbounds=[None]*8
            pbounds[0]=self.pbounds['Load']
            pbounds[1]=self.pbounds['JW_pump']
            pbounds[2]=self.pbounds['RC_Superheat']
            pbounds[3]=self.pbounds['ORC_Subcool']
            pbounds[4]=self.pbounds['ORC_Superheat']
            pbounds[5]=self.pbounds['ORC_Subcool']
            pbounds[6]=self.pbounds['ORC_Pump']
            pbounds[7]=self.pbounds['P_chamber']
        else:
            minFself=self._negTargetLoadFun
            pbounds=[None]*7
            pbounds[0]=self.pbounds['JW_pump']
            pbounds[1]=self.pbounds['RC_Superheat']
            pbounds[2]=self.pbounds['ORC_Subcool']
            pbounds[3]=self.pbounds['ORC_Superheat']
            pbounds[4]=self.pbounds['ORC_Subcool']
            pbounds[5]=self.pbounds['ORC_Pump']
            pbounds[6]=self.pbounds['P_chamber']
            
        
        res=gp_minimize(minFself,pbounds,n_calls=self.nIter+self.initRandP,n_initial_points=self.initRandP,random_state=2480)
        
        if self.fixedLoad==None:
            self.setMaxValues(res.x[0],res.x[1],res.x[2],res.x[3],res.x[4],res.x[5],res.x[6],res.x[7])

        else:
            Load=self.fixedLoad
            self.setMaxValues(Load,res.x[0],res.x[1],res.x[2],res.x[3],res.x[4],res.x[5],res.x[6])

                
        self.optimizer=res
        return res

    def _plotOpt(self,fsave=None):
        randTarget=[None]*self.initRandP
        bayeTarget=[None]*self.nIter
        for i in range(self.initRandP):
            randTarget[i]=-self.optimizer.func_vals[i]
        for i in range(self.nIter):
            bayeTarget[i]=-self.optimizer.func_vals[i+self.initRandP]
        plt.plot(list(range(1,self.initRandP+1)),randTarget,label='random search',linestyle='',marker='.')
        plt.plot(list(range(self.initRandP+1,self.initRandP+self.nIter+1)),bayeTarget,label='bayesian search')
        plt.legend(loc='lower right')
        plt.xlabel('Iterations')
        plt.ylabel('Rank value')
        if fsave!=None:
            plt.savefig(fsave,dpi=300)
        plt.show()
        
        
        
    