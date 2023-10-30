#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

import time

class WHRSOptimizerBase:
    """
    Base class for WHRS optimizers
    """
    def __init__(self,WHRSObject,RankModel,RS=2480):
        """
        Params:
            WHRSObject : a WHRS Object
            RankModel  : vector of 3 components. Weigths of each WHRS outputs
            RS         : random state. Default=2480 (Office phone number)
        """
        # Params
        self.WHRSObject=WHRSObject
        self.RankModel=RankModel
        self.RS=RS
        
        # Fixed for WHRS
        self.params=['Load','JW_pump','RC_Superheat','RC_Subcool','ORC_Superheat'
                    ,'ORC_Subcool','ORC_Pump','P_chamber']
        
        # For optimization
        self.fixedLoad=None
        LoadRange=WHRSObject.params_range['Load']
        if LoadRange[0]==LoadRange[1]:
            self.fixedLoad=LoadRange[0]
            print('Fixed Load={}'.format(self.fixedLoad))
            self.pbounds=WHRSObject.params_range.copy()
            del self.pbounds['Load']
            self.targetFun=self.rankFLoad
        else:
            self.targetFun=self.rankF
            self.pbounds=WHRSObject.params_range
        self.optTime=None
        
        # Max point
        self.Load=None
        self.JW_pump=None
        self.RC_Superheat=None
        self.RC_Subcool=None
        self.ORC_Superheat=None
        self.ORC_Subcool=None
        self.ORC_Pump=None
        self.P_chamber=None
        
        # Max outputs
        self.WHRS_cycle_output=None
        self.CO2_red=None
        self.EPC=None
        
        # Max Target
        self.target=None
        
    def rankFLoad(self,JW_pump,
                      RC_Superheat,RC_Subcool,
                      ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber):
        if self.fixedLoad==None:
            raise Exception('WHRSOptimizerBase: use rankFLoad without fiixing the Load')
            
        return self.rankF(self.fixedLoad,JW_pump,
                          RC_Superheat,RC_Subcool,
                          ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber)
    
    def rankF(self,Load,JW_pump,
                      RC_Superheat,RC_Subcool,
                      ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber):
        try:
            (WHRS_cycle_output,CO2_red,EPC)=self.WHRSObject(Load,JW_pump,
                              RC_Superheat,RC_Subcool,
                              ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber)
        except:
            print('Error in WHRS(Load={},JW_pump={},RC_Superheat={},RC_Subcool={},ORC_Superheat={},ORC_Subcool={},ORC_Pump={},P_chamber={})'.format(Load,JW_pump,
                              RC_Superheat,RC_Subcool,
                              ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber))
            raise
        return self._targetOutput(WHRS_cycle_output,CO2_red,EPC)
    
    def _targetOutput(self,WHRS_cycle_output,CO2_red,EPC):
        return WHRS_cycle_output*self.RankModel[0]+CO2_red*self.RankModel[1]+EPC*self.RankModel[2]
    
    def setMaxValues(self,Load,JW_pump,
                      RC_Superheat,RC_Subcool,
                      ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber):
        # Max point
        self.Load=Load
        self.JW_pump=JW_pump
        self.RC_Superheat=RC_Superheat
        self.RC_Subcool=RC_Subcool
        self.ORC_Superheat=ORC_Superheat
        self.ORC_Subcool=ORC_Subcool
        self.ORC_Pump=ORC_Pump
        self.P_chamber=P_chamber
        
        # Max outputs
        (WHRS_cycle_output,CO2_red,EPC)=self.WHRSObject(Load,JW_pump,
                          RC_Superheat,RC_Subcool,
                          ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber)
        self.WHRS_cycle_output=WHRS_cycle_output
        self.CO2_red=CO2_red
        self.EPC=EPC
        
        # Max Target
        self.target=self._targetOutput(WHRS_cycle_output,CO2_red,EPC)
        
    def getMaxValues(self):
        return (self.Load,self.JW_pump,self.RC_Superheat,self.RC_Subcool,self.ORC_Superheat,self.ORC_Subcool,self.ORC_Pump,self.P_chamber,
                self.WHRS_cycle_output,self.CO2_red,self.EPC,
                self.target,self.optTime)
    
    def getMaxNames(self):
        return 'Load','JW_pump','RC_Superheat','RC_Subcool','ORC_Superheat','ORC_Subcool','ORC_Pump','P_chamber','WHRS_cycle_output','CO2_red','EPC','rankValue','Time'
    
    def getOptTime(self):
        return self.optTime
    
    def maximize(self):
        tst=time.time()
        vret=self._maximize()
        self.optTime=time.time()-tst
        return vret
    
    # To be define in child classes
    def _maximize(self):
        pass
    
    def plot(self,fsave=None):
        self._plotOpt(fsave)
    
    # To be define in child classes
    def _plotOpt(self,fsave=None):
        pass
        