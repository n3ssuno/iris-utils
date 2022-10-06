#!/usr/bin/env python

"""
Modules to work with natural language texts:
  first and foremost, organizations' legal names.
Part of the IRIS project.

Author: Carlo Bottai
Copyright (c) 2021 - TU/e and EPFL
License: See the LICENSE file.
Date: 2021-01-22

"""

import numpy as np
import pandas as pd
import re
import string
import unicodedata
from nltk.metrics import edit_distance
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

def standardize_legal_type(s):
    s_list = s.split(' ')
    s_last = s_list[-1]
    if s_last.startswith('CORP'):
        s_last = 'CORPORATION'
    if s_last.startswith('INC'):
        s_last = 'INCORPORATED'
    if s_last.startswith('COMP'):
        s_last = 'COMPANY'
    s = f"{' '.join(s_list[:-1])} {s_last}"

    return s

def checkspell_legal_entity_type(s):
    """Try to fix the spelling of the legal entity type
    Note: it works only if there is no more than one mistake letter"""
    legal_entity_types = [
        'LIMITED COMPANY',
        'LIMITED PARTNERSHIP',
        'REGISTERED LIMITED LIABILITY PARTNERSHIP',
        'LIMITED LIABILITY PARTNERSHIP',
        'REGISTERED LIMITED LIABILITY LIMITED PARTNERSHIP',
        'LIMITED LIABILITY LIMITED PARTNERSHIP',
        'PROFESSIONAL CORPORATION',
        'PROFESSIONAL SERVICE CORPORATION',
        'PROFESSIONAL LIMITED LIABILITY COMPANY',
        'LIMITED LIABILITY COMPANY',
        'PROFESSIONAL ASSOCIATION',
        'CORPORATION',
        'INCORPORATED',
        'COMPANY',
        'LIMITED',
        'REGISTERED PARTNERSHIP',
        'ASSOCIATION',
        'CLUB',
        'FOUNDATION',
        'FUND',
        'INSTITUTE',
        'SOCIETY',
        'UNION',
        'SYNDICATE',
        'BANK']
    detokenizer = TreebankWordDetokenizer()
    for legal_entity_type in legal_entity_types:
        legal_entity_type_len = len(word_tokenize(legal_entity_type))
        legal_entity_type_to_check = detokenizer.detokenize(
            word_tokenize(s)[-legal_entity_type_len:])
        if edit_distance(legal_entity_type, legal_entity_type_to_check)==1:
            return s.replace(legal_entity_type_to_check, legal_entity_type)
    return s

def standardize_string(s):
    # Remove blank spaces at the beginning/end of the name
    s = s.strip()

    # Remove punctuation at the end of the name
    s = re.sub(f'[{string.punctuation.replace(")","")}]$', '', s)
    # Remove part in parentheses at the end of the string
    #  e.g., 'FOO BAR INC (FB)' -> 'FOO BAR INC'
    s = re.sub('\s\(\w*\)$', '', s)

    # Transform everything in uppercase
    s = s.upper()
    
    # Remove THE and ET AL at the end of the name
    s = re.sub(',?( THE| ET AL\.?)+$', '', s)

    # The limited companies can be 'LTD' or 'LC'
    #  uniform everything to 'LTD'
    if not (re.search(r'P\.?\s?L\.?\s?L\.?\s?C\.?$', s) or re.search(r'L\.?\s?L\.?\s?C\.?$', s)):
        s = re.sub(' L\.?\s?C\.?$', ' LTD', s)

    s_match = re.findall('(.*)\s?\([0-9]+\)?$',s)
    if len(s_match)>0:
        s = s_match[0]

    s = checkspell_legal_entity_type(s)
    
    legal_entity_types_dict = {
        'LIMITED COMPANY': 'LTD',
        'LIMITED PARTNERSHIP': 'LP',
        'REGISTERED LIMITED LIABILITY PARTNERSHIP': 'RLLP',
        'LIMITED LIABILITY PARTNERSHIP': 'LLP',
        'REGISTERED LIMITED LIABILITY LIMITED PARTNERSHIP': 'RLLLP',
        'LIMITED LIABILITY LIMITED PARTNERSHIP': 'LLLP',
        'PROFESSIONAL CORPORATION': 'PC',
        'PROFESSIONAL SERVICE CORPORATION': 'PSC',
        'PROFESSIONAL LIMITED LIABILITY COMPANY': 'PLLC',
        'LIMITED LIABILITY COMPANY': 'LLC',
        'PROFESSIONAL ASSOCIATION': 'PA',
        'CORPORATION': 'CORP',
        'INCORPORATED': 'INC',
        'COMPANY': 'CO',
        'LIMITED': 'LTD'}
    for k,v in legal_entity_types_dict.items():
        # Transform from long to short form
        s = re.sub(f' {k}$', f' {v}', s)
        # Remove the dots from the short form
        s = re.sub(' ' + ''.join([c+'\.?' for c in v]) + '$', f' {v}', s)
        # Remove the comma between the name and the legal type
        s_match = re.match(f'(.*[^,]),? ({v})$', s)
        if s_match is not None:
            s = ' '.join(s_match.groups())
        # Remove the dot from CO that sometimes comes before the legal type
        s = re.sub(f' CO\.? {v}$', f' CO {v}', s)
        s = re.sub(f' COMPANY {v}$', f' CO {v}', s)
    s = re.sub('\(?PROPRIETARY\)?', f'PTY', s)

    return s

def clean_string(s, remove_spaces=True):
    if remove_spaces:
        s = s.replace(' ','')
    else:
        s = s.strip()
    s = s.replace('(','')
    s = s.replace(')','')
    s = s.replace('-','')
    s = s.replace(',','')

    return s

def compare_string_wo_legal_type(s, remove_spaces=True):
    # Remove legal entity type
    legal_entity_types_set = {
        'CORP',
        'INC',
        'CO',
        'LTD',
        'LLC',
        'LP',
        'RLLP',
        'LLP',
        'RLLLP',
        'LLLP',
        'PC',
        'PLLC',
        'SC',
        'PA',
        'REGISTERED PARTNERSHIP', # also "XYZ, a registered partnership" exists
        'ASSOCIATION',
        'CLUB',
        'FOUNDATION',
        'FUND',
        'INSTITUTE',
        'SOCIETY',
        'UNION', # also "credit union" and "federal credit union" exist
        'SYNDICATE',
        'BANK'
    }
    for lt in legal_entity_types_set:
        s_match = re.match(f'(.*)\s?(CO\s)?{lt}(\s[A-Z]{{0,3}})?$', s)
        if s_match is not None:
            s = s_match.group(1)

    # Remove 'holding(s)' from the name
    s = re.sub(' HOLDINGS?', '', s)
    
    # Remove 'The' at the beginning of the name
    s = re.sub('^THE ', '', s)
    
    # Use '&' instead of 'AND'
    s = re.sub('\sAND\s', ' ', s)
    s = re.sub('\s&\s', ' ', s)
        
    # Remove spaces and some punctuation
    s = clean_string(s, remove_spaces)
    
    s = s.replace('ENGRG','ENGINEERING')

    return s

def strip_accents(s):
    if pd.isna(s):
        return np.nan
    return ''.join(
        c for c in unicodedata.normalize('NFD', s) \
        if unicodedata.category(c) != 'Mn')
