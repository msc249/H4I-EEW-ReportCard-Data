import pandas as pd


# ### 7. Number of currently active facilities regulated in CAA, CWA, RCRRA, GHGRP
# * The program_count() function looks at the ECHO_EXPORTER data that is passed in and counts the number of facilities have the 'flag' parameter set to 'Y' (AIR_FLAG, NPDES_FLAG, RCRA_FLAG, GHG_FLAG)
# * cd_echo_data is a dictionary with key (state, cd), where the state_echo_data is filtered for records of the current CD.
# * cd_echo_active is a dictionary for active facilities in the CD.
# * The number of records from these dictionaries is written into a file named like 'active-facilities_All_pg3', in a directory identified by the state and CD, e.g. "LA2".


def program_count( echo_data, program, flag, state, cd ):
    count = echo_data.loc[echo_data[flag]=='Y'].shape[0]
    print( 'There are {} active facilities in {} CD {} tracked under {}.'.format( 
        str( count ), state, cd, program))
    return count


def get_rowdata( df, field, flag ):
    num_fac = df.loc[df[flag]=='Y'].shape[0]
    if ( num_fac == 0 ):
        return (0,0)
    count_viol = df.loc[((df[field].str.count("S") + 
                df[field].str.count("V")) >= 3)].shape[0]
    fraction_viol = count_viol/num_fac
    print( "    {} facilities with at least 3 quarters in non-compliance over the past 3 years".format( count_viol ))
    print( "    {:.2%} of active facilities with at least 3 quarters in non-compliance over the past 3 years".format( 
           fraction_viol ))
    return (count_viol, fraction_viol * 100.)


def get_cwa_df( df ):
    year = df["YEARQTR"].astype("str").str[0:4:1]
    df["YEARQTR"] = year
    df.rename( columns={'YEARQTR':'YEAR'}, inplace=True )
    # Remove fields not relevant to this graph.
    df = df.drop(columns=['FAC_LAT', 'FAC_LONG', 'FAC_ZIP', 
        'FAC_EPA_REGION', 'FAC_DERIVED_WBD', 'FAC_DERIVED_CD113',
        'FAC_PERCENT_MINORITY', 'FAC_POP_DEN', 'FAC_DERIVED_HUC'])
    d = df.groupby(pd.to_datetime(df['YEAR'], format="%Y").dt.to_period("Y")).sum()
    d.index = d.index.strftime('%Y')
    d = d[ d.index > '2000' ]
    d['Total'] = d.sum(axis=1)
    return( d )

def get_inspections( ds, ds_type ):
    df0 = ds.results[ ds_type ].dataframe
    if ( df0 is None ):
        return None
    else:
        df_pgm = df0.copy()
    if ( len( df_pgm ) > 0 ):
        df_pgm.rename( columns={ ds.date_field: 'Date',
                            ds.agg_col: 'Count'}, inplace=True )
        df_pgm = df_pgm.groupby(pd.to_datetime(df_pgm['Date'], 
                            format=ds.date_format, errors='coerce'))[['Count']].agg('count')
        df_pgm = df_pgm.resample('Y').sum()
        df_pgm.index = df_pgm.index.strftime('%Y')
        df_pgm = df_pgm[ df_pgm.index > '2000' ]
    else:
        print( "No records")
    return df_pgm
    

def get_events( ds, ds_type ):
    df0 = ds.results[ ds_type ].dataframe
    if ( df0 is None ):
        return None
    else:
        df_pgm = df0.copy()
    df_pgm.rename( columns={ ds.date_field: 'Date',
                        ds.agg_col: 'Count'}, inplace=True )
    
    try:
        df_pgm = df_pgm.groupby(pd.to_datetime(df_pgm['Date'], 
                        format=ds.date_format, errors='coerce'))[['Count']].agg('count')
    except ValueError:
        print( "Error with date {}".format(df_pgm['Date']))
    df_pgm = df_pgm.resample('Y').sum()
    df_pgm.index = df_pgm.index.strftime('%Y')
    df_pgm = df_pgm[ df_pgm.index >= '2001']
    return( df_pgm )

def get_num_events( ds, ds_type, state, cd, year ):
    df_pgm = get_events( ds, ds_type )
    if ( df_pgm is None ):
        return 0
    if ( len( df_pgm ) > 0 ):
        num_events = df_pgm[ df_pgm.index == year ]
        if ( num_events.empty ):
            return 0
        else:
            return num_events['Count'][0]
    
def get_num_facilities( data_sets, program, ds_type, year ):
    ds = data_sets[program]
    df0 = ds.results[ ds_type ].dataframe
    if ( df0 is None ):
        return 0
    else:
        df_pgm = df0.copy()
    if ( len( df_pgm ) > 0 ):
        df_pgm.rename( columns={ ds.date_field: 'Date',
                            ds.agg_col: 'Count'}, inplace=True )
        if ( program == 'CWA Violations' ):
            yr = df_pgm['Date'].astype( 'str' ).str[0:4:1]
            df_pgm['Date'] = pd.to_datetime( yr, format="%Y" )
        else:
            df_pgm['Date'] = pd.to_datetime( df_pgm['Date'], format=ds.date_format, errors='coerce' )
        df_pgm_year = df_pgm[ df_pgm['Date'].dt.year == year].copy()
        df_pgm_year['Date'] = pd.DatetimeIndex( df_pgm_year['Date']).year
        num_fac = len(df_pgm_year.index.unique())            
        return num_fac

def get_enf_per_fac( ds_enf, ds_type, num_fac, year ):
    df_pgm = get_enforcements( ds_enf, ds_type )
    if ( df_pgm is None or df_pgm.empty ):
        df_pgm = pd.DataFrame( [[None,None]], columns=['Num_enf_per_fac','Amt_enf_per_fac'])
        print("There were no enforcement actions taken in the focus year")
    else:
        df_pgm = df_pgm[ df_pgm.index == year ]
        if ( df_pgm.empty ):
            df_pgm['Num_enf_per_fac'] = None
            df_pgm['Amt_enf_per_fac'] = None
        else:
            df_pgm['Num_enf_per_fac'] = df_pgm.apply( 
              lambda row: None if ( num_fac == 0 ) else row.Count / num_fac, axis=1 )
            df_pgm['Amt_enf_per_fac'] = df_pgm.apply( 
              lambda row: None if ( num_fac == 0 ) else row.Amount / num_fac, axis=1 )
    return df_pgm
    
def get_enforcements( ds, ds_type ):
    df0 = ds.results[ ds_type ].dataframe
    if ( df0 is None ):
        return None
    else:
        df_pgm = df0.copy()
    if ( len( df_pgm ) > 0 ):
        df_pgm.rename( columns={ ds.date_field: 'Date',
                            ds.agg_col: 'Amount'}, inplace=True )
        if ds.name == "CWA Penalties":
            df_pgm['Amount'] = df_pgm['Amount'].fillna(0) +                     df_pgm['STATE_LOCAL_PENALTY_AMT'].fillna(0)                            
        df_pgm["Count"] = 1
        df_pgm = df_pgm.groupby(pd.to_datetime(df_pgm['Date'], 
                format="%m/%d/%Y", errors='coerce')).agg({'Amount':'sum','Count':'count'})

        df_pgm = df_pgm.resample('Y').sum()
        df_pgm.index = df_pgm.index.strftime('%Y')
        df_pgm = df_pgm[ df_pgm.index >= "2001" ]
    else:
        print( "No records")
    return df_pgm
    
def get_ghg_emissions( ds, ds_type ):
    df_result = ds.results[ ds_type ].dataframe
    if ( df_result is None ):
        print( "No records" )
        return None
    else:
        df_pgm = df_result.copy()
    if ( df_pgm is not None and len( df_pgm ) > 0 ):
        df_pgm.rename( columns={ ds.date_field: 'Date',
                            ds.agg_col: 'Amount'}, inplace=True )
        df_pgm = df_pgm.groupby(pd.to_datetime(df_pgm['Date'], 
                                format=ds.date_format, errors='coerce'))[['Amount']].agg('sum')
        df_pgm = df_pgm.resample('Y').sum()
        df_pgm.index = df_pgm.index.strftime('%Y')
        #df_pgm = df_pgm[ df_pgm.index == '2018' ]
    else:
        print( "No records")
    return df_pgm

def get_violations_by_facilities( df, action_field, flag, noncomp_field ):
    df = df.loc[ df[flag] == 'Y' ]
    df = df.copy()
    noncomp = df[ noncomp_field ]
    noncomp_count = noncomp.str.count('S') + noncomp.str.count('V')
    df['noncomp_qtrs'] = noncomp_count
    df = df[['FAC_NAME', 'noncomp_qtrs']]
    df.rename( columns={'FAC_NAME': 'num_facilities'}, inplace=True )
    df = df.fillna(0)
    df = df.groupby(['noncomp_qtrs']).count()
    return df