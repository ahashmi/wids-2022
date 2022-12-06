from dataclasses import replace
from operator import index
from os import rename
from config import paths, config_log
import logging
import pandas as pd
import json


data_files = {
    'epa': paths['data'] / 'epa' / 'epa_aq_data.csv',
    'cdc': paths['data'] / 'places' / 'cdc_outcomes_data.csv',
}

skip_states = ['AS', 'FM', 'GU', 'MH', 'MP', 'PR', 'PW', 'VI']

cdc_fixes = {
    'NM': {
        'to_replace': 'DoÃ±a Ana', 'value': 'Dona Ana'
        },
}

cdc_drop = [
    'STATE', 'ABBR', 'COUNTY', 'CountyFIPS', 'Geolocation'
]

replacements = [
    {'old': 'Charles', 'new': 'Charles City'},
    {'old': 'Saint', 'new': 'St.'},
]

class State:

    def __init__(self, abbr:str, name:str, epa_df:pd.DataFrame, cdc_df:pd.DataFrame, prnt_logger:logging.Logger) -> None:
        self.abbr = abbr
        self.name = name
        self.epa_df = epa_df
        self.epa_n = self.epa_df.shape[0]
        self.cdc_df = cdc_df
        self.cdc_n = self.cdc_df.shape[0]
        self.logger = prnt_logger
        if self.epa_n + self.cdc_n:
            self.logger.info(f'[STATE] {self.abbr} data - epa: {self.epa_n} rows, cdc: {self.cdc_n} rows')
        else:
            self.logger.warning(f'[STATE] {self.abbr}, no data loaded!')
        ## fix CDC counties
        if self.abbr in cdc_fixes.keys():
            self.cdc_df.replace(**cdc_fixes[self.abbr], inplace=True)

    @staticmethod
    def rename_cols(src_df:pd.DataFrame()) -> None:
        new_cols = ['year']
        for col_nm in src_df.columns:
            if col_nm != 'year':
                new_cols.append(col_nm.split('_')[0])
        src_df.columns = new_cols

    def get_outcomes(self, in_df:pd.DataFrame) -> dict:
        outcomes = {}
        otcm_df = in_df.drop(cdc_drop, axis=1)
        self.rename_cols(otcm_df)
        for yr in pd.unique(otcm_df['year']):
            yr_df = otcm_df[otcm_df['year'] == yr].drop('year', axis=1)
            outcomes[yr] = yr_df.to_dict(orient='records')
        return outcomes
    
    def analyze(self):
        sites = self.epa_df[['AQS_ID', 'COUNTY']].drop_duplicates().to_dict(orient='records')
        self.counties = {}
        unmatched = []
        for site_obj in sites:
            county = site_obj['COUNTY'].strip()
            for replacement in replacements:
                county = county.replace(replacement['old'], replacement['new'])
            if county not in self.counties.keys():
                county_df = self.cdc_df[self.cdc_df['COUNTY'] == county]
                county_fips = county_df['CountyFIPS'].drop_duplicates()
                if county_fips.empty:
                    fips_code = None
                    unmatched.append(county)
                else:
                    fips_code = county_fips.iloc[0]
                self.counties[county] = {
                    'fips': fips_code,
                    'outcomes': self.get_outcomes(county_df),
                    'sites': [],
                }
            self.counties[county]['sites'].append(site_obj['AQS_ID'])
        self.logger.debug(f'[analyze] {self.abbr} counties matched: {len(self.counties)}')
        if len(unmatched):
            self.logger.warning(f'[analyze] {self.abbr} unmatched: {unmatched}')

    def publish(self):
        content_file = paths['docs'] / 'states' / f'{self.abbr}.md'
        content_lines = [
            '---',
            'layout: state',
            f'title: {self.name}',
            f'abbr: {self.abbr}',
            '---',
        ]
        with open(content_file, 'w') as md_out:
            md_out.write('\n'.join(content_lines))
        data_file = paths['site_data'] / 'states' / f'{self.abbr}.json'
        data = {
            'specs': {},
            'counties': self.counties,
        }
        for attr in ['epa_n', 'cdc_n']:
            data['specs'][attr] = getattr(self, attr)
        with open(data_file, 'w') as js_out:
            json.dump(data, js_out, indent=4)

def load_data(func_logger:logging.Logger) -> dict:
    dfs = {}
    for dtype, dfile in data_files.items():
        dfs[dtype] = pd.read_csv(dfile, dtype={'CountyFIPS': 'str', 'year': 'str'})
        n_rows, n_cols = dfs[dtype].shape
        func_logger.info(f'[load_data] loaded {dtype.upper()} data: {n_rows} rows')
        func_logger.debug(f'[load_data] columns ({n_cols}): {dfs[dtype].columns}')
        func_logger.debug(f"[load_data] years: {pd.unique(dfs[dtype]['year'])}")
    return dfs

def parse_states(func_logger:logging.Logger) -> None:
    states_file = paths['ref'] / 'states.json'
    datasets = load_data(func_logger=func_logger)
    with open(states_file, 'r') as js_in:
        states = json.load(js_in)
        for st_abbr, st_name in states.items():
            if st_abbr not in skip_states:
                state_data = {
                    'abbr': st_abbr,
                    'name': st_name,
                }
                for dtype, df in datasets.items():
                    state_data[f'{dtype}_df'] = df[df['STATE'] == st_name].copy()
                crnt_state = State(**state_data, prnt_logger=func_logger)
                crnt_state.analyze()
                crnt_state.publish()


if __name__ == '__main__':
    config_log('parse')
    logger = logging.getLogger('parse')
    parse_states(func_logger=logger)