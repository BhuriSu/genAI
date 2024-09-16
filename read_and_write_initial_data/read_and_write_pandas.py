import os
import pandas as pd

# Directory containing the dataset
directory = 'datasets'

# Columns to keep from the CSV file
columns = ['date', 'province_eng', 'region_eng', 'value']

# Function to create separate dataframes for each year and split into 3 groups
def create_separate_dataframes(file_path: str) -> dict:
    # Load the dataset
    df = pd.read_csv(file_path, usecols=columns)

    # Convert the 'date' column to datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Define the years we want to separate by
    years = ['2019', '2020', '2021', '2022', '2023']

    # Dictionary to store dataframes for each year
    dataframes_by_year = {}

    # Separate the data by year and group into 3 parts
    for year in years:
        # Filter the dataframe by the year
        df_year = df[df['date'].dt.year == int(year)]
        
        # Sort by province_eng and region_eng for consistency
        df_sorted = df_year.sort_values(['province_eng', 'region_eng']).reset_index(drop=True)
        
        # Split the data into 3 groups
        group_size = len(df_sorted) // 3
        groups = [df_sorted.iloc[i:i + group_size] for i in range(0, len(df_sorted), group_size)]
        
        # Store the grouped dataframes for this year
        dataframes_by_year[year] = groups

    return dataframes_by_year

# Function to concatenate all year-based dataframes
def create_main_dataframe(separate_dataframes: dict) -> pd.DataFrame:
    """
    Concats all year-separated dataframes vertically and creates the final dataframe.
    """
    final_df_list = []

    for year, groups in separate_dataframes.items():
        for i, group in enumerate(groups, start=1):
            # Add 'year' and 'group' columns to identify the year and group number
            group['year'] = year
            group['group'] = i
            final_df_list.append(group)

    # Concatenate all dataframes into one
    df = pd.concat(final_df_list).reset_index(drop=True)

    # Sort by 'year' and 'group'
    df = df.sort_values(['year', 'group'])

    return df

# Function to write the final dataframe to a CSV file
def write_main_dataframe(df: pd.DataFrame):
    """
    Writes the final dataframe to a local CSV file.
    """
    output_file = os.path.join(directory, 'thailand_tourist_grouped.csv')
    df.to_csv(output_file, index=False)
    print(f"Data has been written to {output_file}")

if __name__ == '__main__':
    # File path to the dataset
    file_path = os.path.join(directory, 'thailand_tourist.csv')

    # Create separate dataframes by year and split into groups
    all_dataframes = create_separate_dataframes(file_path)

    # Create the main dataframe by concatenating year-based dataframes with group separation
    main_dataframe = create_main_dataframe(all_dataframes)

    # Write the final dataframe to a CSV file
    write_main_dataframe(main_dataframe)
