#!/usr/bin/env python

"""
Modules to collect the award IDs linked to scientific publications
  according to the information provided by CrossRef.
Part of the IRIS project.

Author: Carlo Bottai
Copyright (c) 2021 - TU/e and EPFL
License: See the LICENSE file.
Date: 2021-01-07

"""

import numpy as np
import pandas as pd
import requests
import time
from tqdm import tqdm

def get_data_from_crossref(dois_list, email_addr):
    dois_chunks = [dois_list[i:i+100] for i in range(0, len(dois_list), 100)]
    df_with_award_ids = []
    for dois_chunk in tqdm(dois_chunks):
        dois = ','.join([f'doi:{doi}' for doi in dois_chunk])
        query = 'https://api.crossref.org/works?' \
                f'filter={dois},has-funder:true&' \
                'select=DOI,funder&' \
                f'mailto={email_addr}'
        while True:
            try:
                response = requests.get(query, timeout=5)
                if response.status_code==200:
                    break
                else:
                    time.sleep(10)
            except:
                time.sleep(10)
        results = response.json()['message']['items']
        df = []
        for result in results:
            if 'funder' in result.keys():
                awards = []
                for funder in result['funder']:
                    if 'award' in funder.keys():
                        awards.extend(funder['award'])
                    else:
                        awards.append(np.nan)
                df.append({'doi': result['DOI'], 'award_id': awards})
            else:
                df.append({'doi': result['DOI'], 'award_id': [np.nan]})
        df_with_award_ids.extend(df)
    df_with_award_ids = pd.DataFrame(df_with_award_ids)
    df_with_award_ids = df_with_award_ids.explode('award_id')
    df_with_award_ids.drop_duplicates(inplace=True)

    return df_with_award_ids