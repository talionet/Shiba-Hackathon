"""
Compute some featuers
"""


def add_death_columns(frame):

    frame.death_date = pd.DatetimeIndex(frame.death_date)

    # Was this person hospitalized
    frame["hospitalization"] = ~frame.hospitalization_in.isna()

    # The real discharge date
    frame["date_home"] = frame["discharge_date_max hospitalization_out".split()].max(axis=1)

    # Total time is ER + hospitalization
    frame["total_time_hospital"] = frame.date_home - frame.admission_date_min

    # Mortality of the ER
    frame["mortality_ER"] = frame.discharge_date_max >= frame.death_date

    # Mortality during hospitalization
    frame["mortality_hospital"] = (frame.date_home >= frame.death_date) & ~frame.mortality_ER

    #
    frame["mortality2d"] = frame.death_date <= frame.admission_date_min + pd.Timedelta('2d')
    frame["mortality30d"] = (frame.death_date <= frame.admission_date_min + pd.Timedelta('30d'))
    frame["mortality60d"] = (frame.death_date <= frame.admission_date_min + pd.Timedelta('60d'))

    return frame


if __name__ == "__main__":
    from shibaer.util import *
    data = load_pickle_files("DATAB", "ER")
    data = add_death_columns(data)
    print(data.head())