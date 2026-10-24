insert into public.stocks (ticker, name, sector) values
    ('BMY',  'Bristol-Myers Squibb Company',        'pharmaceuticals'),
    ('NVO',  'Novo Nordisk A/S',                    'pharmaceuticals'),
    ('AZN',  'AstraZeneca PLC',                     'pharmaceuticals'),
    ('NVS',  'Novartis AG',                         'pharmaceuticals'),
    ('GILD', 'Gilead Sciences, Inc.',               'pharmaceuticals'),
    ('REGN', 'Regeneron Pharmaceuticals, Inc.',     'pharmaceuticals'),
    ('VRTX', 'Vertex Pharmaceuticals Incorporated', 'pharmaceuticals'),
    ('SNY',  'Sanofi',                              'pharmaceuticals')
on conflict (ticker) do update
    set name       = excluded.name,
        sector     = excluded.sector,
        is_active  = true,
        updated_at = now();