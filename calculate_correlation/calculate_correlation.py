import logging
import os

import pandas as pd
import datetime as dt
import itertools
import glob
import argparse
import time

OUTPUT_CSV_PATH = os.path.join('output', f'output.csv')

SAMPLING_RATE = 'M'
CSV_DIRECTORY = '/home/tomer/workspace/workspace/financial_data/output/run_1590234732'

SAMPLING_RATE_NAMING = {'M': 'Monthly'}

COPY_TO_OUTPUT_THRESHOLD = 5

parser = argparse.ArgumentParser(description='Calculate correlation between stocks.')
parser.add_argument('--csv_dir',
                    metavar='d',
                    type=str,
                    default=CSV_DIRECTORY,
                    help='Directory where all the csv historical data is located')
parser.add_argument('--sampling_rate',
                    metavar='s',
                    type=str,
                    default=SAMPLING_RATE,
                    help='Sampling rate')

args = parser.parse_args()
CSV_DIRECTORY = args.csv_dir if args.csv_dir else CSV_DIRECTORY
SAMPLING_RATE = args.sampling_rate if args.sampling_rate else SAMPLING_RATE

try:
    os.mkdir('output')
except Exception:
    pass

logging.basicConfig(filename="output/log.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.getLogger().addHandler(logging.StreamHandler())


def calculate_correlation(first_stock, second_stock):
    first_stock_df = pd.read_csv(first_stock)
    second_stock_df = pd.read_csv(second_stock)

    first_stock_df['dailyret'] = first_stock_df['Close'].pct_change(1)
    second_stock_df['dailyret'] = second_stock_df['Close'].pct_change(1)

    second_stock_df.set_index(second_stock_df['Date'].apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%d')), drop=True, inplace=True)
    first_stock_df.set_index(first_stock_df['Date'].apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%d')), drop=True, inplace=True)

    first_stock_df = first_stock_df.resample(SAMPLING_RATE).mean()
    second_stock_df = second_stock_df.resample(SAMPLING_RATE).mean()

    first_stock_df['dailyret'] = first_stock_df['Close'].pct_change(1)
    second_stock_df['dailyret'] = second_stock_df['Close'].pct_change(1)

    first_daily_ret_mean = first_stock_df['dailyret'].mean()
    second_stock_dailyret_mean = second_stock_df['dailyret'].mean()

    second_stock_df['dailyret deviation'] = second_stock_df['dailyret'].apply(lambda x: x - second_stock_dailyret_mean)
    first_stock_df['dailyret deviation'] = first_stock_df['dailyret'].apply(lambda x: x - first_daily_ret_mean)

    min_date = max(second_stock_df.index[0], first_stock_df.index[0])
    max_date = min(second_stock_df.index[-1], first_stock_df.index[-1])

    first_stock_df = first_stock_df[min_date <= first_stock_df.index]
    first_stock_df = first_stock_df[first_stock_df.index <= max_date]

    second_stock_df = second_stock_df[min_date <= second_stock_df.index]
    second_stock_df = second_stock_df[second_stock_df.index <= max_date]

    deviation = first_stock_df['dailyret deviation'][1:]  * second_stock_df['dailyret deviation'][1:]
    covariance = sum(deviation) / (len(first_stock_df) - 1)
    #print("Covariance of Daily Return : ",  covariance)

    sigma_second = second_stock_df['dailyret'].std()
    sigma_first = first_stock_df['dailyret'].std()
    coeff_cor = covariance / (sigma_second * sigma_first)
    return coeff_cor


def main():
    listing = glob.glob(os.path.join(CSV_DIRECTORY, '*.csv'))
    stock_pairs = set([i for i in itertools.combinations(listing, 2)])

    output_path = None
    if os.path.exists(OUTPUT_CSV_PATH):
        output_path = OUTPUT_CSV_PATH
    elif os.path.exists(OUTPUT_CSV_PATH + '_1'):
        output_path = OUTPUT_CSV_PATH + '_1'

    if os.path.exists(output_path):
        results = pd.read_csv(output_path).to_dict()
        stock_pairs = set(stock_pairs).difference(set(zip(results['first'].values(), results['second'].values())))

        for key in results.keys():
            results[key] = list(results[key].values())
    else:
        results = {'first': [], 'second': [], 'sampling': [], 'correlation': []}

    logging.info(f'Found [{len(stock_pairs)}] pairs to check')

    process_counter = 0

    for pair in stock_pairs:
        first_stock, second_stock = pair
        try:
            logging.info(f'Calculating correlation for {first_stock} and {second_stock}')
            correlation = calculate_correlation(first_stock, second_stock)

            results['first'].append(first_stock)
            results['second'].append(second_stock)
            results['sampling'].append(SAMPLING_RATE_NAMING[SAMPLING_RATE])
            results['correlation'].append(correlation)

            process_counter = (process_counter + 1) % COPY_TO_OUTPUT_THRESHOLD
            if process_counter == 0:
                logging.info('Writing to output csv')
                if os.path.exists(OUTPUT_CSV_PATH):
                    if os.path.exists(OUTPUT_CSV_PATH + '_1'):
                        os.remove(OUTPUT_CSV_PATH + '_1')
                    os.rename(OUTPUT_CSV_PATH, OUTPUT_CSV_PATH + '_1')

                pd.DataFrame(results).to_csv(OUTPUT_CSV_PATH, columns=('first', 'second', 'sampling', 'correlation'))

        except Exception as e:
            logging.error(f'Failed calculating correlation for stocks: {pair}')
            logging.error(e)
        finally:
            logging.info('Writing to output csv')
            if os.path.exists(OUTPUT_CSV_PATH):
                if os.path.exists(OUTPUT_CSV_PATH + '_1'):
                    os.remove(OUTPUT_CSV_PATH + '_1')
                os.rename(OUTPUT_CSV_PATH, OUTPUT_CSV_PATH + '_1')

            pd.DataFrame(results).to_csv(OUTPUT_CSV_PATH, columns=('first', 'second', 'sampling', 'correlation'))


if __name__ == '__main__':
    main()
