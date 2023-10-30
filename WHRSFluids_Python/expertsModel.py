#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: quevedo
"""

def getExperts():
    experts=[('ALFONSO',2480),('NOELIA',2481),('RUBEN',2482)]
    return experts



def expNames(experts):
    Names=''
    for e in experts:
        Names=Names+'_'+e[0]
    return Names



def getFileModel():
    return 'rankModel{}.csv'.format(expNames(getExperts()))