import pandas as pd

def extract_dict_values(data: pd.DataFrame, original_column: str) -> pd.DataFrame:
    """
    Extract unique keys from a Pandas Series containing dictionaries and create columns for each key.

    Args:
        series (pd.Series): Pandas Series containing dictionaries.

    Returns:
        pd.DataFrame: DataFrame with extracted dictionary values as columns along with the original series.
    """
    # Select the series to apply the function
    series = data[original_column]
    
    # Create an empty DataFrame to store the extracted values
    extracted_data = pd.DataFrame()

    # Extract unique keys from the dictionaries in the Series
    unique_keys = set().union(*series)

    # Create a column for each unique key and populate it with the corresponding dictionary values
    for key in unique_keys:
        extracted_data[key] = series.apply(lambda x: x.get(key) if isinstance(x, dict) else "not avail")

    # Add the original series as a column in the extracted DataFrame
    
    df = pd.concat([data, extracted_data], axis=1)

    return df