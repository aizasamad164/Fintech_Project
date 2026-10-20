-- =====================================================================
-- 0003_seed_stocks.sql
--
-- Seeds the candidate stock universe (Technology, Healthcare, Renewable
-- Energy). The ingest endpoint and scripts/ingest_all.py both refuse to
-- load a ticker that is not in public.stocks, so this must run first.
--
-- Safe to run more than once: existing tickers are updated, not duplicated.
-- To add a stock later, add one row here (or insert it in the SQL editor).
-- =====================================================================

insert into public.stocks (ticker, name, sector) values
    -- Technology
    ('AAPL',  'Apple Inc.',                      'technology'),
    ('MSFT',  'Microsoft Corporation',           'technology'),
    ('NVDA',  'NVIDIA Corporation',              'technology'),
    ('GOOGL', 'Alphabet Inc. (Class A)',         'technology'),
    ('AVGO',  'Broadcom Inc.',                   'technology'),
    ('ORCL',  'Oracle Corporation',              'technology'),
    ('ADBE',  'Adobe Inc.',                      'technology'),
    ('CRM',   'Salesforce, Inc.',                'technology'),
    ('AMD',   'Advanced Micro Devices, Inc.',    'technology'),
    ('CSCO',  'Cisco Systems, Inc.',             'technology'),
    -- Healthcare
    ('JNJ',   'Johnson & Johnson',               'healthcare'),
    ('UNH',   'UnitedHealth Group Incorporated', 'healthcare'),
    ('LLY',   'Eli Lilly and Company',           'healthcare'),
    ('PFE',   'Pfizer Inc.',                     'healthcare'),
    ('ABBV',  'AbbVie Inc.',                     'healthcare'),
    ('MRK',   'Merck & Co., Inc.',               'healthcare'),
    ('TMO',   'Thermo Fisher Scientific Inc.',   'healthcare'),
    ('ABT',   'Abbott Laboratories',             'healthcare'),
    ('AMGN',  'Amgen Inc.',                      'healthcare'),
    ('ISRG',  'Intuitive Surgical, Inc.',        'healthcare'),
    -- Renewable Energy
    ('NEE',   'NextEra Energy, Inc.',            'renewable_energy'),
    ('ENPH',  'Enphase Energy, Inc.',            'renewable_energy'),
    ('FSLR',  'First Solar, Inc.',               'renewable_energy'),
    ('SEDG',  'SolarEdge Technologies, Inc.',    'renewable_energy'),
    ('RUN',   'Sunrun Inc.',                     'renewable_energy'),
    ('BEP',   'Brookfield Renewable Partners',   'renewable_energy'),
    ('CWEN',  'Clearway Energy, Inc.',           'renewable_energy'),
    ('ORA',   'Ormat Technologies, Inc.',        'renewable_energy')
on conflict (ticker) do update
    set name      = excluded.name,
        sector    = excluded.sector,
        is_active = true,
        updated_at = now();
