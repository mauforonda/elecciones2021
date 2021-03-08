#!/usr/bin/env python3

import requests
import pandas as pd
from pandas.errors import EmptyDataError
import csv
import os

def download(departamento):

    headers = {
        'authority': 'computo.oep.org.bo',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'application/json, text/plain, */*',
        'dnt': '1',
        'captcha': 'nocaptcha',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/json',
        'origin': 'https://computo.oep.org.bo',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://computo.oep.org.bo/',
        'accept-language': 'en-US,en;q=0.9,es;q=0.8',
    }

    dep_id = departamento['id']

    data = f'{{"tipoArchivo":"CSV", "idDepartamento":{dep_id}}}'

    meta = requests.post('https://computo.oep.org.bo/api/v1/descargar', headers=headers, data=data)
    response = requests.get(meta.json()['datoAdicional']['archivo'])
    csvdata = csv.reader(response.content.decode('iso8859').splitlines(), delimiter=',')
    if csvdata.line_num > 0:
        filename = 'datos/{}/{}.csv'.format(departamento['nombre'], '_'.join(meta.json()['datoAdicional']['archivo'].split('/')[-1].split('_')[1:4]))
        data = [row for row in csvdata]
        df = pd.DataFrame(data[1:], columns=data[0])
        if not os.path.exists('datos'):
            os.makedirs('datos')
        if not os.path.exists('datos/{}'.format(departamento['nombre'])):
            os.makedirs('datos/{}'.format(departamento['nombre']))
        df.to_csv(filename, index=False, encoding='utf-8')

departamentos = [
    {'nombre':'chuquisaca', 'id':1},
    {'nombre':'la_paz', 'id':2},
    {'nombre':'cochabamba', 'id':3},
    {'nombre':'oruro', 'id':4},
    {'nombre':'potosi', 'id':5},
    {'nombre':'tarija', 'id':6},
    {'nombre':'santa_cruz', 'id':7},
    {'nombre':'beni', 'id':8},
    {'nombre':'pando', 'id':9}
]
for departamento in departamentos:
    download(departamento)