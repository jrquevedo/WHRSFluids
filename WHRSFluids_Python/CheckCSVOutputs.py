#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: quevedo
"""

import csv
from WHRS import WHRS

csvFile='20221125_Casos_WHRS.csv'

# Read csv
RemoveExtraPars=True 
ExtraPars=[23,25,26]

header=''
VRows=[]
with open(csvFile) as csvf:
    first=True
    csvreader = csv.reader(csvf, delimiter=',')
    for crow in csvreader:
        if RemoveExtraPars:
            row=[]
            for ir in range(len(crow)):
                if ir not in ExtraPars:
                    row.append(crow[ir])
        else:
            row=crow
        if first:
            header=row
            first=False
        else:
            VRow=[float(s) for s in row]
            VRows.append(VRow)

# Check each row

def checkRow(header,row,vheader,values):
    vvheader=vheader.split(',')
    for i in range(len(row)):
        dif=abs(row[i]-values[i])
        if dif>1e-5:
            print('{}{:2} CSV {}={:6.4f} Calculated {}={:6.4f} Dif={:6.4f}'
                      .format('**' if dif>1e-5 else '  ',
                          i,header[i],row[i],vvheader[i],values[i],dif))

#indexes of inputs for WHRS
iLoad=0
iJW_pump=5
iRC_Superheat=11
iRC_Subcool=12
iORC_Superheat=13
iORC_Subcool=14
iORC_Pump=15
iP_chamber=17



rs=WHRS(verbose=1)
for irow in range(len(VRows)):
    row=VRows[irow]
    if row[iJW_pump]>100:
        row[iJW_pump]=row[iJW_pump]/100000
    if row[iORC_Pump]>100:
        row[iORC_Pump]=row[iORC_Pump]/100000
    if row[iP_chamber]>100:
        row[iP_chamber]=row[iP_chamber]/100000
        
    (Exergy_eff_WHRS,CO2_red,EPC)=rs(row[iLoad],row[iJW_pump],row[iRC_Superheat],row[iRC_Subcool],
                                     row[iORC_Superheat],row[iORC_Subcool],row[iORC_Pump],row[iP_chamber])
    checkRow(header,row,rs.getHeader(),rs.getValues())    

