# Python ≥3.11 is required
import sys
import time

assert sys.version_info >= (3, 11)
import pandas as pd
from pylsl import StreamInlet, StreamOutlet, StreamInfo, resolve_stream

import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

position_Pelvis_z = "Pelvis z.1"
Pelvis_T8_x = "Pelvis_T8 Axial Bending"
Pelvis_T8_y = "Pelvis_T8 Lateral Bending"
Pelvis_T8_z = "Pelvis_T8 Flexion/Extension"
jLeftShoulder_y = "Left Shoulder Abduction/Adduction"
jLeftShoulder_z = "Left Shoulder Flexion/Extension"
jRightShoulder_y = "Right Shoulder Abduction/Adduction"
jRightShoulder_z = "Right Shoulder Flexion/Extension"

EAWS_Standing = "St"
EAWS_Crouching = "Cr"
EAWS_Lying = "Ly"
EAWS_Upright = "U"
EAWS_BentForward = "BF"
EAWS_BentStrongForward = "BS"
EAWS_ElbowOverShoulder = "OS"
EAWS_HandsAboveHead = "OH"
EAWS_TrunkRotation = "TR"
EAWS_LateralBending = "LB"


def auto_label(df):
    # Constants
    MULT_PELVIS_Z_LY = 0.2
    MULT_PELVIS_Z_CR = 0.85
    TH_PELVIS_BF = 20
    TH_PELVIS_BS = 60
    TH_SHOULDER_OS = 75
    TH_SHOULDER_OH = 90
    OFFSET_CR = 0
    OFFSET_SHOULDER_BF_Y = 0  # Dynamic using -> df[Pelvis_T8_y]
    OFFSET_SHOULDER_BF_Z = 0  # Dynamic using -> df[Pelvis_T8_z]
    MAX_TR = 60.0
    MAX_LB = 60.0

    st_u_L5_avg = 1.0 #df[position_Pelvis_z][:8].mean(skipna=True) --> TO CHECK

    # Main poses: St, Ly, Cr
    df["AutoDePos"] = "St"  # Default value
    df.loc[df[position_Pelvis_z] < MULT_PELVIS_Z_LY * st_u_L5_avg, "AutoDePos"] = "Ly"

    condition_cr = (df[position_Pelvis_z] >= MULT_PELVIS_Z_LY * st_u_L5_avg) & (
        df[position_Pelvis_z] < MULT_PELVIS_Z_CR * st_u_L5_avg
    )

    #print(st_u_L5_avg)
    # print(df[position_Pelvis_z], " ", MULT_PELVIS_Z_LY * st_u_L5_avg, " : ", MULT_PELVIS_Z_CR * st_u_L5_avg)
    # condition_cr = ((df[jLeftHip_z] > 30) |  (df[jLeftKnee_z] > 30) ) & ((df[jRightHip_z] > 30) |  (df[jRightKnee_z] > 30) )

    df.loc[
        condition_cr,
        "AutoDePos",
    ] = "Cr"

    # Symmetric sub-poses: : BF, BS, OH, OS, U
    conditions_sym = [
        ((df[Pelvis_T8_z] >= TH_PELVIS_BS) & (df["AutoDePos"] == "St")),
        ((df[Pelvis_T8_z] >= TH_PELVIS_BS + OFFSET_CR) & (df["AutoDePos"] == "Cr")),
        ((df[Pelvis_T8_z] >= TH_PELVIS_BF) & (df["AutoDePos"] == "St")),
        ((df[Pelvis_T8_z] >= TH_PELVIS_BF + OFFSET_CR) & (df["AutoDePos"] == "Cr")),
        (
            (df[jLeftShoulder_y] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Y)
            | (df[jLeftShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_y] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Y)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OH + OFFSET_SHOULDER_BF_Z)
        ),
        (
            (df[jLeftShoulder_y] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Y)
            | (df[jLeftShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
            | (df[jRightShoulder_y] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Y)
            | (df[jRightShoulder_z] >= TH_SHOULDER_OS + OFFSET_SHOULDER_BF_Z)
        ),
        ((df[Pelvis_T8_z] < TH_PELVIS_BF) & (df["AutoDePos"] != "Cr")),
        ((df[Pelvis_T8_z] < TH_PELVIS_BF + OFFSET_CR) & (df["AutoDePos"] == "Cr")),
    ]
    choices_sym = ["_BS", "_BS", "_BF", "_BF", "_OH", "_OS", "_U", "_U"]

    for condition, choice in zip(conditions_sym, choices_sym):
        mask = ~(df.loc[condition, "AutoDePos"].str.contains("|".join(choices_sym)))
        df.loc[condition & mask, "AutoDePos"] += choice  # Add choice to rows not in choices_sym

    # Asymmetric sub-poses: Trunk rotations
    conditions_tr = [
        (abs(df[Pelvis_T8_x]) > 5 * (MAX_TR / 6.0)),
        (abs(df[Pelvis_T8_x]) > 4 * (MAX_TR / 6.0)),
        (abs(df[Pelvis_T8_x]) > 3 * (MAX_TR / 6.0)),
        (abs(df[Pelvis_T8_x]) > 2 * (MAX_TR / 6.0)),
        (abs(df[Pelvis_T8_x]) > 1 * (MAX_TR / 6.0)),
        (abs(df[Pelvis_T8_x]) > 0 * (MAX_TR / 6.0)),
    ]
    choices_tr = ["_TR5", "_TR4", "_TR3", "_TR2", "_TR1", "_TR0"]

    for condition, choice in zip(conditions_tr, choices_tr):
        mask = ~(
            df.loc[condition, "AutoDePos"].str.contains("|".join(choices_tr))
        )  # Create a boolean mask to identify elements not in choices_sym
        df.loc[condition & mask, "AutoDePos"] += choice  # Add choice to rows not in choices_sym

    # Asymmetric sub-poses: Trunk lateral bendings
    conditions_lb = [
        (abs(df[Pelvis_T8_y]) > 5 * (MAX_LB / 6.0)),
        (abs(df[Pelvis_T8_y]) > 4 * (MAX_LB / 6.0)),
        (abs(df[Pelvis_T8_y]) > 3 * (MAX_LB / 6.0)),
        (abs(df[Pelvis_T8_y]) > 2 * (MAX_LB / 6.0)),
        (abs(df[Pelvis_T8_y]) > 1 * (MAX_LB / 6.0)),
        (abs(df[Pelvis_T8_y]) > 0 * (MAX_LB / 6.0)),
    ]
    choices_lb = ["_LB5", "_LB4", "_LB3", "_LB2", "_LB1", "_LB0"]

    for condition, choice in zip(conditions_lb, choices_lb):
        mask = ~(
            df.loc[condition, "AutoDePos"].str.contains("|".join(choices_lb))
        )  # Create a boolean mask to identify elements not in choices_sym
        df.loc[condition & mask, "AutoDePos"] += choice  # Add choice to rows not in choices_sym

    return df


def main():
    print("looking for an xsens stream...")
    streams = resolve_stream("type", "hum_ergo_feat")  # 👉change here

    # create a new inlet to read from the stream
    inlet = StreamInlet(streams[0])

    # get the full stream info (including custom meta-data) and dissect it
    info = inlet.info()
    print("The stream's XML meta-data is: ")
    print(info.as_xml())
    print("The manufacturer is: %s" % info.desc().child_value("manufacturer"))
    print("Cap circumference is: %s" % info.desc().child("cap").child_value("size"))
    print("The channel labels are as follows:")
    ch = info.desc().child("channels").child("channel")
    for k in range(info.channel_count()):
        print("  " + ch.child_value("label"))
        ch = ch.next_sibling()

    type = "AutoDePos"
    name = inlet.info().name() + " - " + type

    # make an outlet
    outlet = StreamOutlet(StreamInfo(name, type, channel_count=1, channel_format="string", source_id=name))

    df = pd.DataFrame(
        columns=[
            position_Pelvis_z,
            Pelvis_T8_x,
            Pelvis_T8_y,
            Pelvis_T8_z,
            jLeftShoulder_y,
            jLeftShoulder_z,
            jRightShoulder_y,
            jRightShoulder_z,
        ]
    )

    window_size_ms = 250.0  # ms
    max_samples = int(window_size_ms / 2 / (1000.0 / info.nominal_srate()))
    counter = 0
    n = 20
    while True:
        start_time = time.time()
        samples, timestamps = inlet.pull_chunk(max_samples=max_samples, timeout=window_size_ms / 2 / 1000)
        #print(len(samples))
        df_new_chunk = pd.DataFrame(samples, columns=df.columns, index=timestamps)
        df = pd.concat([df, df_new_chunk])

        counter += 1

        if(counter == n):
            filtered_df = df[df.index >= df.index[-1] - window_size_ms / 1000.0]
            samples_mean = filtered_df.mean()

            df_mean = pd.DataFrame(samples_mean.values.reshape(1, -1), columns=df.columns, index=[timestampsow])
            
            df_labelled = auto_label(df_mean)

            try:
                print(df_labelled["AutoDePos"].values[0], " ", df[Pelvis_T8_x].iloc[-1])

                #print (df[position_Pelvis_z].iloc[-1])
                outlet.push_sample(df_labelled["AutoDePos"].values, timestamp=timestamps[-1])

                counter = 0
            except IndexError:
                print("Index out of range error occurred.")



if __name__ == "__main__":
    main()
