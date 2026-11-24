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

def create_features(df, col="Consumption"):
    df = df.copy()

    # Time features
    df["Hour"] = df.index.hour
    df["DayOfWeek"] = df.index.dayofweek
    df["Month"] = df.index.month
    df["Year"] = df.index.year
    df["IsWeekend"] = (df.index.dayofweek >= 5).astype(int)

    # Lags
    df["lag24"] = df[col].shift(24)
    df["lag168"] = df[col].shift(168)

    # Rolling mean over 24 hours
    df["roll_24"] = df[col].rolling(24).mean()

    return df


def check_missing(dataset):
    return dataset.isna().sum()


def drop_invalid_dates(dataset, date_col):
    return dataset.dropna(subset=[date_col])


def remove_duplicates(dataset, date_col):
    return dataset.drop_duplicates(subset=date_col, keep="first").reset_index(drop=True)


def fill_missing_hours(dataset, col="Consumption"):
    dataset = dataset.asfreq("h")
    dataset[col] = dataset[col].interpolate(method="time")
    return dataset


def preprocess_pipe(path):
    df = load_data_set(path)
    df = convert_to_date_time(df, "Datetime")
    df = drop_invalid_dates(df, "Datetime")
    df = fix_chrono_order(df, "Datetime")
    df = remove_duplicates(df, "Datetime")
    df = set_index(df, "Datetime")
    df = fill_missing_hours(df)
    df = flag_anomalies(df, "Consumption")
    df = treat_anomalies(df, "Consumption")
    df = df.drop(columns="is_anomaly")
    df = create_features(df)
    df = df.dropna()
    return df



def split_train_test(dataset, target="Consumption", train_size=0.8):
    X = dataset.drop(columns=target)
    y = dataset[target]

    split = int(len(dataset) * train_size)

    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    return X_train, X_test, y_train, y_test