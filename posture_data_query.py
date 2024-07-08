import pandas as pd
import time
from datetime import datetime, timedelta
import requests
import json
import os

import pytz

utc=pytz.UTC

labels = ['Time', 'Key']


class DataQuery:
    def __init__(self):
        pass

    def process_files(self, keyboard_filename, mouse_filename):
        while True:
            df = pd.read_csv(keyboard_filename, skiprows=7)
            labels = []  # You should define 'labels' somewhere in your code
            
            df.columns = labels

            df['Time'] = pd.to_datetime(df['Time'], format="%H:%M:%S.%f")

            start_time = datetime.now() - timedelta(minutes=10)
            mask = (df['Time'].dt.time >= pd.Timestamp(start_time).time())
            filtered_df = df.loc[mask]

            wrk = filtered_df.groupby(pd.to_datetime(df.Time).dt.minute).apply(lambda grp: grp.index.size)
            wrk.index = wrk.index.map(lambda h: f'{h:02}')

            print("********************************************************************")
            print(f"Start time = {start_time}")
            print(wrk.to_frame()) 

            time.sleep(10)

    def __execute_query(self, query):
        url = "http://127.0.0.1:8000/graphql"

        response = requests.post(url=url, json={"query": query})

        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Something went wrong when executing the query:\n {query}")

    def __get_datetime_from_json(self, json_string):
        datetime_temp = datetime.fromisoformat(json_string)

        if datetime_temp.tzinfo == None:
            utc = pytz.UTC

            datetime_temp = utc.localize(datetime_temp)

        return datetime_temp

    def get_id_person(self, person_json):
        return person_json['data']['persons'][0]['id']

    def get_last_active_session_id(self, person_json):
        sessions = person_json['data']['persons'][0]['hasACollectionOfRecords']

        last_active_session_id = None
        last_active_session_name = None
        last_active_session_begin_time = datetime(year=1900, month=1, day=1,hour=0,minute=0,second=0, tzinfo=pytz.UTC)

        for session in sessions:
            current_session = session['session']

            current_timeinterval = current_session['timeInterval']
            current_begin_time = self.__get_datetime_from_json(current_timeinterval['beginTime'])

            if current_begin_time > last_active_session_begin_time:
                last_active_session_id = current_session['id'] 
                last_active_session_name = current_session['name'] 
                last_active_session_begin_time = current_begin_time

        return (last_active_session_id, last_active_session_name)

    def get_filename_for_monitoring_system(self, monitoring_records_json, monitoring_system_name):
        for monitoring_system in monitoring_records_json['data']['monitoringRecords']:
            if monitoring_system['isRecordedBySystem']['name'] == monitoring_system_name:
                full_filename = os.path.join(monitoring_system['absolutepath'], monitoring_system['fileName']) + '.csv'
                return full_filename

    def query_get_person(self, person_name):
        query = """{
            persons(name: "%%person_name%%") {
                id
                hasACollectionOfRecords {
                    session {
                        id
                        name
                        timeInterval {
                            beginTime
                            endTime
                        }
                    }
                }
            }
        }
        """
        query = query.replace("%%person_name%%", person_name)
        result = self.__execute_query(query)
        return result

    def query_get_monitoring_records_for_person_and_session(self, person_id, session_id):
        query = """{
            monitoringRecords(recordedPersonId: "%%person_id%%", sessionId: "%%session_id%%") {
                fileName
                path
                absolutepath
                isRecordedBySystem {
                    name
                    id
                    manufacturer
                }
            }
        }
        """
        query = query.replace("%%person_id%%", person_id)
        query = query.replace("%%session_id%%", session_id)
        result = self.__execute_query(query)
        return result
    
    def get_file_path(self):
        person_data = self.query_get_person("John Doe")
        person_json = json.loads(person_data)
        person_id = self.get_id_person(person_json)
        print(f"Person found. Id = {person_id}.")

        (last_session_id, last_session_name) =  self.get_last_active_session_id(person_json)
        print(f"Last session found. Id = {last_session_id}, name = {last_session_name}.")

        monitoring_records_data = self.query_get_monitoring_records_for_person_and_session(person_id=person_id, session_id=last_session_id)
        monitoring_records_json = json.loads(monitoring_records_data)

        posture_file = self.get_filename_for_monitoring_system(monitoring_records_json, 'Keyboard') # TODO: why Keyboard?? should be Posture
        print(posture_file)

        return posture_file

        # Call process_files with appropriate filenames
        # self.process_files(keyboard_file, mouse_file)

if __name__ == "__main__":
    fp = DataQuery()
    fp.main()

