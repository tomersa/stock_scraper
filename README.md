This scraper takes all the csv files in the input/ directory and run each one separately.
csv files are expected to be in the following format:
ticker, name
^MSFT,"Microsoft corp"
^AAPL,"Apple corp"

See an example in the input/all_sp_500.csv


An example on how to run can be found in the run.sh


The output will be in the output directory. With a directory for each csv file from the input. It will contain a csv for each stock in the form of[stock]_historical_data.csv
