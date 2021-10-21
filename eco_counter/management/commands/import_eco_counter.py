"""
Usage:
For initial import or changes in the stations:
python manage.py import-eco-counter --initial-import
otherwise for incremental import:
python manage.py import-eco-counter

Brief explanation of the import alogithm:
1. Import the stations.
2. Read the csv file as a pandas DataFrame.
3. Reads the year and month from the ImportState.
4. Set the import to start from that year and month, the import always begins
 from the first day and time 00:00:00 of the month in state, i.e. the longest
 timespan that is imported is one month and the shortest is 15min, depending 
 on the import state.
5. Delete tables(HourData, Day, DayData and Week) that will be repopulated. *
6. Set the current state to state variables: current_years, currents_months, 
 current_weeks, these dictionaries holds references to the model instances. 
 Every station has its own state variables and the key is the name of the station.
7. Iterate through all the rows
    7.1 Read the time
    7.2 Read the current year, month, week and day number.  
    7.3 If index % 4 == 0 save current hour to current_hours state, the input
     data has a sample rateof 15min, and the precision stored while importing
    is One hour.
    7.4 If day number has changed save hourly and day data.
    7.4.1 If Year, month or week number has changed. Save this data, create new tables
          and update references to state variables.
    7.4.2 Create new day tables using the current state variables(year, month week),
          update day state variable. Create HourData tables and update current_hours 
          state variable. HourData tables are the only tables that contains data that are
          in the state, thus they are updated every fourth iteration. (15min samples to 1h)
    8.6 Iterate through all the columns, except the first that holds the time.
    8.6.1 Store the sampled data to current_hour state for every station, 
           every mode of transportaion and direction.   
9. Finally store all data in states that has not been saved.
10. Save import state.

* If executed with the --delete-tables flag, the import will start from the beginning
of the .csv file, 1.1.2020. 

"""

import logging
import requests
import pytz
import math
import io
import re
import pandas as pd 
import dateutil.parser
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from eco_counter.models import (
    Station, 
    HourData,
    Day,
    DayData,
    Week,     
    WeekData,
    Month, 
    MonthData,
    Year, 
    YearData,
    ImportState
    )

STATIONS_URL = "https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson"
OBSERVATIONS_URL = "https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv"
logger = logging.getLogger("eco_counter")


class Command(BaseCommand):
    help = "Imports Turku Traffic Volumes"
    
    # List used to lookup name and type
    # Output of pandas dataframe, i.e. csv_data.keys()
    columns = []   
    
    def delete_tables(self):
        HourData.objects.all().delete()
        DayData.objects.all().delete()
        Day.objects.all().delete()
        WeekData.objects.all().delete()
        Week.objects.all().delete()
        Month.objects.all().delete()
        MonthData.objects.all().delete()
        Year.objects.all().delete()
        YearData.objects.all().delete()
        Station.objects.all().delete()
        ImportState.objects.all().delete()

    def get_dataframe(self):
        response = requests.get(OBSERVATIONS_URL) 
        assert response.status_code == 200, "Fetching observations csv {} status code: {}".\
            format(OBSERVATIONS_URL, response.status_code)
        string_data = response.content
        csv_data = pd.read_csv(io.StringIO(string_data.decode('utf-8')))
        return csv_data

    def calc_and_save_cumulative_data(self, src_obj, dst_obj):
        dst_obj.value_ak = 0
        dst_obj.value_ap = 0
        dst_obj.value_at = 0
        dst_obj.value_pk = 0
        dst_obj.value_pp = 0
        dst_obj.value_pt = 0
        dst_obj.value_jk = 0
        dst_obj.value_jp = 0
        dst_obj.value_jt = 0 
        for src in src_obj:
            dst_obj.value_ak += src.value_ak
            dst_obj.value_ap += src.value_ap
            dst_obj.value_at += src.value_at
            dst_obj.value_pk += src.value_pk
            dst_obj.value_pp += src.value_pp
            dst_obj.value_pt += src.value_pt
            dst_obj.value_jk += src.value_jk
            dst_obj.value_jp += src.value_jp
            dst_obj.value_jt += src.value_jt 
        dst_obj.save()

    def create_and_save_year_data(self, stations, current_years):
        for station in stations:
            year = current_years[station]
            year_data = YearData.objects.update_or_create(year=year, station=stations[station])[0]
            self.calc_and_save_cumulative_data(year.month_data.all(), year_data)

    def create_and_save_month_data(self, stations, current_months, current_years):                 
        for station in stations:
            month = current_months[station]
            month_data = MonthData.objects.update_or_create(month=month,\
                 station=stations[station], year=current_years[station])[0]
            day_data = DayData.objects.filter(day__month=month)
            self.calc_and_save_cumulative_data(day_data, month_data)

    def create_and_save_week_data(self, stations, current_weeks):
        for station in stations:
            week = current_weeks[station]
            week_data = WeekData.objects.update_or_create(week=week, station=stations[station])[0]
            day_data = DayData.objects.filter(day__week=week)
            self.calc_and_save_cumulative_data(day_data, week_data)

    def create_and_save_day_data(self, stations, current_hours, current_days):
        for station in stations:
            day_data = DayData.objects.create(station=stations[station], day=current_days[station])
            current_hour = current_hours[station]
            day_data.value_ak = sum(current_hour.values_ak)
            day_data.value_ap = sum(current_hour.values_ap)
            day_data.value_at = sum(current_hour.values_at)
            day_data.value_pk = sum(current_hour.values_pk)
            day_data.value_pp = sum(current_hour.values_pp)
            day_data.value_pt = sum(current_hour.values_pt)
            day_data.value_jk = sum(current_hour.values_jk)
            day_data.value_jp = sum(current_hour.values_jp)
            day_data.value_jt = sum(current_hour.values_jt)
            day_data.save()
   
    def save_hour_data(self, current_hour, current_hours):       
        for station in current_hour:                   
            hour_data = current_hours[station]                        
            # Store "Auto"
            if "AK" and "AP" in current_hour[station]:
                ak = current_hour[station]["AK"]
                ap = current_hour[station]["AP"]
                tot = ak+ap
                hour_data.values_ak.append(ak)
                hour_data.values_ap.append(ap)
                hour_data.values_at.append(tot)
            # Store "Pyöräilijä"
            if "PK" and "PP" in current_hour[station]:
                pk = current_hour[station]["PK"]
                pp = current_hour[station]["PP"]
                tot = pk+pp              
                hour_data.values_pk.append(pk)
                hour_data.values_pp.append(pp)
                hour_data.values_pt.append(tot)
            # store "Jalankulkija" pedestrian 
            if "JK" and "JP" in current_hour[station]:
                jk = current_hour[station]["JK"]
                jp = current_hour[station]["JP"]
                tot = jk+jp     
                hour_data.values_jk.append(jk)
                hour_data.values_jp.append(jp)
                hour_data.values_jt.append(tot)  

            hour_data.save()       

    def save_stations(self):
        response = requests.get(STATIONS_URL)
        assert response.status_code == 200, "Fetching stations from {} , status code {}"\
            .format(STATIONS_URL, response.status_code)
        response_json = response.json()
        features = response_json["features"]
        saved = 0
        for feature in features:
            station = Station()
            name = feature["properties"]["Nimi"]            
            if not Station.objects.filter(name=name).exists():                
                station.name = name
                lon = feature["geometry"]["coordinates"][0]
                lat = feature["geometry"]["coordinates"][1]
                point = Point(lon, lat, srid=4326)
                point.transform(settings.DEFAULT_SRID)
                station.geom = point
                station.save()
                saved += 1
        logger.info("Retrived {numloc} stations, saved {saved} stations.".\
            format(numloc=len(features), saved=saved))

    def gen_test_csv(self, keys, start_time, end_time):
        """
        Generates testdata for a given timespan, 
        for every 15min the value 1 is set.
        """       
        df = pd.DataFrame(columns=keys)
        df.keys = keys
        cur_time = start_time
        c = 0
        while cur_time <= end_time:
            # Add value to all keys(sensor stations)
            vals = [1 for x in range(len(keys)-1)]
            vals.insert(0, str(cur_time))
            df.loc[c] = vals
            cur_time = cur_time + timedelta(minutes=15)
            c += 1            
        return df       

    def get_station_name_and_type(self,column):
        #Station type is always: A|P|J + K|P  
        station_type = re.findall("[APJ][PK]", column)[0]
        station_name = column.replace(station_type,"").strip()               
        return station_name, station_type                   

    def save_observations(self, csv_data, start_time):        
        stations = {}
        #Dict used to lookup station relations
        for station in Station.objects.all():
            stations[station.name] = station     
        # state variable for the current hour that is calucalted for every iteration(15min)  
        current_hour = {}
        current_hours = {}
        current_days = {}
        current_weeks = {}
        current_months = {}
        current_years = {}      
      
        import_state = ImportState.load()
        rows_imported = import_state.rows_imported
        current_year_number = import_state.current_year_number 
        current_month_number = import_state.current_month_number
        current_weekday_number = None

        current_week_number = int(start_time.strftime("%-V"))
        prev_weekday_number = start_time.weekday()
        prev_year_number = current_year_number
        prev_month_number = current_month_number
        prev_week_number = current_week_number
        current_time = None
        prev_time = None       
        # All Hourly, daily and weekly data that are past the current_week_number
        # are delete thus they are repopulated.  HourData and DayData are deleted
        # thus their on_delete is set to models.CASCADE.     
        Day.objects.filter(month__month_number=current_month_number, \
            month__year__year_number=current_year_number).delete() 
        for week_number in range(current_week_number+1, current_week_number+5):   
            Week.objects.filter(week_number=week_number, years__year_number=current_year_number).delete()
       
        # Set the references to the current state. 
        for station in stations:
            current_years[station] = Year.objects.get_or_create(station=stations[station], \
                year_number=current_year_number)[0]           
            current_months[station] = Month.objects.get_or_create(station=stations[station], \
                year=current_years[station], month_number=current_month_number)[0]            
            current_weeks[station] = Week.objects.get_or_create(station=stations[station], week_number=current_week_number, years__year_number=current_year_number)[0]
            current_weeks[station].years.add(current_years[station])
          
        for index, row in csv_data.iterrows():           
            try:
                aika = row.get("aika", None)
                if type(aika)==str:
                    current_time = dateutil.parser.parse(aika) 
                # When the time is changed due to daylight savings
                # Input data does not contain any timestamp for that hour, only data
                # so the current_time is calculated
                else:
                    current_time = prev_time+timedelta(minutes=15)  
            except dateutil.parser._parser.ParserError:
                # If malformed time calcultate new current_time.
                current_time = prev_time+timedelta(minutes=15)

            if prev_time:
                # Compare the utcoffset, if not equal the daylight saving has changed.
                if current_time.tzinfo.utcoffset(current_time) != prev_time.tzinfo.utcoffset(prev_time):
                    # Take the daylight saving time (dst) hour from the utcoffset
                    current_time_dst_hour = dateutil.parser.parse(str(current_time.tzinfo.utcoffset(current_time)))
                    prev_time_dst_hour = dateutil.parser.parse(str(prev_time.tzinfo.utcoffset(prev_time)))                        
                    # If the prev_time_dst_hour is less than current_time_dst_hour, 
                    # then this is the hour clocks are changed backwards, i.e. summertime
                    if prev_time_dst_hour < current_time_dst_hour:
                        # Add an hour where the values are 0, for the nonexistent hour 3:00-4:00
                        # To keep the hour data consistent with 24 hours. 
                        temp_hour = {}
                        for station in stations:
                            temp_hour[station] = {}                                
                        for column in self.columns[1:]: 
                            station_name, station_type = self.get_station_name_and_type(column)        
                            temp_hour[station_name][station_type] = 0
                        self.save_hour_data(temp_hour, current_hours)             
            
            current_year_number = current_time.year
            current_week_number = int(current_time.strftime("%-V"))
            current_weekday_number = current_time.weekday()
            current_month_number = datetime.date(current_time).month
       
            #Adds data for an hour every fourth iteration, sample rate is 15min.
            if index % 4 == 0:
                self.save_hour_data(current_hour, current_hours)                
                # Clear current_hour after storage, to get data for every hour.
                current_hour = {}
            
            if prev_weekday_number != current_weekday_number or not current_hours: 
                # Store hour data if data exists.
                if current_hours:
                    self.create_and_save_day_data(stations, current_hours, current_days)
                current_hours = {}
                
                # Year, month, week tables are created before the day tables 
                # to ensure correct relations.            
                if prev_year_number != current_year_number or not current_years:
                    # if we have a prev_year_number and it is not the current_year_number store yearly data.
                    if prev_year_number:                   
                        self.create_and_save_year_data(stations, current_years)                       
                    for station in stations:
                        year = Year.objects.create(year_number=current_year_number, station=stations[station])
                        current_years[station] = year
                        current_weeks[station].years.add(year)
                    prev_year_number = current_year_number              
       
                if prev_month_number != current_month_number or not current_months:
                    if  prev_month_number:  
                        self.create_and_save_month_data(stations, current_months, current_years)                 
                    for station in stations:
                        month = Month.objects.create(station=stations[station],\
                            year=current_years[station], month_number=current_month_number)
                        current_months[station] = month                
                    prev_month_number = current_month_number 

                if prev_week_number != current_week_number or not current_weeks:                                  
                    if prev_week_number:
                        self.create_and_save_week_data(stations, current_weeks)                 
                    for station in stations:
                        week = Week.objects.create(station=stations[station],\
                            week_number=current_week_number)
                        week.years.add(current_years[station])
                        current_weeks[station] = week               
                    prev_week_number = current_week_number                  
                    
                for station in stations:  
                    day = Day.objects.create(station=stations[station], date=current_time,\
                        weekday_number=current_weekday_number, week=current_weeks[station],\
                             month=current_months[station], year=current_years[station])                  
                    current_days[station] = day                    
                    hour_data = HourData.objects.create(station=stations[station], day=current_days[station])
                    current_hours[station] = hour_data
                prev_weekday_number = current_weekday_number
            
            """         
            Build the current_hour dict by iterating all cols in row.
            current_hour dict store the rows in a structured form. 
            current_hour keys are the station names and every value contains a dict with the type as its key
            The type is: A|P|J(Auto, Pyöräilijä, Jalankulkija) + direction P|K , e.g. "JK"
            current_hour[station][station_type] = value, e.g. current_hour["TeatteriSilta"]["PK"] = 6
            Note the first col is the "aika" and is discarded, the rest are observations for every station
            """
            for column in self.columns[1:]: 
                station_name, station_type = self.get_station_name_and_type(column)                          
                value = row[column]
                if math.isnan(value):
                    value = int(0)
                else:
                    value = int(row[column])
                    
                if station_name not in current_hour:
                    current_hour[station_name]={}
                # if type exist in current_hour, we add the new value to get the hourly sample
                if station_type in current_hour[station_name]:                                     
                    current_hour[station_name][station_type] = int(current_hour[station_name][station_type]) + value
                else:
                    current_hour[station_name][station_type] = value 
            prev_time = current_time
        #Finally save hours, days, months etc. that are not fully populated.
        self.save_hour_data(current_hour, current_hours)  
        self.create_and_save_day_data(stations, current_hours, current_days)
        self.create_and_save_week_data(stations, current_weeks)                 
        self.create_and_save_month_data(stations, current_months, current_years)                 
        self.create_and_save_year_data(stations, current_years)                     
        
        import_state.current_year_number = current_year_number
        import_state.current_month_number = current_month_number
        import_state.rows_imported = rows_imported + len(csv_data)     
        import_state.save()
        logger.info("Imported observations until: "+str(current_time))

    def add_arguments(self, parser):
        parser.add_argument(           
            "--initial-import",
            action="store_true",
            default=False,
            help="Deletes all tables before importing. Imports stations and\
                 starts importing from row 0.",
        )
        parser.add_argument(            
            "--test-mode", 
            type=int,
            nargs="+",
            default=False,
            help="Run script in test mode. Uses Generated pandas dataframe.",
        )

    def handle(self, *args, **options):
        if options["initial_import"]:
            logger.info("Deleting tables")
            self.delete_tables()
            logger.info("Retrieving stations...")
            self.save_stations()      
        logger.info("Retrieving observations...")
        csv_data = self.get_dataframe()
        self.columns = csv_data.keys()  

        start_time = None
        if options["test_mode"]:         
            logger.info("Retrieving observations in test mode.")
            self.save_stations()      
            start_time = options["test_mode"][0]            
            csv_data = self.gen_test_csv(csv_data.keys(), start_time, options["test_mode"][1]) 
        else:
            import_state = ImportState.load() 
            start_time = "{year}-{month}-1 00:00:00".format(year=import_state.current_year_number, \
                month=import_state.current_month_number)         
            timezone = pytz.timezone("Europe/Helsinki")
            start_time = dateutil.parser.parse(start_time)
            start_time = make_aware(start_time, timezone)
            # The timeformat for the input data is : 2020-01-01 00:00:00+02:00
            # Convert starting time to input datas timeformat
            start_time_string = start_time.strftime("%Y-%m-%d %H:%M:%S%z")
            # Add a colon separator to the offset segment, +0200 -> +02:00 
            start_time_string = "{0}:{1}".format(
                start_time_string[:-2],
                start_time_string[-2:]
            )
            start_index = csv_data.index[csv_data["aika"]==start_time_string].values[0]  
            logger.info("Starting import at index: {}".format(start_index))
            csv_data = csv_data[start_index:]
        self.save_observations(csv_data, start_time)
      

             
       
