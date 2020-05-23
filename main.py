import shutil
import os
import yfinance as yf
import pandas as pd
import sys
import time

CHARACTERS_TO_REMOVE_FROM_TICKER_NAME = '^()'
CHARACTERS_REPLACEMENT = {'&': 'n', '/': '-', ' ': '_'}
for i in CHARACTERS_TO_REMOVE_FROM_TICKER_NAME:
    CHARACTERS_REPLACEMENT[i] = ''

TICKERS_TO_IGNORE = set(['nan'])

START_DATE = '1922-01-01'
END_DATE = '2021-12-31'


def main(input_files):
    for input_file in input_files:
        output_directory = f"output/run_{int(time.time())}"
        os.mkdir(output_directory)

        input_file_name = input_file.split('/')[-1]
        shutil.copy(input_file, os.path.join(output_directory, input_file_name))

        print(f"Processing input file: {input_file}")
        tickers_input = pd.read_csv(input_file)
        tickers = tickers_input.values.tolist()
        tickers_left = []
        processed_tickers = []

        for ticker, name in tickers:
            try:
                ticker_df = yf.download(ticker,
                                        start=START_DATE,
                                        end=END_DATE,
                                        progress=False)

                processed_name = str(name).lower()
                for i, j in CHARACTERS_REPLACEMENT.items():
                    processed_name = processed_name.replace(i, j)

                if processed_name in TICKERS_TO_IGNORE:
                    print(f"Ignoring ticker: {name}")
                    tickers_left.append(name)
                    continue

                print(f"{name} -> {processed_name}")
                ticker_df.to_csv(os.path.join(output_directory, f'{processed_name}_historical_data.csv'))
                processed_tickers.append((ticker, name))
            except Exception as e:
                tickers_left.append((ticker, name))
                print(e)
            finally:
                time.sleep(2)

        tickers_left_path = save_tickers_to_csv(output_directory, tickers_left, 'tickers_left')
        processed_tickers_path = save_tickers_to_csv(output_directory, processed_tickers, 'processed_tickers')

        if tickers_left_path == None:
            print(f"No tickers left to process. Deleting input file: {input_file}")
            print(f"Processed tickers file is in : {processed_tickers_path}")
            os.remove(input_file)
        else:
            print("Copying back tickers that were left to input file")
            from shutil import copyfile
            copyfile(tickers_left_path, input_file)


def save_tickers_to_csv(output_directory, tickers_list, filename):
    csv_output_path = os.path.join(output_directory, f"{filename}.csv")
    if len(tickers_list) == 0:
        print(f"Skipping saving of ticker [{filename}] list due to that it's empty")
        return

    print(f"Saving dataframe: {csv_output_path}")
    with open(csv_output_path, 'w') as f:
        f.write(f'ticker, name{os.linesep}')
        for ticker, name in tickers_list:
            f.write(f'{ticker},{name}{os.linesep}')

    return csv_output_path

if __name__ == "__main__":
    input_files = ['input/' + f for f in os.listdir('input') if f.endswith('.csv')]
    main(input_files)