#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@version 2

New in version 2:
    - Use different fluids
    - Returns WHRS_cycle_output

@author: quevedo
"""


import math
import pickle
import os.path
import CoolProp.CoolProp as CP

class WHRS():
    def __init__(self,PropsSIStore='file',verbose=0):
        """
        Params:
            PropsSIStore : possible values: 'none','memory','file'
                            What to do with PropsSI calls
                            'none'   : no store. All times a value is required 
                                       a call to PropsSI method is executed
                            'memory' : store in memory. The first time that is 
                                       called PropsSI(P) store the result, when 
                                       PropsSI(P) is later called the value stored
                                       will be used (only 1 call per parameters' value')
                            'file'   : like memory but all the calls are stored 
                                       in a file and loaded at the begining of 
                                       the execution
                            Default='file'
            verbose      : int value in [0,2]. If >0 this class shows process' information.
                         Default=0
        """
        # Params
        self.verbose=verbose
        self.PropsSIStore=PropsSIStore
        

        
        # Tables of caculated params
        self.EngineLoad=       [ 30   , 35   , 40   , 45   , 50   , 55   , 60   , 65   , 70   , 75   , 80   , 85   , 90   , 95   ,100   ,110   ]
        self.FOConsumption=    [175.10,179.04,182.98,186.92,185.79,194.80,198.74,202.68,206.62,210.56,214.80,215.87,210.27,208.15,206.04,201.81]
        self.TempEG=           [600.15,605.15,611.15,616.15,622.15,630.15,639.15,648.15,657.15,666.15,689.15,672.15,695.15,678.15,682.15,699.15]
        self.MaxFlowRate=      [  2.18,  2.47,  2.76,  3.05,  3.29,  3.63,  3.92,  4.21,  4.50,  4.79,  5.08,  5.45,  6.66,  5.95,  6.24,  6.82]
        self.FO_consumption_WO=[175.1 ,179.04,182.98,186.92,185.79,194.8 ,198.74,202.68,206.62,210.56,215.5 ,215.87,210.27,208.15,206.04,201.81]
        
        self.Engine_blockLoad=[0,  75   ,  80   , 100]
        self.Engine_block=    [0, 295.93, 366.80, 369.06]

        self.T_D2_Constant=369.15       # ENGINE JW
        self.T_Pump_eff_Constant=0.75   # JW PUMP
        self.T_sw_in_Constant=15.13+273.15     # TSW PUMP
        self.P_sw_in_Constant=2.4       # PSW PUMP
        self.ORC_Pump_eff_Constant=0.75 # ORC PUMP
        self.Pinch_point_des_Constant=10# DESALINATION
        self.T_des_surface_Constan=60+273.15   # DESALINATION
        self.N_TEG_Constant=100         # TEG
        self.TEG_hot_Constant=61.965+273.15
        
        # Fluid Names and Codes
                             # Name                  Code                   Id
        self.FluidNameCode=[ ['Ammonia',            'ammonia'],           #  0
                             ['Cyclohexane',        'Cyclohexane'],       #  1
                             ['Hexane',             'Hexane'],            #  2
                             ['Propane',            'Propane'],           #  3
                             ['Propylene',          'propylene'],         #  4
                             ['Toluene',            'toluene'],           #  5
                             ['R1233zd(E)',         'R1233zdE'],          #  6
                             ['R1234ZE(Z)',         'R1234ZE(Z)'],        #  7
                             ['R1234Yf',            'R1234YF'],           #  8
                             ['R161',               'Fluoroethane'],      #  9
                             ['IsoButane',          'isobutane'],         # 10
                             ['Dimethyl Ether',     'DIMETHYLETHER'],     # 11
                             ['n-Pentane',          'nPentane'],          # 12
                             ['1,2-Dichloroethane', '1,2-dichloroethane'],# 13
                             ['Novec 649',          'NOVEC649'],          # 14
                             ['SES36',              'SES36']              # 15
                           ]
        self.defaultFluidId=1 # Cyclohexane
        
        # Stored PropSI
        self.filePropSI='PropSI.dump'
        self.dictPropSI={}
        
        # Input parameters' ranges
        self.params_range={'Load'         :[50   ,100   ], # [50,100] Beta(a=2,b=2)*50+50 <- entre 75-80
                           'JW_pump'      :[ 3.15,  4.15],
                           'RC_Superheat' :[ 1e-4, 25   ],
                           'RC_Subcool'   :[ 1e-4, 10   ],
                           'ORC_Superheat':[ 1e-4, 25   ],
                           'ORC_Subcool'  :[ 1e-4, 10   ],
                           'ORC_Pump'     :[ 5.59,  6.6 ], 
                           'P_chamber'    :[ 0.09,  0.2 ],
                           'Fluid'        : [0   , len(self.FluidNameCode)-1]
                          } 
        
        # Input/Calculated/Fixed,Output Params
        self.params_name_type=[('Load','i'),             # 0
                               ('FO_Consumption','c'),   # 1
                               ('Exh_in','c'),           # 2
                               ('m_exh','c'),            # 3
                               ('T_D2','f'),             # 4
                               ('JW_pump','i'),          # 5
                               ('Pump_eff','f'),         # 6
                               ('Heat_block','c'),       # 7
                               ('T_sw_in','f'),          # 8
                               ('P_sw_in','f'),          # 9
                               ('Power','c'),            #10
                               ('RC_Superheat','i'),     #11
                               ('RC_Subcool','i'),       #12
                               ('ORC_Superheat','i'),    #13
                               ('ORC_Subcool','i'),      #14
                               ('ORC_Pump','i'),         #15
                               ('ORC_Pump_eff','f'),     #16
                               ('P_chamber','i'),        #17
                               ('Pinch_point_des','f'),  #18
                               ('T_des_surface','f'),    #19
                               ('N_TEG','f'),            #20
                               ('TEG_hot','f'),          #21
                               ('TEG_cold','c'),         #22
                               ('WHRS_cycle_output','o'),#23
                               ('CO2_red','o'),          #24
                               ('EPC','o')               #25
                              ]
        
        # Model
        self.params_value=[None]*len(self.params_name_type) 

    def _loadPropSI(self):
        if self.PropsSIStore!='file':
            return
        if len(self.dictPropSI)==0: # No loaded data
            if self.verbose>=1:
                print('There are no PropSI data')
            if not os.path.isfile(self.filePropSI): # No file
                if self.verbose>=1:
                    print('Not exist file: {}'.format(self.filePropSI))
                return 
            # There is file
            if self.verbose>=1:
                print('Reading from file: {}'.format(self.filePropSI))
            with open(self.filePropSI, 'rb') as f:
                self.dictPropSI=pickle.load(f)  # self.dictPropSI
                if self.verbose>=1:
                    print('Readed: {} calls'.format(len(self.dictPropSI)))
                    
    def _savePropSI(self):
        if self.PropsSIStore!='file':
            return
        with open(self.filePropSI, 'wb') as f:
            pickle.dump(self.dictPropSI,f)  # dictPropSI
        if self.verbose>=1:
            print('Guardado en {} {} entradas de PropSI'
                  .format(self.filePropSI,len(self.dictPropSI)))

    def _py_CoolProp_CoolProp_PropsSI(self,P1,P2,P3=None,P4=None,P5=None,P6=None):#('P','T',T_cond_ORC,'Q',1,self._getDefaultFluidCode()) 
        Tup=(P1,P2,P3,P4,P5,P6)
        if Tup in self.dictPropSI:
            v=self.dictPropSI[Tup]
            if self.verbose>=2:
                print('Stored: {} -> {}'.format(Tup,v))
            return v
        
        try:
            if P3==None:
                prop = CP.PropsSI(P1,P2)
            else:
                prop = CP.PropsSI(P1,P2,P3,P4,P5,P6)
            if self.verbose>=2:
                print('({} {} {} {} {} {}) -> {}'.format(P1,P2,P3,P4,P5,P6,prop))
        except ValueError:
            print('Error en: CP.PropsSI({},{},{},{},{},{}'.format(P1,P2,P3,P4,P5,P6))
            raise
            
            
        
        self.dictPropSI[Tup]=prop # Store in dict
        
        return prop
            
    def _warndlg(self,msg1,msg2):
        print('Warning:',msg1,msg2)
        
    def _checkParam(self,v,name):
        range=self.params_range[name]
        if self.verbose>=1:
            print('Parameter {}={} range=[{},{}]'.format(name,v,range[0],range[1]))
        if v<range[0] or v>range[1]:
            raise Exception('WHRS constructor: Paramter {}={} out of range [{},{}]'
                            .format(name,v,range[0],range[1]))
        

    def _interpolate(self,v,X,Y,Yname,Xname='Load'):
        # If v is out of range then output the extreme values
        if v<=X[0]:
            return Y[0]
        np=len(X)
        if v>=X[np-1]:
            return Y[np-1]
        
        # Search for the interval in X where v is
        for i in range(np-1):
            if X[i+1]>v: # v is in the interval [X[i],X[i+1])
                incre=Y[i+1]-Y[i] # increment
                p=Y[i]+incre*(v-X[i])/(X[i+1]-X[i]) # Add to Y[i] de proportion of increment
                
                if self.verbose>=1:
                    print('{}={} in [{}({})),{}({}))] incre={:5.2f} {}={}'
                          .format(Xname,v,X[i],Y[i],X[i+1],Y[i+1],incre,Yname,p))
                return p
            
    def _calculateFOC(self,Load):
        return self._interpolate(Load,self.EngineLoad,self.FOConsumption,'FO_Consumption')
    
    def _calculateTempEG(self,Load):
        return self._interpolate(Load,self.EngineLoad,self.TempEG,'TempEG')
            
    def _calculateMaxFlowRate(self,Load):
        return self._interpolate(Load,self.EngineLoad,self.MaxFlowRate,'MaxFlowRate')
    
    def _calculateEngine_block(self,Load):
        return self._interpolate(Load,self.Engine_blockLoad,self.Engine_block,'Engine_block')
    
    def _calculateFO_consumption_WO(self,Load):
        return self._interpolate(Load,self.EngineLoad,self.FO_consumption_WO,'FO_consumption_WO')
        
    def setDefaultFluid(self,fluid):
        if type(fluid)!=int:
            raise Exception('WHRS.setDefaultFluid(fluid), fluid is not an integer')
        if fluid<0 or fluid>=len(self.FluidNameCode):
            raise Exception('WHRS.setDefaultFluid(fluid), fluid is not in [0,{}]'.format(len(self.FluidNameCode)-1))
        self.defaultFluidId=fluid
        if self.verbose>=1:
            print('Fluid used: {}({})'.format(self.FluidNameCode[fluid][0],self.FluidNameCode[fluid][1]))
        
    def getDefaultFluidName(self):
        return self.FluidNameCode[self.defaultFluidId][0]
    
    def getDefaultFluidCode(self):
        return self.FluidNameCode[self.defaultFluidId][1]
        
    def _getDefaultFluidCode(self):
        return self.FluidNameCode[self.defaultFluidId][1]
    
    def __call__(self,Load,JW_pump,
                      RC_Superheat,RC_Subcool,
                      ORC_Superheat,ORC_Subcool,ORC_Pump,P_chamber,fluid=None):
        self._loadPropSI() # Load stored calls to PropSI
        # 0. INPUT DATA
        
        # Diesel engine
        self._checkParam(Load,'Load')
        self._checkParam(JW_pump,'JW_pump')
        
        
        
        FO_Consumption = self._calculateFOC(Load)         # ENGINE FO
        Exh_in         = self._calculateTempEG(Load)      # ENGINE EXH
        m_exh          = self._calculateMaxFlowRate(Load) # ENGINE EXH
        T_D2           = self.T_D2_Constant               # ENGINE JW
        HT_pump        = JW_pump * 100000                 # JW PUMP
        Pump_eff       = self.T_Pump_eff_Constant         # JW PUMP
        Heat_block     = self._calculateEngine_block(Load)# ENGINE BLOCK, CAC AND LOC 
        T_sw_in        = self.T_sw_in_Constant            # TSW PUMP
        P_sw_in        = self.P_sw_in_Constant * 100000   # PSW PUMP
        Power          = 3000 * (Load/100)                # ENGINE POWER
        
        # Waste Heat Recovery System
        
        self._checkParam(RC_Superheat,'RC_Superheat')  # ENGINE JW
        self._checkParam(RC_Subcool,'RC_Subcool')      # ENGINE JW
        self._checkParam(ORC_Superheat,'ORC_Superheat')# ORC FLUID
        self._checkParam(ORC_Subcool,'ORC_Subcool')    # ORC FLUID
        self._checkParam(ORC_Pump,'ORC_Pump')          # ORC PUMP
        self._checkParam(P_chamber,'P_chamber')        # DESALINATION
        
        ORC_Pump        = ORC_Pump * 100000 # ORC PUMP
        ORC_Pump_eff    = self.ORC_Pump_eff_Constant # ORC PUMP
        P_chamber       = P_chamber * 100000 # DESALINATION
        Pinch_point_des = self.Pinch_point_des_Constant # DESALINATION
        T_des_surface   = self.T_des_surface_Constan# DESALINATION
        N_TEG           = self.N_TEG_Constant # TEG
        TEG_hot         = self.TEG_hot_Constant # TEG hot side temperature (NOT VALID)
        # TEG_cold      will be calculated afterwards
        

        
        # Hot source 1 - Exhaust gas
        if (Exh_in <= 595):
            self._warndlg ({'Exhaust gas temperature introduced is too low.'},'Warning') # Exhaust gas temperature below W6L32 data at 30# MCR
        
        if (Exh_in >= 750):
            self._warndlg ({'Exhaust gas temperature introduced is too high.'},'Warning') # Exhaust gas temperature above W6L32 data at 110# MCR
        
        Exh_out = 413 # Desired exhaust gas temp outlet of RC Evaporator - OPERATIONAL CONDITION
        Exh_min = 403.15 # Min temp to avoid cold corrosion, reference point, K - ACID DEW POINT LIMIT
        if (m_exh <= 2):
            self._warndlg('Exhaust gas mass flow introduced is too low.','Warning') # Exhaust gas mass flow below engine data at 30# MCR
        
        if (m_exh >= 7.5):
            self._warndlg('Exhaust gas mass flow introduced is too high.','Warning') # Exhaust gas mass flow over engine data at 110# MCR
        
        Cp_exh = 1.185 # kJ/kg·K - KOSHY, 2015.
        
        # Hot source 2 - Jacket water
        m_jw = 16.685 # kg/s - W6L32 data
        Cp_jw = 4.05 # kJ/kg·K - Sample analysis
        if (T_D2 <= 323.15):
            self._warndlg ({'Jacket Water temperature is too low.'},'Warning') # Minimum temperature of JW at the engine outlet: 50 ºC - ENGINE ALARM
        
        if (T_D2 >= 388.15):
            self._warndlg ({'Jacket Water temperature is too high.'},'Warning') # Maximum temperature of JW at the engine outlet: 115 ºC - ENGINE ALARM (113 ºC)
        
        
        # Cold source - Sea water
        m_sw = 11.62 # kg/s - OPERATIONAL CONDITION - FACET J100 and SW Pump ITUR Normabloc N2-40/160B/7.5-2900 rpm (40.8 m3/h at 2.4 bar)
        if (T_sw_in <= 273.15):
            self._warndlg({'Sea water temperature introduced is too low.'},'Warning') # Sea water at 0ºC
        
        if (T_sw_in >= 323.15):
            self._warndlg({'Sea water temperature introduced is too high.'},'Warning') # Sea water at 50ºC
        
        if (P_sw_in <= 50000):
            self._warndlg({'Sea water pressure introduced is too low.'},'Warning') # Sea water at 0.5 bar
        
        if (P_sw_in >= 500000):
            self._warndlg({'Sea water pressure introduced is too high.'},'Warning') # Sea water at 5 bar
        
        Cp_sw = self._py_CoolProp_CoolProp_PropsSI('Cpmass','T',T_sw_in,'Q',0,"Water")/1000 # Cp Sea water, kJ/kg·K - LLAMADA A BASE DE DATOS COOLPROP (TODAS LAS ESTRUCTURAS DEL TIPO self._py_CoolProp_CoolProp_PropsSI SON LLAMADAS A LA BASE DE DATOS)
        Sw_density = 1025 # Sea water density, kg/m3 - STANDARD VALUE
        Sw_pump_eff = 0.8
        
        # Ambient conditions
        T_env = 298.15 # K - ISO 15550:2002
        Press_env = 100000 # Pa - ISO 15550:2002
        
        # TEG Limits
        if (TEG_hot >= 473):
            self._warndlg ({'Thermoelectric modules cannot withstand temperatures over 200 ºC.'},'Warning') # Limit of Bi2Te3 TEG continuous operation
        
     
        
        # 1. DESALINATION SYSTEM
        # Operational desired conditions
        Kjw = 25.6 # Constant for one phase evaporator
        Des_area = 4.8 # Desalinator surface area, m2
        Daily_cap = 22 # FW generation, m3/24h - MAX CAPACITY OF FW GENERATOR
        T_D3 = 55 + 273.15 # JW outlet temperature from evaporator, K - OPERATIONAL CONDITION
        PD2 = HT_pump # JW inlet pressure to evaporator, Pa - OPERATIONAL CONDITION
        PD3 = PD2 - 10000 # JW outlet pressure from evaporator, Pa
        if (PD2 >= 500000):
            self._warndlg ({'Jacket Water pressure is too high for the desalination equipment.'},'Warning') # Maximum pressure of JW at the inlet of the desalinator: 5 bar, Pa
        
        if (P_chamber < 9000):
            self._warndlg ({'Chamber press is too low.','The device cannot withstand this level of vacuumm.'},'Warning') # Minimum vacuum: 0,09 bar, Pa
        
        if (P_chamber > 20000):
            self._warndlg ({'Chamber press is too high for desalination.'},'Warning') # Maximum chamber press: 0,2 bar, Pa
        
        if (Pinch_point_des < 0):
            self._warndlg ({'Pinch point is too low for desalination'},'Warning') # Minimum pinch point: 0 K
        
        if (Pinch_point_des > 30):
            self._warndlg ({'Pinch point is too high for desalination.'},'Warning') # Maximum pinch point: 30 K
        
        # Desalination process (Counterflow JW / SW)
        T_des = self._py_CoolProp_CoolProp_PropsSI('T','Q',1,'P',P_chamber,"Water") # Vaporization temperature of sea water inside desalination system, K
        m_jw_des = (((Kjw*Daily_cap) / (T_D2 - T_D3)) * 1.025) / 3.6 # Mass flow needed on the evaporator, kg/s EQ 1 - DOC 3
        m_jw_cycles = m_jw - m_jw_des # mass flow remaining for the RC + ORC, kg/s EQ 14 - DOC 3
        Q_jw_des = m_jw_des * Cp_jw * (T_D2 - T_D3) # Available heat from JW heat source, kJ/s EQ 2 - DOC 3
        Q_radiation_des = (0.84 * 5.67 * 1e-8 * (T_des_surface)**4 * Des_area)/1000 # Heat radiated to environment (Emissivity * Stefan-Boltzmann constant * Desalinator temp * Des area), kJ EQ 3 - DOC 3
        Q_sw_des = Q_jw_des - Q_radiation_des # Available heat for fresh water generation, kJ/s EQ 4 - DOC 3
        Q_sw_des_equivalent = Q_sw_des * (1 - (T_env / T_des)) # Equivalent amount of power, according to GUDE, 2009 EQ 5 - DOC 3
        H_D2 = (self._py_CoolProp_CoolProp_PropsSI('H','T',T_D2,'P',PD2,"Water"))/1000 # Enthalpy of jacket water at the inlet of the desalination, kJ/kg
        S_D2 = (self._py_CoolProp_CoolProp_PropsSI('S','T',T_D2,'P',PD2,"Water"))/1000 # Entropy of jacket water at the inlet of the desalination, kJ/kg·K
        H_D3 = (self._py_CoolProp_CoolProp_PropsSI('H','T',T_D3,'P',PD3,"Water"))/1000 # Enthalpy of jacket water at the outlet of the desalination, kJ/kg
        S_D3 = (self._py_CoolProp_CoolProp_PropsSI('S','T',T_D3,'P',PD3,"Water"))/1000 # Enthalpy of jacket water at the outlet of the desalination, kJ/kg·K
        
        # 2. STEAM RANKINE CYCLE
        # Operational desired conditions
        if (RC_Superheat < 0):
            self._warndlg ({'Rankine Superheating is too low.'},'Warning') # Minimum superheating: 0 K
        
        if (RC_Superheat > 25):
            self._warndlg ({'Rankine Superheating is too high.'},'Warning') # Maximum superheating: 25 K
        
        if (RC_Subcool < 0):
            self._warndlg ({'Rankine Subcooling is too low.'},'Warning') # Minimum subcooling: 0 K
        
        if (RC_Subcool > 25):
            self._warndlg ({'Rankine Subcooling is too high.'},'Warning') # Maximum subcooling: 25 K
        
        # Pump Conditions
        if (Pump_eff <= 0):
            self._warndlg ({'Pump efficiency is too low.'},'Warning') 
        
        if (Pump_eff > 1):
            self._warndlg ({'Pump efficiency is too high.'},'Warning')
        
        # Turbine Conditions
        Turb_eff_RC = 0.8 # Turbine efficiency - OPERATIONAL CONDITION
        Gen_eff_RC = 0.96 # Alternator efficiency - OPERATIONAL CONDITION
        # Condenser inside (Saturated liquid, RC1)
        T_RC1 = (55 + 273.15) + RC_Subcool # K
        P_RC1 = self._py_CoolProp_CoolProp_PropsSI('P','T',T_RC1,'Q',0,"Water") # Pa
        S_RC1 = self._py_CoolProp_CoolProp_PropsSI('S','T',T_RC1,'Q',0,"Water")/1000 # kJ/kg·K
        # Condenser outlet (Subcooled liquid before engine, 1)
        T_1 = 55 + 273.15 # Temperature of jacket water at the inlet of the engine, K - OPERATIONAL CONDITION
        P_1 = P_RC1 # Pa
        H_1 = self._py_CoolProp_CoolProp_PropsSI('H','T',T_1,'P',P_1,"Water")/1000 # kJ/kg
        S_1 = self._py_CoolProp_CoolProp_PropsSI('S','T',T_1,'P',P_1,"Water")/1000 # kJ/kg·K
        D_1 = self._py_CoolProp_CoolProp_PropsSI('D','T',T_1,'P',P_1,"Water") # kg/m3
        SpecVol_RC1 = 1/D_1 # m3/kg
        # Pump (Liquid pumped, 2s and 2)
        P_2 = P_1 + HT_pump  # Jacket water pump raises pressure, Pa
        S_2s = S_1 # kJ/kg·K
        w_spec_pump_ideal = (SpecVol_RC1 * (P_2 - P_1))/1000 # Specific work introduced on the pump, kJ/kg EQ 10 - DOC 3
        H_2s = w_spec_pump_ideal + H_1 # Enthalpy at 2s, kJ/kg EQ 10 - DOC 3 
        W_pump_ideal = (m_jw * w_spec_pump_ideal) # Ideal work needed by the pump, kJ/s EQ 10 - DOC 3
        W_pump_real = W_pump_ideal / Pump_eff # Real work needed by the pump, kJ/s EQ 10 - DOC 3
        H_2 = ((H_2s - H_1)/Pump_eff) + H_1 # Enthalpy at point 2, kJ/kg
        H_2_joules = H_2 * 1000 # Enthalpy in J/kg for the correct calculation of T_2 and S_2
        T_2 = self._py_CoolProp_CoolProp_PropsSI('T','P',P_2,'H',H_2_joules,"Water") # Temperature of the jacket water at the outlet of the pump, K
        S_2 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_2,'H',H_2_joules,"Water")/1000 # Entropy of the jacket water at the outlet of the pump, kJ/kg·K
        I_pump_RC = m_jw * T_env * (S_2 - S_1) # Irreversibilities on the pumping process, kJ/s EQ 11 - DOC 3
        # Engine (Liquid heated with pressure drop - First heat source, 2c)
        T_2c = T_D2 # Temperature of jacket water at the outlet of the engine (W6L32 data), K
        P_2c = P_2 - 55000 # Loss of pressure on engine, Pa - 0,55 bar - OPERATIONAL CONDITION
        H_2c = self._py_CoolProp_CoolProp_PropsSI('H','T',T_2c,'P',P_2c,"Water")/1000 # kJ/kg
        S_2c = self._py_CoolProp_CoolProp_PropsSI('S','T',T_2c,'P',P_2c,"Water")/1000 # kJ/kg·K
        Q_engine = m_jw * Cp_jw * (T_2c - T_2) # Heat supplied to the cycle by the engine, kJ/s EQ 12 - DOC 3
        I_engine = m_jw * T_env * (S_2c - S_2) # Irreversibilities due to engine heating and loss of pressure, kJ/s EQ 13 - DOC 3
        # Mass flow of jacket water used for RC and ORC
        Q_exh = m_exh * Cp_exh * (Exh_in - Exh_out) # Heat available from exhaust gas, kJ/s EQ 6 - DOC 3
        T_evap_RC = self._py_CoolProp_CoolProp_PropsSI('T','P',P_2c,'Q',0,"Water") # Vaporization temperature of jacket water at P_2c, K
        T_RC2 = T_D2 # Temperature of jacket water at the inlet of the evaporator, K
        H_sat_vap_RC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_2c,'Q',1,"Water")/1000 # Enthalpy of water saturated vapor at P_2c, kJ/kg
        H_sat_liq_RC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_2c,'Q',0,"Water")/1000 # Enthalpy of water saturated liquid at P_2c, kJ/kg
        m_jw_RC = Q_exh / ((Cp_jw * (T_evap_RC - T_RC2)) + (H_sat_vap_RC - H_sat_liq_RC) + (Cp_jw * RC_Superheat) ) # Mass of jacket water for the RC (three steps method), kg/s EQ 9 - DOC 3
        m_jw_ORC = m_jw_cycles - m_jw_RC # Mass of jacket water available for ORC, kg/s EQ 14 - DOC 3 se obtiene m_jw_ORC
        I_engine_RC = m_jw_RC * T_env * (S_2c - S_2) # Irreversibilities due to engine heating and loss of pressure accounting for the RC, kJ/s
        # Evaporator (Counterflow Exh Gas / JW - Second heat source, RC2 and RC3)
        H_RC2 = H_2c # kJ/kg
        S_RC2 = S_2c # kJ/kg·K
        T_RC3 = T_evap_RC + RC_Superheat # Expected outlet temperature of jacket water at evaporator, K
        P_RC3 = P_2c - 10000 # Loss of pressure in evaporator, Pa - OPERATIONAL CONDITION
        H_RC3 = self._py_CoolProp_CoolProp_PropsSI('H','T',T_RC3,'P',P_RC3,"Water")/1000 # kJ/kg
        S_RC3 = self._py_CoolProp_CoolProp_PropsSI('S','T',T_RC3,'P',P_RC3,"Water")/1000 # kJ/kg
        T_avg_exh = (Exh_in - Exh_out) / math.log (Exh_in/Exh_out) # Exhaust average temperature inside the evaporator, K
        I_evap_exh_RC = Q_exh * (1 - (T_env / T_avg_exh)) # Irreversibilities of the exhaust gas on evaporator, kJ/s EQ 15 - DOC 3
        I_evap_jw_RC = m_jw_RC * (H_RC3 - H_RC2 - (T_env * (S_RC3 - S_RC2))) # Irreversibilities of the jacket water on evaporator, kJ/s EQ 16 - DOC 3
        I_evap_RC_total = I_evap_exh_RC + I_evap_jw_RC # Total irreversibilities on evaporator, kJ/s EQ 17 - DOC 3
        # Turbine (Expansion, 4s and 4)
        P_RC4 = P_RC1 + 10000 # Loss of pressure in condenser, Pa - OPERATIONAL CONDITION
        S_RC4s = S_RC3 # Isentropic process, kJ/kg·K
        S_RC_P4_f = self._py_CoolProp_CoolProp_PropsSI('S','P',P_RC4,'Q',0,"Water")/1000 # kJ/kg·K
        S_RC_P4_g = self._py_CoolProp_CoolProp_PropsSI('S','P',P_RC4,'Q',1,"Water")/1000 # kJ/kg·K
        X_RC4s = (S_RC4s - S_RC_P4_f) / (S_RC_P4_g - S_RC_P4_f) # Steam quality at state 4s
        H_RC_P4_f = self._py_CoolProp_CoolProp_PropsSI('H','P',P_RC4,'Q',0,"Water")/1000 # kJ/kg
        H_RC_P4_g = self._py_CoolProp_CoolProp_PropsSI('H','P',P_RC4,'Q',1,"Water")/1000 # kJ/kg
        H_RC4s = H_RC_P4_f + (X_RC4s * (H_RC_P4_g - H_RC_P4_f)) # kJ/kg
        W_turbine_ideal_RC = (m_jw_RC * (H_RC3 - H_RC4s)) # Ideal work delivered by the turbine, kJ/s
        H_RC4 = H_RC3 + (Turb_eff_RC * (H_RC4s - H_RC3)) # kJ/kg
        H_RC4_joules = H_RC4 * 1000 # Enthalpy in J/kg for calculations
        T_RC4 = self._py_CoolProp_CoolProp_PropsSI('T','P',P_RC4,'H',H_RC4_joules,"Water") # K
        S_RC4 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_RC4,'H',H_RC4_joules,"Water")/1000 # kJ/kg·K
        X_RC4 = (S_RC4 - S_RC_P4_f) / (S_RC_P4_g - S_RC_P4_f) # Steam quality at state 4
        W_turbine_real_RC = W_turbine_ideal_RC * Turb_eff_RC # Real work delivered by the turbine, kJ/s EQ 18 - DOC 3
        Gen_power_RC = W_turbine_real_RC * Gen_eff_RC # Electrical power delivered to the grid by the RC, kJ/s EQ 18 - DOC 3
        I_turbine_RC = m_jw_RC * T_env * (S_RC4 - S_RC3) # Irreversibilities of turbine, kJ/s EQ 19 - DOC 3
        # Condenser (Counterflow JW / SW - Cool source, 4 and RC1)
        T_cond_RC = self._py_CoolProp_CoolProp_PropsSI('T','P',P_RC4,'Q',1,"Water") # Condensation temperature of jacket water at P_4, K
        Q_cond_jw_RC = m_jw_RC * Cp_jw * (T_RC4 - T_1) # Heat to disipate into Sea Water in order to fully condense Jacket Water, kJ/s
        Q_cond_RC = m_jw_RC * (H_RC4 - H_1) # Total heat on condenser, kJ/s EQ 20 - DOC 3
        
        # 3. ORC
        # Operational desired conditions
        if (ORC_Superheat < 0):
            self._warndlg ({'Organic Rankine Superheating is too low.'},'Warning') # Minimum superheating: 0 K
        
        if (ORC_Superheat > 25):
            self._warndlg ({'Organic Rankine Superheating is too high.'},'Warning') # Maximum superheating: 25 K
        
        if (ORC_Subcool < 0):
            self._warndlg ({'Organic Rankine Subcooling is too low.'},'Warning') # Minimum subcooling: 0 K
        
        if (ORC_Subcool > 25):
            self._warndlg ({'Organic Rankine Subcooling is too high.'},'Warning') # Maximum subcooling: 25 K
        
        # Operation conditions
        T_evap_jw_ORC_in = T_D2 # Jacket water temperature at the inlet of ORC evaporator, K
        T_evap_jw_ORC_out = 55 + 273.15 # Jacket water temperature at the outlet of the ORC evaporator, K
        T_cond_ORC = T_sw_in + 5 # Estimated temperature of condensation for the ORC, K - OPERATIONAL CONDITION
        P_cond_ORC = self._py_CoolProp_CoolProp_PropsSI('P','T',T_cond_ORC,'Q',1,self._getDefaultFluidCode()) # Condensation pressure of ORC at the estimated T_cond_ORC, Pa
        Cp_ORC = self._py_CoolProp_CoolProp_PropsSI('Cpmass','T',T_cond_ORC,'Q',0,self._getDefaultFluidCode())/1000 # Cp of ORC fluid, kJ/kg·K
        Q_evap_jw_ORC = m_jw_ORC * Cp_jw * (T_evap_jw_ORC_in - T_evap_jw_ORC_out) # Available heat for ORC on jacket water, kJ/s
        # ORC Condenser outlet (Subcooled liquid before pump, 1)
        T_ORC1 = T_cond_ORC - ORC_Subcool # Temperature at state 1 of ORC, K
        P_ORC1 = P_cond_ORC # Pressure at state 1 of ORC, Pa
        H_ORC1 = self._py_CoolProp_CoolProp_PropsSI('H','T',T_ORC1,'P',P_ORC1,self._getDefaultFluidCode())/1000 # kJ/kg
        S_ORC1 = self._py_CoolProp_CoolProp_PropsSI('S','T',T_ORC1,'P',P_ORC1,self._getDefaultFluidCode())/1000 # kJ/kg·K
        D_ORC1 = self._py_CoolProp_CoolProp_PropsSI('D','T',T_ORC1,'P',P_ORC1,self._getDefaultFluidCode()) # kg/m3
        SpecVol_ORC1 = 1/D_ORC1 # m3/kg
        # ORC Pump (Liquid pumped, ORC2s and ORC2)
        P_ORC2 = P_ORC1 + ORC_Pump # Pa
        S_ORC2s = S_ORC1 # kJ/kg
        w_spec_pump_ORC_ideal = (SpecVol_ORC1 * (P_ORC2 - P_ORC1))/1000 # Specific work introduced on the ORC pump, kJ/kg EQ 28 - DOC 3
        H_ORC2s = w_spec_pump_ORC_ideal + H_ORC1 # Enthalpy at state 2s of ORC, kJ/kg
        H_ORC2 = ((H_ORC2s - H_ORC1)/ORC_Pump_eff) + H_ORC1 # Enthalpy at state 2 of ORC, kJ/kg
        H_ORC2_joules = H_ORC2 * 1000 # Enthalpy in J/kg for the correct calculation of T_ORC2 and S_ORC2
        T_ORC2 = self._py_CoolProp_CoolProp_PropsSI('T','P',P_ORC2,'H',H_ORC2_joules,self._getDefaultFluidCode()) # Temperature of the jacket water at the outlet of the pump, K
        S_ORC2 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_ORC2,'H',H_ORC2_joules,self._getDefaultFluidCode())/1000 # Entropy of the jacket water at the outlet of the pump, kJ/kg·K
        T_evap_ORC = self._py_CoolProp_CoolProp_PropsSI('T','P',P_ORC2,'Q',0,self._getDefaultFluidCode()) # Vaporization temperature of ORC fluid, K
        T_ORC3 = T_evap_ORC + ORC_Superheat # Temperature of ORC fluid at the outlet of evaporator, K
        T_crit = self._py_CoolProp_CoolProp_PropsSI('Tcrit',self._getDefaultFluidCode()) # Critical temperature of the ORC fluid
        if (T_crit < T_ORC3):
            self._warndlg ({'Organic Rankine Cycle is on Supercritical state.'},'Warning')
        
        P_ORC3 = P_ORC2 - 10000 # Drop of pressure inside ORC evaporator, Pa
        H_ORC3 = self._py_CoolProp_CoolProp_PropsSI('H','T',T_ORC3,'P',P_ORC3,self._getDefaultFluidCode())/1000 # kJ/kg
        m_ORC = Q_evap_jw_ORC / ((Cp_ORC * (T_evap_ORC - T_ORC2)) + (H_ORC3 - H_ORC2) + (Cp_ORC * ORC_Superheat)) # Mass flow of ORC fluid inside the circuit, kg/s
        W_pump_ideal_ORC = (m_ORC * w_spec_pump_ORC_ideal) # Work ideally needed by the ORC pump, kJ/s EQ 28 - DOC 3
        W_pump_real_ORC = W_pump_ideal_ORC / ORC_Pump_eff # Work introduced on the ORC pump, kJ/s EQ 28 - DOC 3
        I_pump_ORC = m_ORC * T_env * (S_ORC2 - S_ORC1) # Irreversibilities on the ORC pumping process, kJ/s EQ 29 - DOC 3
        # ORC Evaporator (Counterflow JW / ORC fluid, ORC3)
        S_ORC3 = self._py_CoolProp_CoolProp_PropsSI('S','T',T_ORC3,'P',P_ORC3,self._getDefaultFluidCode())/1000 # kJ/kg·K
        T_avg_ORC = (T_evap_jw_ORC_in - T_evap_jw_ORC_out) / math.log (T_evap_jw_ORC_in / T_evap_jw_ORC_out) # Exhaust average temperature inside the evaporator, K
        I_evap_jw_ORC = Q_evap_jw_ORC * (1 - (T_env / T_avg_ORC)) # Irreversibilities of the jacket water on ORC evaporator, kJ/s EQ 31 - DOC 3
        I_evap_ORC = m_ORC * (H_ORC3 - H_ORC2 - (T_env * (S_ORC3 - S_ORC2))) # Irreversibilities of the ORC fluid on ORC evaporator, kJ/s EQ 32 - DOC 3
        I_evap_ORC_total = I_evap_jw_ORC + I_evap_ORC # Total irreversibilities on ORC evaporator, kJ/s EQ 33 - DOC 3
        # ORC Turbine (Expansion, ORC4)
        Turb_eff_ORC = 0.8 # ORC Turbine efficiency - OPERATIONAL CONDITION
        Gen_eff_ORC = 0.96 # ORC Generator efficiency - OPERATIONAL CONDITION
        P_ORC4 = P_ORC1 + 10000 # Loss of pressure in condenser, Pa - OPERATIONAL CONDITION
        S_ORC4s = S_ORC3 # Isentropic process, kJ/kg·K
        S_P4_f_ORC = self._py_CoolProp_CoolProp_PropsSI('S','P',P_ORC4,'Q',0,self._getDefaultFluidCode())/1000 # kJ/kg·K
        S_P4_g_ORC = self._py_CoolProp_CoolProp_PropsSI('S','P',P_ORC4,'Q',1,self._getDefaultFluidCode())/1000 # kJ/kg·K
        X_ORC4s = (S_ORC4s - S_P4_f_ORC) / (S_P4_g_ORC - S_P4_f_ORC) # Steam quality at state 4s
        S_ORC4s_joules = S_ORC3 * 1000 # Entropy in J/kg·K for calculations
        H_P4_f_ORC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_ORC4,'Q',0,self._getDefaultFluidCode())/1000 # kJ/kg
        H_P4_g_ORC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_ORC4,'Q',1,self._getDefaultFluidCode())/1000 # kJ/kg
        H_ORC4s = H_P4_f_ORC + (X_ORC4s * (H_P4_g_ORC - H_P4_f_ORC)) # kJ/kg
        W_turbine_ideal_ORC = (m_ORC * (H_ORC3 - H_ORC4s)) # Ideal work delivered by ORC turbine, kJ/s
        H_ORC4 = H_ORC3 + (Turb_eff_ORC * (H_ORC4s - H_ORC3))/1000 # kJ/kg
        H_ORC4_joules = H_ORC4 * 1000 # Enthalpy in J/kg for calculations
        T_ORC4 = self._py_CoolProp_CoolProp_PropsSI('T','P',P_ORC4,'H',H_ORC4_joules,self._getDefaultFluidCode()) # K
        S_ORC4 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_ORC4,'H',H_ORC4_joules,self._getDefaultFluidCode())/1000 # kJ/kg·K
        X_ORC4 = (S_ORC4 - S_P4_f_ORC) / (S_P4_g_ORC - S_P4_f_ORC) # Steam quality at state 4
        W_turbine_real_ORC = W_turbine_ideal_ORC * Turb_eff_ORC # Real work delivered by the ORC turbine, kJ/s EQ 34 - DOC 3
        Gen_power_ORC = W_turbine_real_ORC * Gen_eff_ORC # Electrical power delivered to the grid by the ORC, kJ/s EQ 34 - DOC 3
        I_turbine_ORC = m_ORC * T_env * (S_ORC4 - S_ORC3) # Irreversibilities on the turbine, kJ/s EQ 35 - DOC 3
        # ORC Condenser (Liquid, ORC1)
        H_sat_vap_ORC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_ORC4,'Q',1,self._getDefaultFluidCode())/1000 # Enthalpy of ORC saturated vapor at P_2c, kJ/kg
        H_sat_liq_ORC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_ORC4,'Q',0,self._getDefaultFluidCode())/1000 # Enthalpy of ORC saturated liquid at P_2c, kJ/kg
        Q_cond_ORC = m_ORC * ((Cp_ORC * (T_ORC4 - T_cond_ORC)) + (H_sat_vap_ORC - H_sat_liq_ORC) + (Cp_ORC * ORC_Subcool)) # Total heat on condenser, kJ/s EQ 36 - DOC 3
        
        # 4. THERMOELECTRIC GENERATORS
        A_TEG = 0.0016 # Area of a 40x40 mm TEG module, m2
        A_engine = 35.81 # Area of engine block + CAC + LOC, m2
        Occup_factor = ((N_TEG * A_TEG) / A_engine) * 100 # Occupancy ratio of the TEG module inside the engine
        if (Occup_factor > 100):
            self._warndlg ({'TEGs installed exceed the engine area.'},'Warning') 
        

        
        # 5. SEA WATER CONDITIONS
        H_sw_in = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_in,'T',T_sw_in,"Water")/1000 # Enthalpy of sea water at the inlet of the condenser, kJ/kg
        S_sw_in = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_in,'T',T_sw_in,"Water")/1000 # Entropy of sea water at the inlet of the condenser, kJ/kg
        T_sw_out_ORC_1 = T_sw_in + (Q_cond_ORC / (m_sw * Cp_sw)) # Sea water temperature at the outlet of ORC condenser, K
        P_sw_out_ORC_1 = P_sw_in - 10000 # Loss of pressure on ORC condenser, Pa
        H_sw_out_ORC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_out_ORC_1,'T',T_sw_out_ORC_1,"Water")/1000 # Enthalpy of sea water at the outlet of ORC condenser, kJ/kg
        S_sw_out_ORC = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_out_ORC_1,'T',T_sw_out_ORC_1,"Water")/1000 # Entropy of sea water at the outlet of ORC condenser, kJ/kg·K
        T_sw_in_RC_2 = T_sw_out_ORC_1
        P_sw_in_RC_2 = P_sw_out_ORC_1
        H_sw_in_RC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_in_RC_2,'T',T_sw_in_RC_2,"Water")/1000 # Enthalpy of sea water at the inlet of RC condenser, kJ/kg
        S_sw_in_RC = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_in_RC_2,'T',T_sw_in_RC_2,"Water")/1000 # Entropy of sea water at the inlet of RC condenser, kJ/kg·K
        T_sw_out_RC_2 = T_sw_in_RC_2 + (Q_cond_jw_RC / (m_sw * Cp_sw)) # Sea water temp at the outlet of the evaporator, K
        P_sw_out_RC_2 = P_sw_in_RC_2 - 10000 # Loss of pressure on RC condenser, Pa
        H_sw_out_RC = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_out_RC_2,'T',T_sw_out_RC_2,"Water")/1000 # Enthalpy of sea water at the outlet of RC condenser, kJ/kg
        S_sw_out_RC = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_out_RC_2,'T',T_sw_out_RC_2,"Water")/1000 # Entropy of sea water at the outlet of RC condenser, kJ/kg·K
        T_sw_in_DES_3 = T_sw_out_RC_2
        P_sw_in_DES_3 = P_sw_out_RC_2
        H_sw_in_DES_3 = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_in_DES_3,'T',T_sw_in_DES_3,"Water")/1000 # Enthalpy of sea water at the inlet of the desalination, kJ/kg
        S_sw_in_DES_3 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_in_DES_3,'T',T_sw_in_DES_3,"Water")/1000 # Entropy of sea water at the inlet of the desalination, kJ/kg·K
        P_sw_out_DES_3 = P_sw_in_DES_3 - 10000 # Loss of pressure on desalination condenser, Pa
        T_sw_out_DES_3 = T_sw_in_DES_3 # Sea water general outlet from desalination, K - ASSUMED ALL HEAT GOES INTO EVAPORATION
        T_sw_out_DES_3_distillate = T_D2 - Pinch_point_des # Sea water outlet temperature according to Pinch Point, K
        if (T_des >= T_sw_out_DES_3_distillate):
            self._warndlg ({'The vaporization temperature of the desalination process is higher than the pinch point selected.'},'Error')
        
        H_sw_out_DES_3 = self._py_CoolProp_CoolProp_PropsSI('H','P',P_sw_out_DES_3,'T',T_sw_out_DES_3,"Water")/1000 # Enthalpy of sea water at the outlet of the desalination, kJ/kg
        S_sw_out_DES_3 = self._py_CoolProp_CoolProp_PropsSI('S','P',P_sw_out_DES_3,'T',T_sw_out_DES_3,"Water")/1000 # Entropy of sea water at the outlet of the desalination, kJ/kg·K
        H_sw_DES_3_f = (self._py_CoolProp_CoolProp_PropsSI('H','P',P_chamber,'Q',0,"Water"))/1000 # kJ/kg
        H_sw_DES_3_g = (self._py_CoolProp_CoolProp_PropsSI('H','P',P_chamber,'Q',1,"Water"))/1000 # kJ/kg
        m_sw_distillate = Q_sw_des / ((Cp_sw * (T_des - T_sw_in_DES_3)) + (H_sw_DES_3_g - H_sw_DES_3_f) + (Cp_sw * (T_sw_out_DES_3_distillate - T_des))) # Mass flow of distillate, kg/s
        m_sw_distillate_hour = m_sw_distillate * 3600 # Mass flow of distillate, kg/s
        m_sw_out_DES_3 = m_sw - m_sw_distillate # Not vaporized sea water, kg/s
        T_sw_in_TEG_4 = T_sw_out_DES_3
        
        # NEW LINE
        TEG_cold=T_sw_in_TEG_4 # NEW LINE
        
        if (TEG_cold >= TEG_hot):
            self._warndlg ({'Thermoelectric modules temperatures are not consistent.'},'Warning')
   
        

        
        # RC Condenser
        I_cond_jw = m_jw_RC *(H_RC4 - H_1 - (T_env * (S_RC4 - S_1))) # Irreversibilities of the jacket water on condenser, kJ/s EQ 21 - DOC 3
        I_cond_sw_RC = m_sw * (H_sw_out_RC - H_sw_in_RC - (T_env * (S_sw_out_RC - S_sw_in_RC))) # Irreversibilities of the sea water on condenser, kJ/s EQ 22 - DOC 3
        I_cond_RC_total = I_cond_jw + I_cond_sw_RC # Total irreversibilities on the condenser, kJ/s EQ 23 - DOC 3
        # ORC Condenser
        I_cond_ORC = m_ORC *(H_ORC1 - H_ORC4 - (T_env * (S_ORC1 - S_ORC4))) # Irreversibilities of the ORC fluid on condenser, kJ/s EQ 37 - DOC 3
        I_cond_sw_ORC = m_sw * (H_sw_in - H_sw_out_ORC - (T_env * (S_sw_in - S_sw_out_ORC))) # Irreversibilities of the sea water on condenser, kJ/s EQ 38 - DOC 3
        I_cond_ORC_total = I_cond_ORC + I_cond_sw_ORC # Total irreversibilities on the condenser, kJ/s EQ 39 - DOC 3
        # Desalination
        W_des_pump = 10.4 # Real work from the pump of the desalination system and ejector, kJ/s - ITUR Normabloc N2-40/160B/7.5-2900 rpm (40.8 m3/h at 2.4 bar)
        Daily_distillate = (m_sw_distillate * 3600 * 24 ) / Sw_density # Daily fresh water production, m3
        
        
        Q_TEG = Heat_block * (Occup_factor / 100) # Percentage of heat block, CAC and LOC used on the TEGs, kJ/s
        TEG_gradient = TEG_hot - TEG_cold # Temperature gradient of TEG between faces, K
        if (TEG_gradient <= 60):
           TEG_output = 0.901 * N_TEG # Amount of energy recovered, Watts
        elif (61 <= TEG_gradient):
           TEG_output = 3.299 * N_TEG # Amount of energy recovered, Watts 
        
        if (121 <= TEG_gradient):
           TEG_output = 6.299 * N_TEG # Amount of energy recovered, Watts 
        
        TEG_output_kW = TEG_output / 1000 # kW     
        
        T_sw_out_TEG_4 = T_sw_in_TEG_4 + (Q_TEG / (m_sw_out_DES_3 * Cp_sw)) # Cooling of TEG with the remaining sea water on system
        P_sw_in_TEG_4 = P_sw_out_DES_3
        P_sw_out_TEG_4 = P_sw_in_TEG_4 - 10000 # Loss of pressure on TEG cooler, Pa
        if (T_sw_out_TEG_4 >= 333.15):
            self._warndlg ({'Sea water is exiting the WHRS at a temperature over 60 ºC.'},'Error')
        
        if (P_sw_out_TEG_4 <= 100000):
            self._warndlg ({'Sea water is exiting the WHRS at a pressure lower than 1 bar.'},'Error')
        
        
        # 6. WHRS PERFORMANCE
        # Rankine cycle performance
        Heat_input_RC = (Q_engine * (m_jw_RC / m_jw)) + Q_exh # Heat available from hot current, kJ/s
        Cycle_output_RC = W_turbine_real_RC - W_pump_real # Total work on the cycle, kJ/s
        Cycle_output_gen_RC = Gen_power_RC - W_pump_real # Total work recovered, kJ/s EQ 24 - DOC 3
        Cycle_eff_RC = (Cycle_output_gen_RC / Heat_input_RC) * 100 # Real efficiency of the cycle (Electrical power vs. Exh gas heat) EQ 26 - DOC 3
        Irreversibilities_RC = I_pump_RC + I_engine_RC + I_evap_RC_total + I_turbine_RC + I_cond_RC_total # Total irreversibilities of the cycle, kJ/s EQ 25 - DOC 3
        Exergy_eff_RC = (Cycle_output_gen_RC / (Cycle_output_gen_RC + Irreversibilities_RC))*100 # Exergy efficiency of the RC cycle EQ 27 - DOC 3
        # ORC performance
        Heat_input_ORC = Q_evap_jw_ORC # Heat available from hot current, kJ/s
        Cycle_output_ORC = W_turbine_real_ORC - W_pump_real_ORC # Total work on the cycle, kJ/s
        Cycle_output_gen_ORC = Gen_power_ORC - W_pump_real_ORC # Total work recovered, kJ/s EQ 40 - DOC 3
        Cycle_eff_ORC = (Cycle_output_gen_ORC / Heat_input_ORC) * 100 # Real efficiency of the cycle (Electrical power vs. Jacket water heat) EQ 42 - DOC 3
        Irreversibilities_ORC = I_pump_ORC + I_evap_ORC_total + I_turbine_ORC + I_cond_ORC_total # Total irreversibilities of the cycle, kJ/s EQ 41 - DOC 3
        Exergy_eff_ORC = (Cycle_output_gen_ORC / (Cycle_output_gen_ORC + Irreversibilities_ORC))*100 # Exergy efficiency of the ORC cycle EQ 43 - DOC 3
        # TEG performance
        TEG_eff = (TEG_output_kW / Q_TEG) * 100 # Efficiency of the TEG
        T_avg_TEG = (TEG_hot - TEG_cold) / math.log (TEG_hot / TEG_cold) # Average temperature inside the TEGs, K EQ 46 - DOC 3
        I_TEG = Q_TEG * (1 - (T_env / T_avg_TEG)) # Irreversibilities on the TEG, kJ/s EQ 45 - DOC 3
        Exergy_eff_TEG = (TEG_output_kW / (TEG_output_kW + I_TEG))*100 # Exergy efficiency of TEG system EQ 44 - DOC 3
        # Desalination performance
        Desalination_eff = (Q_sw_des_equivalent / (Q_jw_des + W_des_pump))*100 # Efficiency of the desalination process
        T_avg_des = (T_D2 - T_D3) / math.log (T_D2 / T_D3) # Average temperature of jacket water inside desalination system, K
        I_des_jw = Q_jw_des * (1 - (T_env / T_avg_des)) # Irreversibilities of jacket water, kJ/s
        I_des_sw = m_sw * (H_sw_in_DES_3 - H_sw_out_DES_3 - (T_env * (S_sw_in_DES_3 - S_sw_out_DES_3))) # Irreversibilities of sea water, kJ/s
        I_des = I_des_jw + I_des_sw # Total irreversibilities on desalination process, kJ/s
        Exergy_eff_DES = (Q_sw_des_equivalent / (Q_jw_des + I_des))*100 # Exergy efficiency of desalination system
        # Entire WHRS performance
        WHRS_heat_input = Heat_input_RC + Heat_input_ORC + Q_TEG + Q_jw_des # Total heat input for WHRS, kJ/s
        WHRS_cycle_output = Cycle_output_gen_RC + Cycle_output_gen_ORC + TEG_output_kW + Q_sw_des_equivalent # Total output of WHRS, kJ/s
        WHRS_eff = (WHRS_cycle_output / WHRS_heat_input)*100 # Thermal efficiency of WHRS
        I_WHRS = Irreversibilities_RC + Irreversibilities_ORC + I_TEG + I_des # Irreversibilities of WHRS, kJ/s
        Exergy_eff_WHRS = (WHRS_cycle_output / (WHRS_cycle_output + I_WHRS))*100 # Exergy efficiency of WHRS
        
        # 7. FUEL SAVINGS DOC 3 - FUEL SAVINGS
        Fuel_savings_RC = FO_Consumption * Cycle_output_gen_RC # Fuel saved due to RC, g/h
        Fuel_savings_ORC = FO_Consumption * Cycle_output_gen_ORC # Fuel saved due to ORC, g/h
        Fuel_savings_TEG = FO_Consumption * TEG_output_kW # Fuel saved due to TEGs, g/h
        Fuel_savings_DES = FO_Consumption * Q_sw_des_equivalent # Fuel used on desalination, g/h
        Fuel_savings_WHRS = Fuel_savings_RC + Fuel_savings_ORC + Fuel_savings_TEG + Fuel_savings_DES # Total FO savings with the whole WHRS, g/h
        Total_output = Power + Cycle_output_gen_RC + Cycle_output_gen_ORC + TEG_output_kW + Q_sw_des_equivalent # Total power output with WHRS, kJ/s
        New_FO = (Power * FO_Consumption) / Total_output # New FO consumption with WHRS, g/kW·h
        Fuel_savings_perc = 100 - ((New_FO / FO_Consumption) * 100) # Percentage of fuel saved with TEG installed
        
        # Eff Final Output
        if self.verbose>=1:
            print('Exergy_eff_WHRS={}'.format(Exergy_eff_WHRS))
        
        #****  CO2 reduction
        TotalFOCons=New_FO*Power
        Daily_W_FOCons=(TotalFOCons*24)/1000
        CO2_W_day=Daily_W_FOCons*3.206
        
        
        FO_consumption_WO=self._calculateFO_consumption_WO(Load)
        TotalFO_WO_Cons=FO_consumption_WO*Power
        Daily_WO_FO=(TotalFO_WO_Cons*24)/1000
        CO2_WO_day=Daily_WO_FO*3.206
        
        CO2_red=(1-(CO2_W_day/CO2_WO_day))*100
        if self.verbose>=1:
            print('CO2_red={}'.format(CO2_red))
        
        #**** Economic
        Ctot=76580.6116 # B52
        CRF=0.13387878  # B53
        fk=8            # B54
        t=5000          # B55
        
        EPC=(Ctot*(CRF+fk))/(WHRS_cycle_output*t)
        if self.verbose>=1:
            print('EPC={}'.format(EPC))
            
        # Save dictPropSI
        self._savePropSI()
        
        # Store params
        self.params_value[0]=Load
        self.params_value[1]=FO_Consumption
        self.params_value[2]=Exh_in
        self.params_value[3]=m_exh
        self.params_value[4]=T_D2
        self.params_value[5]=JW_pump
        self.params_value[6]=Pump_eff
        self.params_value[7]=Heat_block
        self.params_value[8]=T_sw_in
        self.params_value[9]=P_sw_in
        self.params_value[10]=Power
        self.params_value[11]=RC_Superheat
        self.params_value[12]=RC_Subcool
        self.params_value[13]=ORC_Superheat
        self.params_value[14]=ORC_Subcool
        self.params_value[15]=ORC_Pump / 100000
        self.params_value[16]=ORC_Pump_eff
        self.params_value[17]=P_chamber / 100000
        self.params_value[18]=Pinch_point_des
        self.params_value[19]=T_des_surface 
        self.params_value[20]=N_TEG
        self.params_value[21]=TEG_hot   
        self.params_value[22]=TEG_cold   
        self.params_value[23]=WHRS_cycle_output  
        self.params_value[24]=CO2_red   
        self.params_value[25]=EPC        
        
        return (WHRS_cycle_output,CO2_red,EPC)
        
    def _HeaderName(self,N,T):
        return '{}_{}'.format(N,T)

    def getHeader(self):
        Header=''
        first=True
        for NT in self.params_name_type:
            Name=self._HeaderName(NT[0],NT[1])
            if first:
                Header=Name
                first=False
            else:
                Header=Header+','+Name
        return Header
    
    def getStrValues(self):
        Row=''
        first=True
        for v in self.params_value:
            strv='{}'.format(v)
            if first:
                Row=strv
                first=False
            else:
                Row=Row+','+strv
        return Row
    
    def getValues(self):
        Row=[]
        first=True
        for v in self.params_value:
            Row.append(v)
        return Row
        
# Example of use

# CP.PropsSI("H","T",328.15,"P",15762.10154-1,"Water")

# JW_Pump sería 3,47664 Bar
# ORC_Pump = 5,59730
# P_chamber = 0,15

# EF=WHRS(verbose=1)
# EF(Load=60.0,JW_pump=3.15,RC_Superheat=8.022159028375663,RC_Subcool=1e-4,ORC_Superheat=1e-3,ORC_Subcool=1e-3,ORC_Pump=6.6,P_chamber=0.2)
# print(EF.getHeader())
# print(EF.getValues())


