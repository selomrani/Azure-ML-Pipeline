import pandas as pd

def load_data_set(path):
    try:
        df = pd.read_csv(path)
        df = df.rename(columns={
            "PJME_MW" : "Consumption"
        })
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")


def convert_to_date_time(dataset, date_col):
    dataset = dataset.copy()
    dataset[date_col] = pd.to_datetime(dataset[date_col], errors="coerce")
    return dataset


def is_ordered(dataset, date_col):
    return dataset[date_col].is_monotonic_increasing


def fix_chrono_order(dataset, date_col):
    if is_ordered(dataset, date_col):
        return dataset
    return dataset.sort_values(date_col).reset_index(drop=True)

def set_index(dataset,col):
    return dataset.set_index(col
                             )
def flag_anomalies(dataset,col,threshold=3):
    dataset = dataset.copy()
    grouped = dataset.groupby(dataset.index.hour)[col]
    z = (dataset[col] - grouped.transform("mean")) / grouped.transform("std")
    dataset["is_anomaly"] = z.abs() > threshold
    return dataset


def treat_anomalies(df, col):
    df = df.copy()
    df.loc[df["is_anomaly"], col] = None
    df[col] = df[col].interpolate(method="time")
    return df