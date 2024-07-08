from eaws_score import EAWSScore
from multikim_score import MultikimScore
from participant import Operator
from task import Task
from posture_data_query import DataQuery

import datetime
import csv
import cv2
import csv
import time

class PhysicalLoad:
    def __init__(self, score_type, posture_csv, operator, task):
        self.score_type = score_type
        self.posture_csv = posture_csv
        self.posture_data = []
        self.operator = operator
        self.task = task
        self.score = 0

    def calculate_score(self):
        if self.score_type == "EAWS":
            self.posture_data, total_duration = self.load_posture_data()
            self.task.duration = total_duration
            print("Total duration (s):", total_duration)
            
            eaws = EAWSScore(self.operator, self.task, self.posture_data)
            extra_loads = [
                
            ]
            eaws.calculate_whole_body_extra_points(extra_loads)
            eaws.calculate_posture_score()
            self.score = eaws.calculate_eaws_score()
            return self.score
        elif self.score_type == "MULTIKIM":
            return MultikimScore().calculate()
        else:
            raise ValueError("Unknown score type")
        
    def calculate_intermediate_score(self, time, index):
        if self.score_type == "EAWS":
            eaws = EAWSScore(self.operator, self.task, self.posture_data)
            extra_loads = [
                
            ]
            eaws.calculate_whole_body_extra_points(extra_loads)
            return eaws.calculate_intermediate_eaws_score(time, index)
        elif self.score_type == "MULTIKIM":
            pass
        else:
            raise ValueError("Unknown score type")
    

    def load_posture_data(self):
        with open(self.posture_csv, 'r') as file:
            lines = file.readlines()
            
            # Find and parse the start and end times
            start_time_line = next(line for line in lines if "Start time" in line).strip().split(": ")[1].split()[1]
            end_time_line = next(line for line in lines if "End time" in line).strip().split(": ")[1].split()[1]
            
            start_time = self.parse_time(start_time_line)
            end_time = self.parse_time(end_time_line)

            if start_time is None or end_time is None:
                raise ValueError("Invalid start or end time format")

            total_duration = end_time - start_time

            # Read posture data
            posture_data = []
            previous_time = None
            for line in lines[8:]:
                parts = line.strip().split(",")
                time_str = parts[0]
                posture = parts[1]
                time_seconds = self.parse_time(time_str)
                if previous_time is not None:
                    duration = time_seconds - previous_time
                else:
                    duration = 0  # First line, so duration is 0
                    
                posture_data.append({"time": duration, "posture": posture})
                previous_time = time_seconds 

        return posture_data, total_duration

    
    def parse_time(self, time_str):
        time_format = "%H:%M:%S.%f"
        try:
            parsed_time = datetime.datetime.strptime(time_str, time_format)
            total_seconds = parsed_time.hour * 3600 + parsed_time.minute * 60 + parsed_time.second + parsed_time.microsecond / 1e6
            return total_seconds
        except ValueError:
            return None
        
    def process_video_with_posture(self, input_vid_filepath, output_vid_filepath):
        # Open the video capture object
        cap = cv2.VideoCapture(input_vid_filepath)

        # Check if video opened successfully
        if not cap.isOpened():
            print("Error opening video!")
            return

        # Define text properties
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_thickness = 1
        text_color = (0, 0, 0)  # Red color in BGR format

        # Get video properties for output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Adjust fourcc for different codecs (e.g., MP4: 'XVID')
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create video writer object with the obtained properties
        out = cv2.VideoWriter(output_vid_filepath, fourcc, fps, (frame_width, frame_height))

        cumulative_duration = 4.3 # TODO: Change Delay between beginning of video and beginning of recording (when pressing record in datamanager)
        current_posture_index = 0
        closest_posture = None

        while True:
            # Capture frame-by-frame
            frame_exists, frame = cap.read()

            if not frame_exists:
                break

            # Calculate elapsed time
            elapsed_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            # Find the posture entry for which the cumulative duration is closest to the elapsed time
            while current_posture_index < len(self.posture_data) and cumulative_duration < elapsed_time:
                closest_posture = self.posture_data[current_posture_index]
                cumulative_duration += closest_posture['time']
                current_posture_index += 1


            text = f"Timestamp: {elapsed_time}"[:-4]   
            cv2.putText(frame, text, (10, 25), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
            
            if closest_posture is not None:
                # Overlay closest posture and corresponding timestamp
                posture_text = f"Posture: {closest_posture['posture']}"
                cv2.putText(frame, posture_text, (10, 50), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                whole_body_extra_score, posture_score, eaws_score = self.calculate_intermediate_score(cumulative_duration, current_posture_index)
                eaws_text = f"Whole body extra points: {whole_body_extra_score}"
                cv2.putText(frame, eaws_text, (10, 75), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"Posture score: {posture_score}"
                cv2.putText(frame, eaws_text, (10, 100), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                eaws_text = f"EAWS: {eaws_score}"
                cv2.putText(frame, eaws_text, (10, 125), font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
                

            # Display the resulting frame
            cv2.imshow('Video with Posture', frame)

            # Write the frame to the output video
            out.write(frame)

            # Wait for key press
            key = cv2.waitKey(1)
            if key == ord('q'):
                break

        # Release the video capture object and close all windows
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"Video with posture saved to: {output_vid_filepath}")


if __name__ == "__main__":
    #score_type = input("Enter score type (EAWS/MULTIKIM): ").upper()
    #posture_csv = input("Enter path to posture data CSV file: ")
    operator1 = Operator("Ilias", "M", 173, 82)
    task = Task('Task 1')
    data = DataQuery()
    posture_file = data.get_file_path()
    physical_load = PhysicalLoad("EAWS", posture_file, operator1, task)
    print("Score:", physical_load.calculate_score())
    physical_load.process_video_with_posture("EAWS_Assembly_MVP-001.mp4", "output.mp4")