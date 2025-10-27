import pandas as pd
import sys
arp_before = 'reports/arp-October-21_18-57.csv'
arp_after = 'reports/arp-October-21_18-59.csv'

route_before = "reports/routes-October-26_19-53.csv"
route_after = "reports/routes-October-26_19-54.csv"

def compareArp(before,after):
    df1 = pd.read_csv(before,index_col=0)
    df2 = pd.read_csv(after,index_col=0)
    df_merged1 = df1.merge(df2, on=['ip', 'mac'], how='left', indicator=True)
    missing_after = df_merged1[df_merged1['_merge'] == 'left_only'].drop('_merge', axis=1)
    print ('Missing Enteries')
    print(missing_after)
    df_merged2 = df2.merge(df1, on=['ip', 'mac'], how='left', indicator=True)
    extra_after = df_merged2[df_merged2['_merge'] == 'left_only'].drop('_merge', axis=1)
    print ('Extra Enteries')
    print(extra_after)

def compareRoute(before,after):
    df1 = pd.read_csv(before,index_col=0).drop(columns=['updated1','updated2'],axis=1)
    df2 = pd.read_csv(after,index_col=0).drop(columns=['updated1','updated2'],axis=1)  
    merged1 = df1.merge(df2, how='left', indicator=True)
    missingDf = merged1[merged1['_merge'] == 'left_only'].drop(columns='_merge',axis=1)
    print ('Missing Routes:')
    print (missingDf)
    merged2 = df2.merge(df1, how='left', indicator=True)
    extraDf = merged2[merged2['_merge'] == 'left_only'].drop(columns='_merge',axis=1)
    print ('Extra Routes:')
    print (extraDf)
    


b = compareRoute(route_before,route_after)
#a = compareArp(arp_before,arp_after)

