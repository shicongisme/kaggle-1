import numpy as np
import pandas as pd
from sklearn import *
from datetime import datetime
from sklearn.preprocessing import OneHotEncoder,LabelEncoder
from sklearn.preprocessing import StandardScaler
from geopy.distance import great_circle
#, parse_dates=['visit_date']
print ('Loading Data')
#air_visit = pd.read_csv('input/air_visit_data.csv', converters={'visitors': lambda u: np.log1p(
#        float(u)) if float(u) > 0 else 0})
air_visit = pd.read_csv('input/air_visit_data.csv')    
air_store = pd.read_csv('input/air_store_info.csv')
hpg_store = pd.read_csv('input/hpg_store_info.csv')
#air_reserve = pd.read_csv('input/air_reserve.csv', converters={'reserve_visitors': lambda u: np.log1p(
#        float(u)) if float(u) > 0 else 0})
air_reserve = pd.read_csv('input/air_reserve.csv')
#hpg_reserve = pd.read_csv('input/hpg_reserve.csv', converters={'reserve_visitors': lambda u: np.log1p(
#        float(u)) if float(u) > 0 else 0})
hpg_reserve = pd.read_csv('input/hpg_reserve.csv')
store_id = pd.read_csv('input/store_id_relation.csv')
date_info = pd.read_csv('input/date_info.csv').rename(columns={'calendar_date':'visit_date'})
sub = pd.read_csv('input/sample_submission.csv')
weather = pd.read_csv('input/weather.csv')

#def find_outliers(series):
#    return (series - series.mean()) > 2.4 * series.std()

#air_visit['is_outlier'] = air_visit.groupby('air_store_id').apply(lambda g: find_outliers(g['visitors'])).values
#air_visit = air_visit[air_visit['is_outlier'] == False]
#mean_decay = (air_visit['visitors']*np.power(0.9, np.arange(air_visit.shape[0])[::-1])).sum(axis=1).values
#air_visit['visitors'].diff().mean()
#print (mean_decay)
#tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].apply(pd.DataFrame.diff(axis=1).mean()).reset_index().rename(columns={'visitors':'min_visitors'})
#def calc_shifted_ewm(series, alpha, adjust=True):
#    return series.shift().ewm(alpha=alpha, adjust=adjust).mean().reset_index()

#prep_df['ewm'] = prep_df.groupby(['air_store_id', 'dow'])\
#                  .apply(lambda g: calc_shifted_ewm(g['visitors'], 0.1))
#                  .sort_index(level=['air_store_id', 'visit_date']).values

#tmp = data['tra'].groupby(['air_store_id','dow']).agg({'visitors' : [np.min,np.mean,np.median,np.max,np.size]}).reset_index()
#tmp.columns = ['air_store_id', 'dow', 'min_visitors', 'mean_visitors', 'median_visitors','max_visitors','count_observations']
#stores = pd.merge(stores, tmp, how='left', on=['air_store_id','dow']) 
print ('Loading Finished')

print ('Preprocessing Data')

# weather
#weather['visit_date'] = pd.to_datetime(weather[['year','month','day']]).astype(str)
#weather['mean_temperature'] = weather['max_temperature']*0.5 + weather['min_temperature']*0.5
#weather['max_temperature_lev'] = weather['max_temperature'].map(lambda x:1 if x<=0 else 2 if x>0 and x<10 else 3 if x>=10 and x<20 else 4 if x>=20 and x<30 else 5)
#weather['min_temperature_lev'] = weather['min_temperature'].map(lambda x:1 if x<=0 else 2 if x>0 and x<10 else 3 if x>=10 and x<20 else 4 if x>=20 and x<30 else 5)
#weather['precipitation_lev'] = weather['precipitation'].map(lambda x:1 if x<5 else 2 if x>=5 and x<30 else 3)
#weather.drop(['year','month','day'],axis=1, inplace=True)

# store
air_store['air_area_name_province'] = air_store['air_area_name'].map(lambda x: x.split(' ')[0])
air_store['air_area_name_city'] = air_store['air_area_name'].map(lambda x: x.split(' ')[1])
air_store['air_area_name_ward'] = air_store['air_area_name'].map(lambda x: x.split(' ')[2])
air_store.drop('air_area_name', axis=1, inplace=True)

# hpg reserve
hpg_reserve = pd.merge(hpg_reserve, store_id, how='inner', on=['hpg_store_id'])
hpg_reserve['visit_datetime'] = pd.to_datetime(hpg_reserve['visit_datetime'])
hpg_reserve['visit_datetime'] = hpg_reserve['visit_datetime'].dt.date
hpg_reserve['reserve_datetime'] = pd.to_datetime(hpg_reserve['reserve_datetime'])
hpg_reserve['reserve_datetime'] = hpg_reserve['reserve_datetime'].dt.date
hpg_reserve['reserve_datetime_diff'] = hpg_reserve.apply(lambda r: (r['visit_datetime'] - r['reserve_datetime']).days,axis=1)

tmp1 = hpg_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_datetime_diff','reserve_visitors']].sum().rename(columns={'visit_datetime':'visit_date', 'reserve_datetime_diff': 'reserve_diff_sum', 'reserve_visitors':'reserve_visitors_sum'})
tmp2 = hpg_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_datetime_diff', 'reserve_visitors']].mean().rename(columns={'visit_datetime':'visit_date', 'reserve_datetime_diff': 'reserve_diff_mean', 'reserve_visitors':'reserve_visitors_mean'})
#tmp3 = hpg_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_visitors']].count().rename(columns={'visit_datetime':'visit_date', 'reserve_visitors':'reserve_visitors_count'})
hpg_reserve = pd.merge(tmp1, tmp2, how='inner', on=['air_store_id','visit_date']) 
hpg_reserve = pd.merge(hpg_reserve, tmp3, how='inner', on=['air_store_id','visit_date']) 

hpg_reserve['visit_date'] = hpg_reserve['visit_date'].astype(str)

# air reserve
air_reserve['visit_datetime'] = pd.to_datetime(air_reserve['visit_datetime'])
air_reserve['visit_datetime'] = air_reserve['visit_datetime'].dt.date
air_reserve['reserve_datetime'] = pd.to_datetime(air_reserve['reserve_datetime'])
air_reserve['reserve_datetime'] = air_reserve['reserve_datetime'].dt.date
air_reserve['reserve_datetime_diff'] = air_reserve.apply(lambda r: (r['visit_datetime'] - r['reserve_datetime']).days,axis=1)

tmp1 = air_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_datetime_diff','reserve_visitors']].sum().rename(columns={'visit_datetime':'visit_date', 'reserve_datetime_diff': 'reserve_diff_sum', 'reserve_visitors':'reserve_visitors_sum'})
tmp2 = air_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_datetime_diff', 'reserve_visitors']].mean().rename(columns={'visit_datetime':'visit_date', 'reserve_datetime_diff': 'reserve_diff_mean', 'reserve_visitors':'reserve_visitors_mean'})
#tmp3 = air_reserve.groupby(['air_store_id','visit_datetime'], as_index=False)[['reserve_visitors']].count().rename(columns={'visit_datetime':'visit_date', 'reserve_visitors':'reserve_visitors_count'})
air_reserve = pd.merge(tmp1, tmp2, how='inner', on=['air_store_id','visit_date']) 
#air_reserve = pd.merge(air_reserve, tmp3, how='inner', on=['air_store_id','visit_date']) 

air_reserve['visit_date'] = air_reserve['visit_date'].astype(str)

# holiday
date_info['holiday'] = date_info.apply((lambda x:x.day_of_week=='Sunday' or x.day_of_week=='Saturday' or x.holiday_flg==1),axis=1).astype(int)
date_info.drop('holiday_flg', axis=1, inplace=True)

# submission
seasons = [0,0,1,1,1,2,2,2,3,3,3,0] #feb is winter, then spring, summer, fall

sub['air_store_id'] = sub['id'].map(lambda x: '_'.join(x.split('_')[:2]))
sub['visit_date'] = sub['id'].map(lambda x: str(x).split('_')[2])
test_id = sub['id']
sub.drop('id', axis=1, inplace=True)
sub['visit_datetime'] = pd.to_datetime(sub['visit_date'])
sub['year'] = sub['visit_datetime'].dt.year
#sub['quarter'] = sub['visit_datetime'].dt.quarter
sub['month'] = sub['visit_datetime'].dt.month
sub['yearmonth'] = sub['year'] + sub['month']
#sub['woy'] = sub['visit_datetime'].dt.weekofyear
sub['dow'] = sub['visit_datetime'].dt.dayofweek
sub['day'] = sub['visit_datetime'].dt.day
#sub['season'] = sub['month'].map(lambda x: seasons[(x - 1)])
#sub['salary_day'] = sub['day'].map(lambda x:1 if x==10 or x==25 else 0)
sub['date_int'] = sub['visit_datetime'].apply(lambda x: x.strftime('%Y%m%d')).astype(int)

sub  = pd.merge(sub, air_store,  how='inner', on='air_store_id')
sub  = pd.merge(sub, date_info, how='left',  on='visit_date')
#sub  = pd.merge(sub , weather, how='left',  on=['visit_date','air_area_name_province'])

# visit
air_visit['visit_datetime'] = pd.to_datetime(air_visit['visit_date'])
air_visit['year'] = air_visit['visit_datetime'].dt.year
#air_visit['quarter'] = air_visit['visit_datetime'].dt.quarter
air_visit['month'] = air_visit['visit_datetime'].dt.month
#air_visit['woy'] = air_visit['visit_datetime'].dt.weekofyear
air_visit['yearmonth'] = air_visit['year'] + air_visit['month']
air_visit['dow'] = air_visit['visit_datetime'].dt.dayofweek
air_visit['day'] = air_visit['visit_datetime'].dt.day
#air_visit['season'] = air_visit['month'].map(lambda x: seasons[(x - 1)])
#air_visit['salary_day'] = air_visit['day'].map(lambda x:1 if x==10 or x==25 else 0)
air_visit['date_int'] = air_visit['visit_datetime'].apply(lambda x: x.strftime('%Y%m%d')).astype(int)

air_visit  = pd.merge(air_visit, air_store,  how='inner', on='air_store_id')
air_visit  = pd.merge(air_visit , date_info, how='left',  on='visit_date')
#air_visit  = pd.merge(air_visit , weather, how='left',  on=['visit_date','air_area_name_province'])

# train data
prep_df = pd.merge(air_visit, hpg_reserve,  how='left', on=['air_store_id', 'visit_date'])
prep_df = pd.merge(prep_df, air_reserve,  how='left', on=['air_store_id', 'visit_date'])
#prep_df  = pd.merge(prep_df, air_store,  how='inner', on='air_store_id')
#prep_df  = pd.merge(prep_df , date_info, how='left',  on='visit_date')
prep_df = prep_df[prep_df['visit_date'] >= '2016-06-29']

prep_df  = prep_df.drop(['day_of_week','visit_datetime'],axis=1)

## dow visitors statistics
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].min().reset_index().rename(columns={'visitors':'dow_min_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].mean().reset_index().rename(columns={'visitors':'dow_mean_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].median().reset_index().rename(columns={'visitors':'dow_median_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].max().reset_index().rename(columns={'visitors':'dow_max_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].count().reset_index().rename(columns={'visitors':'dow_count_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].std().reset_index().rename(columns={'visitors':'dow_std_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'dow_skew_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'dow_kurt_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['air_store_id','dow'])
## genre-dow visitors statistics
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].mean().reset_index().rename(columns={'visitors':'genre_dow_mean_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].median().reset_index().rename(columns={'visitors':'genre_dow_median_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name'])
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].max().reset_index().rename(columns={'visitors':'genre_dow_max_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].count().reset_index().rename(columns={'visitors':'genre_dow_count_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].std().reset_index().rename(columns={'visitors':'genre_dow_std_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'genre_dow_skew_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'genre_dow_kurt_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_genre_name']) 
## province-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].mean().reset_index().rename(columns={'visitors':'province_dow_mean_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].median().reset_index().rename(columns={'visitors':'province_dow_median_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province'])
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].max().reset_index().rename(columns={'visitors':'province_dow_max_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].count().reset_index().rename(columns={'visitors':'province_dow_count_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].std().reset_index().rename(columns={'visitors':'province_dow_std_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'province_dow_skew_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'province_dow_kurt_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_province']) 
## province-city-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].mean().reset_index().rename(columns={'visitors':'city_dow_mean_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].median().reset_index().rename(columns={'visitors':'city_dow_median_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city'])
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].max().reset_index().rename(columns={'visitors':'city_dow_max_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].count().reset_index().rename(columns={'visitors':'city_dow_count_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].std().reset_index().rename(columns={'visitors':'city_dow_std_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'city_dow_skew_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'city_dow_kurt_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_city']) 
## province-city-ward-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].mean().reset_index().rename(columns={'visitors':'ward_dow_mean_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].median().reset_index().rename(columns={'visitors':'ward_dow_median_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward'])
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].max().reset_index().rename(columns={'visitors':'ward_dow_max_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].count().reset_index().rename(columns={'visitors':'ward_dow_count_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].std().reset_index().rename(columns={'visitors':'ward_dow_std_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'ward_dow_skew_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'ward_dow_kurt_visitors'})
prep_df = pd.merge(prep_df, tmp, how='left', on=['dow','air_area_name_ward']) 

## reserv stastistic
prep_df['total_reserv_sum'] = prep_df['reserve_visitors_sum_x'] + prep_df['reserve_visitors_sum_y']
prep_df['total_reserv_mean'] = (prep_df['reserve_visitors_mean_x'] + prep_df['reserve_visitors_mean_y']) / 2
prep_df['total_reserv_dt_diff_mean'] = (prep_df['reserve_diff_mean_x'] + prep_df['reserve_diff_mean_y']) / 2

## geo
prep_df['var_max_lat'] = prep_df['latitude'].max() - prep_df['latitude']
prep_df['var_max_long'] = prep_df['longitude'].max() - prep_df['longitude']
prep_df['lat_plus_long'] = prep_df['latitude'] + prep_df['longitude']

prep_df.fillna(-1, inplace=True)

def df_lbl_enc(df):
    for c in df.columns:
        if df[c].dtype == 'object':
            lbl = LabelEncoder()
            df[c] = lbl.fit_transform(df[c])
            print(c)
    return df

prep_df = df_lbl_enc(prep_df)
prep_df.to_csv('prep_df.csv')
#label = np.log1p(prep_df['visitors'].values)
label = prep_df['visitors'].values
prep_df = prep_df.drop(['visit_date','visitors'], axis=1)
prep_df_ohe = pd.get_dummies(prep_df, columns=['dow','air_genre_name','air_area_name_province','air_area_name_city','air_area_name_ward'], drop_first=True, sparse=True)

train = prep_df_ohe


#sc = StandardScaler()
#train = sc.fit_transform(train)   

# test data
predict_data = pd.merge(sub, hpg_reserve,  how='left', on=['air_store_id', 'visit_date'])
predict_data = pd.merge(predict_data, air_reserve,  how='left', on=['air_store_id', 'visit_date'])
#predict_data  = pd.merge(predict_data, air_store,  how='inner', on='air_store_id')
#predict_data  = pd.merge(predict_data , date_info, how='left',  on='visit_date')
predict_data  = predict_data.drop(['day_of_week','visit_datetime'],axis=1)

## dow visitors statistics
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].min().reset_index().rename(columns={'visitors':'dow_min_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].mean().reset_index().rename(columns={'visitors':'dow_mean_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].median().reset_index().rename(columns={'visitors':'dow_median_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].max().reset_index().rename(columns={'visitors':'dow_max_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].count().reset_index().rename(columns={'visitors':'dow_count_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].std().reset_index().rename(columns={'visitors':'dow_std_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow']) 
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'dow_skew_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow'])
tmp = air_visit.groupby(['air_store_id','dow'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'dow_kurt_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['air_store_id','dow'])
## genre-dow visitors statistics
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].mean().reset_index().rename(columns={'visitors':'genre_dow_mean_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].median().reset_index().rename(columns={'visitors':'genre_dow_median_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name'])
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].max().reset_index().rename(columns={'visitors':'genre_dow_max_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].count().reset_index().rename(columns={'visitors':'genre_dow_count_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].std().reset_index().rename(columns={'visitors':'genre_dow_std_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'genre_dow_skew_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name']) 
tmp = air_visit.groupby(['dow','air_genre_name'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'genre_dow_kurt_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_genre_name'])  
## province-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].mean().reset_index().rename(columns={'visitors':'province_dow_mean_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].median().reset_index().rename(columns={'visitors':'province_dow_median_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province'])
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].max().reset_index().rename(columns={'visitors':'province_dow_max_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].count().reset_index().rename(columns={'visitors':'province_dow_count_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].std().reset_index().rename(columns={'visitors':'province_dow_std_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'province_dow_skew_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province']) 
tmp = air_visit.groupby(['dow','air_area_name_province'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'province_dow_kurt_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_province'])
## province-city-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].mean().reset_index().rename(columns={'visitors':'city_dow_mean_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].median().reset_index().rename(columns={'visitors':'city_dow_median_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city'])
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].max().reset_index().rename(columns={'visitors':'city_dow_max_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].count().reset_index().rename(columns={'visitors':'city_dow_count_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].std().reset_index().rename(columns={'visitors':'city_dow_std_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'city_dow_skew_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
tmp = air_visit.groupby(['dow','air_area_name_city'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'city_dow_kurt_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_city']) 
## province-city-ward-dow visitors statistics
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].mean().reset_index().rename(columns={'visitors':'ward_dow_mean_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].median().reset_index().rename(columns={'visitors':'ward_dow_median_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward'])
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].max().reset_index().rename(columns={'visitors':'ward_dow_max_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].count().reset_index().rename(columns={'visitors':'ward_dow_count_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].std().reset_index().rename(columns={'visitors':'ward_dow_std_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].apply(pd.DataFrame.skew).reset_index().rename(columns={'visitors':'ward_dow_skew_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 
tmp = air_visit.groupby(['dow','air_area_name_ward'])['visitors'].apply(pd.DataFrame.kurt).reset_index().rename(columns={'visitors':'ward_dow_kurt_visitors'})
predict_data = pd.merge(predict_data, tmp, how='left', on=['dow','air_area_name_ward']) 

## reserv stastistic
predict_data['total_reserv_sum'] = predict_data['reserve_visitors_sum_x'] + predict_data['reserve_visitors_sum_y']
predict_data['total_reserv_mean'] = (predict_data['reserve_visitors_mean_x'] + predict_data['reserve_visitors_mean_y']) / 2
predict_data['total_reserv_dt_diff_mean'] = (predict_data['reserve_diff_mean_x'] + predict_data['reserve_diff_mean_y']) / 2

## geo
predict_data['var_max_lat'] = predict_data['latitude'].max() - predict_data['latitude']
predict_data['var_max_long'] = predict_data['longitude'].max() - predict_data['longitude']
predict_data['lat_plus_long'] = predict_data['latitude'] + predict_data['longitude']

predict_data.fillna(-1, inplace=True)

predict_data = df_lbl_enc(predict_data)
predict_data.to_csv('predict_data.csv')
predict_data = predict_data.drop(['visit_date','visitors'], axis=1)
predict_data_ohe = pd.get_dummies(predict_data, columns=['dow','air_genre_name','air_area_name_province','air_area_name_city','air_area_name_ward'], drop_first=True, sparse=True)

X_test = predict_data_ohe
#X_test = sc.transform(X_test)

print ('Preprocessing Finished')

print (train.shape)
print (X_test.shape)

from sklearn.cross_validation import train_test_split  
X_train, X_valid, y_train, y_valid = train_test_split(train, label, test_size=0.15, random_state=0)
import lightgbm as lgb


params = {
    'num_leaves': 80,
    'objective': 'regression',
    'min_data_in_leaf': 200,
    'max_bin': 256,
    'learning_rate': 0.005,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 2,
    'metric': 'rmse',
    'num_threads': 8   
}

MAX_ROUNDS = 30000

dtrain = lgb.Dataset(
        X_train, label=y_train
)
dval = lgb.Dataset(
        X_valid, label=y_valid, reference=dtrain)
bst = lgb.train(
        params, dtrain, num_boost_round=MAX_ROUNDS,
        valid_sets=[dtrain, dval], early_stopping_rounds=50, verbose_eval=100
)
val_pred = bst.predict(
        X_valid, num_iteration=bst.best_iteration or MAX_ROUNDS)
test_pred = bst.predict(
        X_test, num_iteration=bst.best_iteration or MAX_ROUNDS)
print("\n".join(("%s: %.2f" % x) for x in sorted(
        zip(X_train.columns, bst.feature_importance("gain")),
        key=lambda x: x[1], reverse=True)))

from sklearn.metrics import mean_squared_error
def RMSLE(y, pred):
    return mean_squared_error(y, pred)**0.5

score = RMSLE(y_valid, val_pred)
print('score:',score)

result = pd.DataFrame({"id": test_id, "visitors": test_pred})   
result['visitors'] = np.expm1(result['visitors'])
result.to_csv('lgb.csv', index=False)
print('Done')
