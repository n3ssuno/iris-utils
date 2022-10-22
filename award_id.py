#!/usr/bin/env python

"""
Modules to extract the award id number from the government-interest statements
 found in the texts of US patents.
 Part of the IRIS project.

Author: Carlo Bottai
Copyright (c) 2020 - TU/e and EPFL
License: See the LICENSE file.
Date: 2020-11-17

"""

# TODO Find a better solution to generalize this line
folder = 'data/interim'

def removePunctuation(word, preserve=None):
    import string
    punctuation = string.punctuation
    if preserve is not None:
        for c in preserve:
            punctuation = punctuation.replace(c,'')
    word = word.translate(str.maketrans('','',punctuation))
    return word

def getBasicForm(word):
    from nltk.stem.wordnet import WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()
    # Remove punctuation
    word = removePunctuation(word)
    # Take the lower case for each letter in the string
    word = word.lower()
    # Take the singular form of the word
    word = lemmatizer.lemmatize(word)
    # Take the present tense of the word
    word = lemmatizer.lemmatize(word,'v')
    return word

def includeWord(word):
    from nltk.corpus import words
    
    word = removePunctuation(word)
    if len(word)<3 and word.isupper() and word.isalpha():
        return True
    if any(c.isdigit() for c in word):# and sum(c.islower() for c in word)<3: # TO HAVE EXCLUDED THE WORDS WITH LOWER CHARS. IS POTENTIALLY DANGEROUS -> NOW IT RETAINS WORDS WITH ONE OR TWO LOWER CHARS. (THIS ACCOUNTS FOR OCR MISTAKES AND SIMILAR)
        return True
    if getBasicForm(word) not in words.words():# and (not any(c.isdigit() for c in word)):
        return True

def isYear(word, current_year):
    import re
    match = re.match(r'(^(19|20)[0-9]{2}$)', word)
    if match is None:
        return False
    else:
        match = match.group(1)
        if int(match) <= current_year:
            return True
        else:
            return False

def isAcronym(word, excludedAcronyms):
    import re
    
    word = removePunctuation(word, '-/')
    word_ = removePunctuation(word)
    if (word_.isupper() and 
        word_.isalpha() and 
        any([w in excludedAcronyms for w in re.split('-|/',word)])):
        return True
    return False

def addIsolated(all_strings, identified_string_idx,
                other_identified_strings,
                excludedAcronyms, stops,
                forward=False):
    # TODO
    # Maybe the forward search can be implemented
    #  by reverting the all_strings list, i.e. all_strings[::-1]
    from nltk.corpus import words
    import re
    
    #i = all_strings.index(identified_string)
    identified_string = all_strings[identified_string_idx]
    i = identified_string_idx
    if ((not forward and i==0) or 
        (forward and i==(len(all_strings)-1))):
        return identified_string
    if not forward:
        candidate_piece_idx = i-1
    else:
        candidate_piece_idx = i+1
    candidate_piece = all_strings[candidate_piece_idx]
    if ((forward and 
        (identified_string[-1:] in stops or
         candidate_piece[:1] in stops)) or 
        (not forward and 
        (identified_string[:1] in stops or
         candidate_piece[-1:] in stops))):
        return identified_string
    candidate_piece = candidate_piece.translate(str.maketrans('','',stops))
    if ((candidate_piece.isupper() and 
         #removePunctuation(candidate_piece).isalpha() and
         not isAcronym(candidate_piece, excludedAcronyms)) or
         (len(removePunctuation(candidate_piece))<5 and 
          removePunctuation(candidate_piece).isnumeric())):
        new_sg = addIsolated(all_strings, candidate_piece_idx, 
                             other_identified_strings,
                             excludedAcronyms, stops, forward)
        if isinstance(new_sg, list):
                new_sg = new_sg[0]
        if not forward:
            if (len(all_strings)>(i+2) and 
                all_strings[i+1]=='and' and 
                all_strings[i+2]!=new_sg and 
                not any(c.islower() for c in all_strings[i+2]) and
                not isAcronym(all_strings[i+2], excludedAcronyms) and
                all_strings[i+2] not in words.words() and 
                abs(len(identified_string)-len(all_strings[i+2]))<2):
                if len(all_strings)>(i+3):
                    if all_strings[i+3] not in other_identified_strings:
                        return [new_sg + '+' + identified_string, 
                                new_sg + '+' + all_strings[i+2]]
                    else:
                        return [new_sg + '+' + identified_string]
                else:
                    return [new_sg + '+' + identified_string, 
                            new_sg + '+' + all_strings[i+2]]
            else:
                return [new_sg + '+' + identified_string]
        else:
            return [identified_string + '+' + new_sg]
#     else:
    return identified_string

def excludeLaws(gi_statement):
    # These regexs are based on the one provided by the USPTO
    #  You can find it here
    #  https://github.com/CSSIP-AIR/government-interest-parsing
    import re
    
    #gi_statement = gi_statement.replace('§','')
    
    len_check = len(gi_statement)
    
    if len(re.findall('S\.?B\.?I\.?R\.?',gi_statement))>0:
        sbir_statement = '106-554, Small Business Reauthorization Act of 2000' # It seems that there is only one case like this. Remove or generalize...
        gi_statement = re.sub(sbir_statement,'',gi_statement)
    
    #if len(re.findall('N\.?A\.?S\.?A\.?',gi_statement))>0:
    nasa_statement = ('([Ss]ection\s)?(305|20135\(b\)) of the (National '
                      'Aeronautic(s)? (&|and) Space|NASA) Act(ion)?'
                      '(\s(of\s)?\(?1958)?')
    gi_statement = re.sub(nasa_statement,'',gi_statement)
    
    law_statements = [
        'P(ublic|\.) [Ll](aw|\.) \d{2,3}\s?[-–]+\s?\d{2,3}', # dovrei aver sostituito – con -, quindi qui non dovrebbe piu' servire...
        ('([\(\s]\d{2,3}\s)?[Uu]\.?[Ss]\.?\s?[Cc]\.?([Pp]\.?)?\s?'
         '(§|\.?sctn\.?|[Cc]hapter|[Ss]ec(tion|\.)?)?\s*(111-)?'
         '\d{3,6}'),
        ('[1-4][0-9]\s?C\.?F\.?R\.?\s?'
         '([Ss]ec(tion|\.)|\.sctn\.|[Pp]art|§)?\s?[0-9\.-]+\s?'
         '(\([A-Za-z]\))?\s?(\([0-9]\))?(\([ivx]{1,3}\))?'),
        '[Ff][Aa][Rr]\s([Rr]egulation\s)?[0-9\.-]+',
        '((\d{2,3}\s)?[Ss][Tt][Aa][Tt]?(ute)?\.?\s\d{3,4})\|?(?![\d-])',
        'ASPR (Section\s)?7-\d{3}.\d{2}(\s?\([a-z]\))?'
    ]
    for law_statement in law_statements:
         gi_statement = re.sub(law_statement,'',gi_statement)
    
#     law_statement = ('(\d{2,3}\s?[-–]+\s?\d{2,3}|(\d{2}\s)?[Uu]\.?[Ss]\.?'
#                      '[Cc]\.?\s&?(§|\.?sctn\.?|[Cc]hapter|&?[Ss]ec(t)?'
#                      '(ion|\.)?)?[\s;]{0,2}(111-)?\d{3,6}|(\d{2,3}\s)?'
#                      '[Ss][Tt][Aa][Tt]?\.?\s\d{3,4})\|?(?![\d-])|'
#                      '([Ff][Aa][Rr]\s([Rr]egulation\s)?[0-9\.-]+)|'
#                      '(48 CFR 52\.227-11)|(402 U\.?S\.?\s?C\.?P\.? 2457)|'
#                      '(72 Statute 435)')
    
    public_law = False
    if len(gi_statement) < len_check or gi_statement.find('Public Law')!=-1:
        public_law = True
    
    return gi_statement, public_law

def findAgency(gi_statement, agencies, nih_institutes):
    import re
    import string
    
    def wordFinder(word, string):
        if re.search(r"\b" + re.escape(word) + r"\b", string):
            return True
        return False
    
    punctuation = string.punctuation.replace('-','')
    
    # TODO
    # This function assumes specific names for the columns of the two 
    #  dataframes: Must be generalised
    
    # Remove the dots to avoid problems with institutions reported
    #  like N.A.S.A. instead of as NASA
    gi_statement = gi_statement.replace('.','')
    for i in punctuation:
        gi_statement = gi_statement.replace(i,' ')
    gi_statement = re.sub('\s+', ' ', gi_statement)
    #gi_statement = gi_statement.translate(
    #    str.maketrans('', '', punctuation))
    gi_statement_low = gi_statement.lower()
    agencies.TITLE = agencies.TITLE.str.lower()
    agencies = agencies.applymap(lambda col: col.translate(
        str.maketrans('', '', punctuation)))
    agencies = agencies[agencies.ACNM!='DARPA']
    nih_institutes.TITLE = nih_institutes.TITLE.str.lower()
    nih_institutes = nih_institutes.applymap(lambda col: col.translate(
        str.maketrans('', '', punctuation)))
        
    ags = []
    for idx,agency in agencies.iterrows():
        if (wordFinder(agency[0],gi_statement) or
            wordFinder('US'+agency[0],gi_statement) or
            wordFinder(agency[1],gi_statement_low) or
            wordFinder(agency[1].replace('department','dept'),
                       gi_statement_low)):
            ags.append(agency[0])
    if wordFinder('Army',gi_statement):
        ags.append('USA')
    if wordFinder('Navy',gi_statement): # or wordFinder('office of naval research',gi_statement_low)
        ags.append('USN')
    if wordFinder('Air Force',gi_statement):
        ags.append('USAF')
    if 'NIH' not in ags:
        if wordFinder('National Institute of Health',gi_statement):
            ags.append('NIH')
        else:
            for idx,agency in nih_institutes.iterrows():
                if (wordFinder(agency[0],gi_statement) or
                    wordFinder(agency[1],gi_statement_low)):
                    ags.append('NIH')
    if 'NRSA' in ags: # This should be generalized to any case in which there is a sub-agency of another agency already present in the list (e.g. ONR)
        ags = [a.replace('NRSA','NIH') for a in ags]
    darpae = '(advanced research projects agency|ARPA)\s*(E|energy)'
    darpa = '(advanced research projects agency|ARPA)'
    if (re.search(darpae,gi_statement.replace('-','')) is not None or
        re.search(darpae,gi_statement_low.replace('-','')) is not None):
        ags.append('DOE')
    elif (re.search(darpa,gi_statement) is not None or
          re.search(darpa,gi_statement_low) is not None):
        ags.append('DARPA')
    
    ags = set(ags)
    ags = '|'.join(ags)
    return ags

def findCity(df, city):
    # TODO
    # This function assumes a specific name for the column
    # Must be generalized
    if any(df.gi_statement.str.find(city)!=-1):
        return city
    return None

def removeShorter(award_ids):
    award_ids.sort(key=len)
    award_ids_ = award_ids[:]
    for i,w in enumerate(award_ids_[:-1]):
        if any(w in o for o in award_ids_[i+1:]):
            award_ids.remove(w)
    award_ids = sorted(award_ids)
    return award_ids

def removeDates(s):
    import re
    
    months = ['January','February','March',
              'April','May','June','July',
              'August','September','October',
              'November','December']
    for month_idx,month in enumerate(months):
        month_ = month[:]
        month = f'[{month[:1]}{month[:1].lower()}]{month[1:3]}'
        if len(month_)>3:
            month = f'{month}[{month_[3:]}\.]?'
        day = '(0?[1-9]|[12]\d|3[01])'
        year = '(19|20)\d{2}(?!\d)'
        date = f'{month} ({day}(-{day})?,\s)?{year}'
        s = re.sub(date,' ',s)
        
        month_idx += 1
        if month_idx<10:
            month_idx = f'0?{month_idx}'
        else:
            month_idx = str(month_idx)
        year = '(19|20)?\d{2}'
        date_idx = f'\s\(?{month_idx}/{day}/{year}[\),;:\.]?\s'
        s = re.sub(date_idx,' ',s)
        s = re.sub('\s+',' ',s)
    
    return s

def removeZip(s, zipcodes):
    # TODO
    # This assumes a specific name for the columns, must be generalized
    import re
    s = s.replace('Redstone Arsenal','Huntsville')
    for idx, zipcode in zipcodes.iterrows():
        if s.find(zipcode['City'])!=-1:
            zc = zipcode['Zipcode']
            target = f'({zc})(-\d{{4}})?'
            s = re.sub(target,'',s)
    return s

def htmlTOunicode(text):
    # TODO
    # Maybe it could be nicer to consider all the possible html codes (remember that &num; is very important and doesn't seem to be officially part of these codes)
    translate = {'&mdash;':'-',
                 '&num;':'#',
                 '&ldquo;':"'",
                 '&rdquo;':"'",
                 '&apos;':"'",
                 '&amp;':'&',
                 '&equals;':'=',
                 '&lsqb;':'[',
                 '&rsqb;':']',
                 '&quest;':'?',
                 '&sect;':'§',
                 '&Ovalhollow;':'', # probably an OCR mistake
                 '&Oslash;':'0', # should be Ø but is a mistake of the OCR
                 '&Prime;':"'",
                 '&plus;':'+',
                 '&oacute;':'ó',
                 '&apos;':"'",
                 '&times;':'x',
                 '&copy;':'(c)',
                 '&mgr;':'mu'} 
    for k,v in translate.items():
        text = text.replace(k,v)
    return text

def award_ids_modifier(s):
    import re
    def modificationRule(gis):
        gis1 = gis.group(1)
        gis2 = gis.group(2)
        gis3 = re.findall('[0-9]+', gis.group(3))
        gis4 = gis.groups()[-1:][0]
        gis = [f'{gis1}+{w}' for w in [gis2] + gis3 + [gis4]]
        gis = ', '.join(gis)
        gis = f' {gis} '
        return gis
    pattern = ('[\s\(]([A-Z]{2})([0-9]{4,7})((, [0-9]{4,7})*),?'
               ' and ([0-9]{4,7})[\s\)]')
    s = re.sub(pattern, modificationRule, s)
    return s

def removeTitle(s):
    import re
    common_pattern = '“.+”'
    patterns = [f'[Ll]abeled:? {common_pattern}',
                f'([Ee]n)?[Tt]itle(d)?:? {common_pattern}',
                f'[Uu]nder {common_pattern} ([Pp]rogram|[Cc]ontract)',
                f'project name:? {common_pattern}']
    for pattern in patterns:
        s = re.sub(pattern,'',s)
    return s

def removeFile(s, stops):
    import re
    import string
    from nltk.tokenize import RegexpTokenizer
    from nltk.corpus import words
    
    punctuation = string.punctuation
    #punctuation += '—'
    
    tokenizer = RegexpTokenizer('\w+')
    
    tokens = tokenizer.tokenize(s)
    idxs = [i for i,w in enumerate(tokens) if w.lower()=='txt']
    for idx in idxs:
        i = 1
        while getBasicForm(tokens[idx-i]) not in words.words():
            i += 1
        idx += 1
        #for w in tokens[idx-i:idx]:
        #    s = s.replace(w,'')
        pattern = f'[{punctuation}\s]+'
        pattern = f'{pattern}'.join(tokens[idx-i:idx])
        s = re.sub(pattern,'',s)
    
    for c in stops:
        punctuation = punctuation.replace(c,'')
    #s = re.sub(f'[{punctuation}“”]{{2,}}','',s)
    s = re.sub('“\s*”','',s)
    s = re.sub('\s+',' ',s)
    return s

import multiprocessing as mp
def award_id_extractor_preprocessor(df, n_cores = mp.cpu_count()-1):
    import pandas as pd
    import os
    import requests
    
    try:
        with open(f'{folder}/acronyms.txt', 'r') as input_file:
            acronyms = input_file.read().splitlines()
        agencies = pd.read_csv(f'{folder}/agencies.tsv', sep='\t')
        nih_institutes = pd.read_csv(f'{folder}/nih_institutes.tsv', sep='\t')
        zipcodes = pd.read_csv(f'{folder}/zipcodes.tsv', sep='\t')
    except:
        print(('Some needed file is lacking\n'
               'Fixing this issue may take time...'))
        if (not os.path.isfile(f'{folder}/acronyms.txt') or 
            not os.path.isfile(f'{folder}/agencies.tsv')):
            print('Create agencies.tsv and/or acronyms.txt')
            from tabula import read_pdf
            import pandas as pd
            file_name = 'GOVMAN-2018-12-03-Commonly-Used-Agency-Acronyms-105.pdf'
            if not os.path.isfile(f'{folder}/{file_name}'):
                url = 'https://www.govinfo.gov/content/pkg/GOVMAN-2018-12-03/pdf/'
                url = url+file_name
                response = requests.get(url)
                with open(f'{folder}/{file_name}', 'wb') as f_out:
                    f_out.write(response.content)
                #os.system(f'wget {url} -P {folder}/')
            agencies = []
            for i in range(8):
                df = pd.concat(read_pdf((f'{folder}/'
                                         'GOVMAN-2018-12-03-Commonly-'
                                         'Used-Agency-Acronyms-105.pdf'), 
                                         pages=i+1, multiple_tables=False))
                df.columns = ['ACNM','TITLE']
                agencies.append(df)
            agencies = pd.concat(agencies)
            agencies = agencies[~agencies.TITLE.isna()].drop_duplicates()
            agencies.TITLE = agencies.TITLE.str.replace('\r',' ')
            agencies.reset_index(drop=True, inplace=True)
            to_fix = agencies.index[agencies.ACNM.isna()]
            for idx in to_fix:
                agencies.iloc[idx-1,1] = ' '.join([agencies.iloc[idx-1,1],
                                                   agencies.iloc[idx,1]])
            agencies.drop(to_fix, inplace=True)
            agencies.reset_index(drop=True, inplace=True)
            agencies_add = [{'ACNM':'ERDA',
                             'TITLE':('ENERGY RESEARCH AND'
                                      ' DEVELOPMENT ADMINISTRATION')},
                            {'ACNM':'FEA',
                             'TITLE':'FEDERAL ENERGY ADMINISTRATION'},
                            {'ACNM':'ARO',
                             'TITLE':'ARMY RESEARCH OFFICE'},
                            {'ACNM':'ONR',
                             'TITLE':'OFFICE OF NAVAL RESEARCH'},
                            {'ACNM':'AFSOR', # It seems it can be spelled in both ways
                             'TITLE':'AIR FORCE OFFICE OF SCIENTIFIC RESEARCH'},
                            {'ACNM':'AFOSR', # It seems it can be spelled in both ways
                             'TITLE':'AIR FORCE OFFICE OF SCIENTIFIC RESEARCH'},
                            {'ACNM':'ARPA-E',
                             'TITLE':('ADVANCED RESEARCH PROJECTS'
                                      ' AGENCY-ENERGY')},
                            {'ACNM':'NRSA',
                             'TITLE':'NATIONAL RESEARCH SERVICE AWARD'},
                            {'ACNM':'MRMC',
                             'TITLE':'MEDICAL RESEARCH AND MATERIEL COMMAND'},
                            {'ACNM':'USPHS',
                             'TITLE':'UNITED STATES PUBLIC HEALTH SERVICE'}, # ESISTE GIA NELLA LISTA MA COME "PHS" 
                            {'ACNM':'CRADA',
                             'TITLE':'COOPERATIVE RESEARCH AND DEVELOPMENT AGREEMENTS'}
                            
                           ]
            agencies_add = pd.DataFrame(agencies_add)
            agencies = agencies.append(agencies_add, 
                                       ignore_index=True)

            agencies.to_csv(f'{folder}/agencies.tsv', sep='\t', index=False)
            print('agencies.tsv created')

            agencies = agencies.ACNM.tolist()
            agencies.append('ARPA')
            agencies = list(pd.Series(agencies).dropna())#.to_list()
            # There is a list of agencies also in the USPTO government 
            #  interest statement extractor script
            #  https://www.dropbox.com/sh/
            #   uxv1e6ifyx0vpf5/AAAy1lVmlCgBHBTDG5zv5rDGa?dl=0
            abbreviations = ['LLC','SBIR','STTR','ARMY','NAVY']
            acronyms = [acm for acm in agencies+abbreviations if len(acm)!=2]
            with open(f'{folder}/acronyms.txt', 'w') as out_file:
                for acronym in acronyms:
                    out_file.write("%s\n"%acronym)
            print('acronyms.txt created')

        if not os.path.isfile(f'{folder}/nih_institutes.tsv'):
            print('Create nih_institutes.tsv')
            nih_url = \
                'https://en.wikipedia.org/wiki/List_of_institutes' \
                '_and_centers_of_the_National_Institutes_of_Health'
            nih_institutes = pd.read_html(nih_url,header=0)[0].iloc[:,[1,0]]
            nih_institutes.rename(columns={'Acronym':'ACNM','Name':'TITLE'}, 
                                  inplace=True)
            nih_institutes.to_csv(f'{folder}/nih_institutes.tsv', sep='\t', index=False)
            print('nih_institutes.tsv created')

        if not os.path.isfile(f'{folder}/zipcodes.tsv'):
            import re
            
            print(('Create zipcodes.tsv\n'
                   'It takes a lot of time...'))
            
            zipcodes_url = \
                'http://federalgovernmentzipcodes.us/' \
                'free-zipcode-database-Primary.csv'
            zipcodes = pd.read_csv(zipcodes_url, usecols=[0,2], dtype=str)
            zipcodes['City'] = zipcodes.City.str.title()
            zipcodes = zipcodes.groupby('City')
            zipcodes = zipcodes.Zipcode.apply(lambda x: '|'.join(x))
            zipcodes = zipcodes.reset_index()
            cities = zipcodes.City.tolist()
            if n_cores==1:
                cts = [findCity(df, city) for city in cities]
            else:
                #import multiprocessing as mp
                from pathos.multiprocessing import ProcessingPool as Pool
                from functools import partial
                pool = mp.Pool(n_cores)
                cts = pool.map(partial(findCity, df), [city for city in cities])
                pool.close()
            cts = list(filter(None.__ne__, cts))
            cts.append('Huntsville') ###################################################################### 
            zipcodes = zipcodes[zipcodes.City.isin(cts)]
            # The zip codes used are probably too uptodate
            #  The following is a very important case, 
            #  but maybe there are others that have to be fixed
            fix_bethesda = zipcodes.loc[zipcodes.City=='Bethesda','Zipcode']
            fix_bethesda = fix_bethesda+'|20014'
            zipcodes.loc[zipcodes.City=='Bethesda','Zipcode'] = fix_bethesda
            zipcodes.to_csv(f'{folder}/zipcodes.tsv', sep='\t', index=False)
            #cities = []
            #for city in set(zipcodes_all.City):
            #    if any(dta_uspto.gi_statement.str.find(city)!=-1):
            #        cities.append(city)
            #zipcodes_all = zipcodes_all[zipcodes_all.City.isin(cities)]
            #zipcodes = [('City','Zipcode')]
            #for idx, zp in zipcodes_all.iterrows():
            #    if any(((dta_uspto.gi_statement.str.find(zp['City'])!=-1) and
            #            (dta_uspto.gi_statement.str.find(zp['Zipcode'])!=-1))):
            #        zipcodes.append(zp)
            #with open(f'{folder}/zipcodes.tsv', 'w') as out_file:
            #    for zipcode in zipcodes:
            #        out_file.write("%s\t%s\n"%zipcode)
            print('zipcodes.tsv created')
            
        return award_id_extractor_preprocessor(df, n_cores)
        
    return acronyms, agencies, nih_institutes, zipcodes

def award_id_extractor(s, inputs, current_year=None):
    """the 'inputs' are a tuple with the four variables produced by 
    award_id_extractor_preprocessor() and is mandatory
    """
    import numpy as np
    import pandas as pd
    import re
#     import string
    from nltk.corpus import words
    from nltk.tokenize import RegexpTokenizer
    
    # TODO
    # I think it is not a very elegant way to solve this problem,
    #  since it is not intuitive how this process works
    #  (running a preprocessor and than pass its output to another
    #  function), but I have no better ideas at the moment
    acronyms, agencies, nih_institutes, zipcodes = inputs
    
    # This is a patch, since I forgot to add the nih_institutes to the 
    #  acronyms list. It must be definitively fixed in the 
    #  award_id_extractor_preprocessor function
    acronyms = acronyms + nih_institutes.ACNM.tolist()
    
    if current_year is None or np.isnan(current_year):
        import datetime
        now = datetime.datetime.now()
        current_year = now.year
    
#     punctuation = string.punctuation
#     punctuation = punctuation.replace('-','')
#     punctuation = punctuation.replace('&','')
#     punctuation = punctuation.replace('#','')
#     punctuation = punctuation.replace('/','') #QUESTA DECISIONE E' VERAMENTE MOLTO DIFFICILE
#     punctuation = punctuation.replace('.','')
#     punctuation = punctuation.replace(',','')
#     punctuation = punctuation.replace(';','')
#     punctuation = punctuation.replace(':','')
#     #punctuation = punctuation.replace('(','')
    
    stops = '.,;:' #(&/ #QUESTA DECISIONE E' VERAMENTE MOLTO DIFFICILE
    
    # Add a space near the punctuation when it is missing
    s = re.sub('(;)([A-Za-z0-9])',lambda x: ' '.join(x.groups()),s)
    s = re.sub('(:)([A-Za-z0-9])',lambda x: ' '.join(x.groups()),s)
    s = re.sub('(\))([A-Za-z0-9])',lambda x: ' '.join(x.groups()),s)
    s = re.sub('([A-Za-z0-9])(\()',lambda x: ' '.join(x.groups()),s)
    #s = s.replace('(',' (')
    #s = s.replace(')',') ')
    
    #tokenizer = RegexpTokenizer(r'[-,\w]+')
    tokenizer = RegexpTokenizer(f'[-/&{stops}\w]+') #/ #QUESTA DECISIONE E' VERAMENTE MOLTO DIFFICILE valutare se tenere unite le parole separate da / o meno!
#     for i in punctuation:
#         gi_statement = gi_statement.replace(i,' ')
#     gi_statement = re.sub('\s+', ' ', gi_statement)
    
    # Fix html char. codes 
    s = htmlTOunicode(s)
    # Remove consecutive hyphens
    s = s.replace('--','-')
    # Replace dashes with the hyphen # TODO Which other dashes exist? They are not included in string.puctuation and so they can create problems...
    for c in ['–','—']:
        s = s.replace(c,'-')
    # Remove the double blank spaces
    s = re.sub('\s+',' ',s)
    
    # Find the agency to help the matching
    ags = findAgency(s, agencies, nih_institutes)
    
    # Remove the text related to the 'CROSS-REFERENCE TO RELATED APPLICATIONS' 
    #  section that is, sometimes, erroneously reported after the government 
    #  statement section. Moreover, also the patent numbers are removed
    #s = re.split('(RELATED|PRIOR|OTHER) (PATENT\s)?APPLICATIONS?',s)[0]
    s = re.sub('((Ser|Pat)(ent|\.)? (No\.?|[Aa]pplication)|S\.?N\.?) (\d{1,2}[/,])?\d{3}[/,]\s?\d{3}','',s)
    s = re.sub('\d{2}/\d{3},\d{3}','',s)
    s = re.sub('PCT[/\s]([A-Z]{2}|W0)\d{2,4}/\d{5,6}','',s)
    # Remove the parts related to laws
    s,pl = excludeLaws(s)
    # Remove the zip codes of the US cities
    s = removeZip(s, zipcodes)
    # Remove post office box number
    s = re.sub('P.O. Box \d+','',s)
    
    # Remove dates from the text (like Dec. 16, 2019)
    s = removeDates(s)
    # Remove title of the project
    s = removeTitle(s)
    # Remove name of files like xxx.txt
    if s.find('.txt')!=-1:
        s = removeFile(s, stops=stops)
    
    # Remove some words from few specific cases that are particularly 
    #  complicated. This portion of code comes mostly from the USPTO script 
    #  that you can find here: 
    #  https://github.com/CSSIP-AIR/government-interest-parsing/
    #   blob/master/NER.py
    
    len_check = len(s)
    s = re.sub(('Licensing (and technical )?inquiri?es may be directed to'
                ' .+\.(mil|gov)\.?'),'',s)
    if (s.find('Legal Counsel')!=-1 or
         s.find('Space and Naval Warfare Systems')!=-1):
        if s.find('Calif')!=-1:
            del_pattern = ('[Cc]ode \d{4,5}|'
                           'D0012|53510|53560|'
                           '(619)?\)?[-\s]?553-\d{4}|'
                           '[\w.]+@[\w.]*navy\.mil|'
                           '(([Rr]eferenc(e|ing)\s)|'
                           '([Nn]avy [Cc]ase\s)|'
                           '(NC\s))+(Number|No\.?)?\s?[\d\,\.]{5,7}')
            s = re.sub(del_pattern,'',s)
        elif  s.find('S.C.')!=-1:
            del_pattern = ('[Cc]ode [A-Z0-9\-]+|'
                           '29419(-9022)?|'
                           '(843)?\)?[-\s]?218-\d{4}|'
                           '[\w.]+@[\w.]*navy\.mil|'
                           '(([Rr]eferenc(e|ing)\s)|'
                           '([Nn]avy [Cc]ase\s)|'
                           '(NC\s))+(Number|No\.?)?\s?[\d\,\.]{5,7}')
            s = re.sub(del_pattern,'',s)
    if len_check > len(s):
        s = re.sub(('(([Rr]eferenc(e|ing)\s)|([Nn]avy [Cc]ase\s)|'
                    '(NC\s))+(Number|No\.?)?\s?[\d\,\.]{5,7}'),'',s)
    
    if s.find('Environmental Protection Agency')!=-1:
        s = s.replace('1025 F St','')
    s = s.replace(('(COOPERATIVE RESEARCH AND TECHNOLOGY ENHANCEMENT '
                   'ACT OF 2004 (CREATE ACT) (PUB. L. 108-453, 118 STAT.'
                   ' 3596 (2004))'),'')
    s = s.replace('CIRID at UCLA','')
    
    # Replace Eng or eng with ENG (it appears in some award ids)
    s = re.sub('-[Ee]ng\.?-?','-ENG-',s)
    
    # Remove all the words with only upper cases at the beginning of the sentence
    #  (in most, if not all, of the cases they are titles)
    s = re.sub(r'^(0?[1-9][\s\.]{1,3})?\b[A-Z&\s-]+\b', '', s)
    # Remove the punctuation
#     s = s.translate(str.maketrans('','',punctuation))
    s = removePunctuation(s, f'-&#/{stops}')
    # Transforme & in "and" if there are spaces on both sizes
    #  and than transform & in a comma and a space if it is not surrounded by 
    #  uppercases only (as in acronymes)
    s = s.replace(' & ',' and ')
    s = re.sub(f'(?![\s\(][A-Z]+)&(?![A-Z]+[\s\){stops}])',', ',s)
    # Replace AAA/BBB with AAA-BBB and than 
    #  replace / with a comma and a blank space
    ##s = re.sub('(^[A-Z]+)/([A-Z]+$)',lambda w: w.group(1) + '-' + w.group(2),s)
    s = re.sub(r'(\b[A-Z]+)/([A-Z]+\b)',lambda w: w.group(1) + ' ' + w.group(2),s)
    ###s = s.replace('/',', ')
    # Replace # with a blank space
    s = s.replace('#',' ')
    # Replace "AA1111, 2222 and 3333" with "AA+1111, AA+2222 and AA+3333"
    s = award_ids_modifier(s)
    # Tokenise
    tokens = tokenizer.tokenize(s)
    # Remove words with only letters and, eventually, a dash
    # (we are looking for things with numbers and, eventually, capital letters)
    # s = [re.sub('^[A-Z]?[a-z]*[-]?[A-Z]?[a-z]$','',w) for w in tokens]
    s = re.sub(r'\b[A-Z]?[a-z]+(-[A-Z]?[a-z]+)?\b','',s)
    s = tokenizer.tokenize(s)
    # Remove the word 'U.S.'
    s = list(filter(('U.S.').__ne__, s))
    # Remove words with only one letter that is not a number
    s = [w for w in s if ((len(w)>2 and w[-1:] in stops) or 
                          len(w)>1 or 
                          w.isnumeric())]
    # Remove the words that are contained in the acronyms list
    s = [w for w in s if not isAcronym(w, acronyms)]
    # Preserve only words (one among these cases)
    #  - that are shorter than 3 characters with only uppercases
    #  - that contain at least one number
    #  - whose basic form (see above) is not in the English dictionary
    s = [w for w in s if includeWord(w)]
    # Look at the word immediately before or after the one identified as 
    #  potential award ids and, if it's not an acronym, add it to the potential
    #  award ids with a '+' in between (look at the addIsolated function 
    #  for further details)
    s_add = []
    idxs = []
    for ws in set(s):
        idxs.extend(idx for idx, elm in enumerate(tokens) if elm==ws)
    for idx in idxs:
        w = addIsolated(tokens, idx, s, 
                        acronyms, stops=stops, forward=False)
        if isinstance(w, list):
            for w_ in w:
                s_add.append(w_)
        else:
            #s = [w]
            s_add.append(w)
    for idx in idxs:
        w = addIsolated(tokens, idx, s,
                        acronyms, stops=stops, forward=True)
        if isinstance(w, list):
            for w_ in w:
                s_add.append(w_)
        else:
            #s = [w]
            s_add.append(w)
#     s = set(s_add.copy())
    s = set(s + s_add.copy())
    s = [w.translate(str.maketrans('','',stops)) for w in s]
    # Remove any potential award id shorter than 4 char. and 
    #  that doesn't contain numbers
    s = [w for w in s if (len(removePunctuation(w))>4 and 
                          any(c.isdigit() for c in w))]
    # Add a "flag", if any of the potential award ids is a potential year 
    #  (i.e., essentially a 19 or 20 followed by other 2 digits; 
    #  for further details look at the isYear function) 
    iy = any([isYear(w, current_year) for w in s])
    # Remove the award ids contained in other (longer) award ids
    s.sort(key=len)
    for i,w in enumerate(s[:]):
        if any(w in o for o in s[i+1:]):
            s.remove(w)
    # Join the potential award ids detected in a string separated by "|"
    if len(s)==0:
        s = ['']
    else:
        s = removeShorter(s)
    s = '|'.join(s)
    
    return pd.Series({
        'award_id': s,
        'public_law_statement': pl,
        'awarding_agency_acronymes': ags,
        'potential_year':iy})

# import multiprocessing as mp
# def award_id_extractor_df(df, n_cores = mp.cpu_count()-1):
#     import numpy as np
#     import pandas as pd
#     from tqdm import tqdm
    
#     ipts = award_id_extractor_preprocessor(df, n_cores)
    
#     tqdm.pandas()
#     if n_cores==1:
#         # TODO
#         # This function works only with these specific column names. 
#         #  It has to be generalized!
#         if 'grant_year' in df.columns:
#             award_ids = df.progress_apply(lambda row: award_id_extractor(
#                 row.gi_statement,
#                 ipts, 
#                 row.grant_year), 
#                 axis=1, result_type='reduce')
#         else:
#             award_ids = df.progress_apply(lambda row: award_id_extractor(
#                 row.gi_statement,
#                 ipts),
#                 axis=1, result_type='reduce')
#         award_ids = pd.DataFrame(award_ids.tolist())
#         ###patent_id = df.patent_id
#         #df_out = df.copy()
#         ##df_out['award_id'] = award_ids
#         ###df_out = pd.DataFrame(df_out)
#         #df_out = pd.concat([df_out,award_ids], axis=1)
#         #df_out.loc[df_out.award_id=='','award_id'] = np.nan
#         #df_out.reset_index(inplace=True, drop=True)
#         #return df_out
#         award_ids.loc[award_ids.award_id=='','award_id'] = np.nan
#         return award_ids
#     else:
#         import multiprocessing as mp
#         from pathos.multiprocessing import ProcessingPool as Pool
#         from functools import partial
#         #from multiprocessing import Pool#, freeze_support
#         #from itertools import repeat
#         import sys
        
#         # The dataframe is too long and exceded the recursion limits
#         #  This fixes the issue
#         try:
#             sys.setrecursionlimit(round(len(df)/n_cores)*2)
#         except:
#             pass
        
#         df_split = np.array_split(df, n_cores)
#         with Pool(n_cores) as pool:
#             #df_out = pool.map(award_id_extractor_df, df_split, 1)
#             df_out = pool.map(partial(award_id_extractor_df, n_cores=1), df_split)
#         df_out = pd.concat(df_out, ignore_index=True)
#         return df_out

def explode_award_ids(df, lst_cols, sep='|', fill_value='', preserve_index=False):
    import numpy as np
    import pandas as pd
    
    # make sure `lst_cols` is list-alike
    if (lst_cols is not None
        and len(lst_cols) > 0
        and not isinstance(lst_cols, (list, tuple, np.ndarray, pd.Series))):
        lst_cols = [lst_cols]
    
    df.loc[:, lst_cols] = df.loc[:, lst_cols].applymap(lambda el: el.split(sep))
    
    # all columns except `lst_cols`
    idx_cols = df.columns.difference(lst_cols)
    
    # calculate lengths of lists
    lens = df[lst_cols[0]].str.len()
    
    # preserve original index values
    idx = np.repeat(df.index.values, lens)
    
    # create \"exploded\" DF
    res = (pd.DataFrame({
                col:np.repeat(df[col].values, lens)
                for col in idx_cols},
                index=idx)
             .assign(**{col:np.concatenate(df.loc[lens>0, col].values)
                            for col in lst_cols}))
    
    # append those rows that have empty lists
    if (lens == 0).any():
        # at least one list in cells is empty
        res = (res.append(df.loc[lens==0, idx_cols], sort=False)
                  .fillna(fill_value))
    
    # revert the original index order
    res = res.sort_index()
    
    # reset index if requested
    if not preserve_index:
        res = res.reset_index(drop=True)
    
    return res
