import requests
import json
import os
import numpy as np
import random

def defi_lama_mcap_tvl():
    #url = "https://api.llama.fi/protocols"
    url = "https://api.llama.fi/summary/fees/GMX"

    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        formatted_data = json.dumps(data, indent=4)

        # mcap_to_tvl_rat = []
        # for item in data:
        #     try:
        #         if float(item['name']) == 'GMX' and float(item['mcap'] > 100000):
        #             mcap_to_tvl_rat.append(float(item['tvl']) / float(item['mcap']))
        #     except:
        #         pass

        # print(mcap_to_tvl_rat)
        # print("Total sampled protocols: " + str(len(mcap_to_tvl_rat)))
        # print("Average mcap to tvl ratio: " + str(np.mean(mcap_to_tvl_rat)))
        with open('defi_lama_data.json', 'w') as f:
            f.write(formatted_data)
        
        #return mcap_to_tvl_rat
    else:
        print("Error retrieving defi lama protocols data.")

def list_lib():
    # list all of the files in the directory ./perpetuals/programs/perpetuals/src/instructions and print them to terminal
    for filename in os.listdir('./perpetuals/programs/perpetuals/src/instructions'):
        print(filename)

def tst():

    a = 3

    if 1 < a < 5:
        print(a)
    else:
        print('none')


def main():
    #defi_lama_mcap_tvl()
    #list_lib()
    tst()


if __name__ == "__main__":
    main()