import datetime
def format_numbers_to_indian_system(df, columns):
    def format_to_indian(x):
        if isinstance(x, int):
            
            s = f"{x:,}"
            return s.replace(",", ",").replace(",,", ",")

        elif isinstance(x, float):
            # Convert float to Indian numbering format
            formatted_float = "{:,.2f}".format(x)
            integer_part, decimal_part = formatted_float.split(".")
            integer_part = "{:,}".format(int(integer_part.replace(",", ""))).replace(",", ",")
            return f"{integer_part}.{decimal_part}"
        elif isinstance(x, str):
            # Handle string representations of numbers with commas
            try:
                return format_to_indian(int(x.replace(",", "")))
            except ValueError:
                return x
        return x

    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(format_to_indian)
        else:
            print(f"Column not found: {col}")
    
    return df



def revert_indian_number_format(df, cols):
    for col in cols:
        if df[col].dtype != 'object':
            df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(',', '').astype(int)
    return df
def convert_date(date_str):
    # Define a dictionary to map month abbreviations to their numerical values
    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    date_str=str(date_str)
    #print(date_str)
    # Check if the date string is in "08 Apr 2024" format
    if date_str[2] == ' ':
        # Split the date string into its components
        parts = date_str.split()
        
        # Extract day, month (convert from abbreviation to number), and year
        day = int(parts[0])
        month = month_map[parts[1]]
        year = int(parts[2])
    
    # Check if the date string is in "2020-04-03" format
    elif date_str[4] == '-':
        # Split the date string into its components
        parts = date_str.split('-')
        
        # Extract year, month, and day
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    
    elif date_str[1]=='/' or date_str[2]=='/':
        parts = date_str.split('/')
        month = int(parts[0])
        day =int(parts[1])
        year = int(parts[2])

    elif date_str[2] == '-' or date_str[1]=='-':
        # Split the date string into its components
        parts = date_str.split('-')
        
        # Extract day, month (convert from abbreviation to number), and year
        day = int(parts[0])
        month = month_map[parts[1]]
        # Determine the century for the year (assuming 2000s for years 00-99)
        year = 2000 + int(parts[2])
    
        
    return datetime.date(year,month,day)