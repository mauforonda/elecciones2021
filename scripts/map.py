#!/usr/bin/env python3

import pandas as pd
import os
import folium
from folium import plugins
import math
from datetime import datetime
from matplotlib import colors, cm
import numpy as np

vote_cols = []
partidos = []
validos = 'VOTO_VALIDO'
min_votes_p = .01

ubicaciones = pd.read_csv('scripts/recintos.csv', index_col='id')
last_files = ['datos/{}/{}'.format(dep, sorted(os.listdir('datos/'+dep))[-1]) for dep in os.listdir('datos') if len(os.listdir('datos/'+dep)) > 0]
last_update = sorted([datetime.strptime('_'.join(sorted(os.listdir('datos/'+dep))[-1].split('_')[1:]), '%Y%m%d_%H%M%S.csv') for dep in os.listdir('datos') if len(os.listdir('datos/'+dep)) > 0])[-1]
votacion = pd.concat([pd.read_csv(f) for f in last_files], axis=0)

def scale(x, victoria_mas=.5):
    if x <= victoria_mas:
        return x/victoria_mas
    else:
        return 1.0

def tooltip(row, partidos):
    return '<div style="min-width:220px"><p style="margin:5px 0px; font-size: 1.4em; text-align:center; font-weight: bold">{}</p>'.format(row['recinto']) + '<p style="margin:5px 0px; font-size: 0.95em; text-align:center; color: #7b7b7b;">{}</p>'.format(row['municipio']) + '<p style="margin:5px 0px; font-size: 0.95em; text-align:center; color: #7b7b7b;">{}/{} mesas contadas</p>'.format(int(row['mesas_votadas']), row['n_mesas']) + '<p style="margin:5px 0px; font-size: 0.95em; text-align:center; color: #7b7b7b;">{} votos válidos</p><hr style="margin-top:10px; margin-bottom:10px">'.format(row[validos]) + ''.join(['<p style="margin:5px 0px"><span style="width: 50%;text-align: right;display: inline-block;"><strong>{}</strong> : </span><span> {:.2%}</p></span>'.format(partido, row['{}_p'.format(partido)]) for partido in partidos if row['{}_p'.format(partido)] > min_votes_p]) + '</div>'

def fix_maps(map_filename):
    with open(map_filename, 'r+') as f:
        html = f.read()
        html = html.replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet-locatecontrol/0.66.2/L.Control.Locate.min.js', 'https://cdn.jsdelivr.net/npm/leaflet.locatecontrol@0.72.0/dist/L.Control.Locate.min.js')
        html = html.replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet-locatecontrol/0.66.2/L.Control.Locate.min.css', 'https://cdn.jsdelivr.net/npm/leaflet.locatecontrol@0.72.0/dist/L.Control.Locate.min.css')
        html = html.replace('<style>#map {position:absolute;top:0;bottom:0;right:0;left:0;}</style>', '<style>#map {position:absolute;top:0;bottom:0;right:0;left:0;} .leaflet-interactive[fill="#a1a1a1"]{cursor: grab !important;}</style>')
        f.seek(0)
        f.write(html)
        f.truncate()

def draw_map(candidatura, map_name):

    locations = ubicaciones.copy()
    votos = votacion.copy()

    votos.insert(0, 'id', (votos.CODIGO_LOCALIDAD.astype(str) + votos.CODIGO_RECINTO.astype(str)).astype(int))
    votos = votos[votos.DESCRIPCION == candidatura]

    vote_cols = votos.columns[16:]
    partidos = [col for col in votos[votos.columns[17:]] if col not in ['VOTO_VALIDO', 'VOTO_BLANCO', 'VOTO_NULO', 'VOTO_EMITIDO', 'VOTO_VALIDO_SISTEMA','VOTO_EMITIDO_SISTEMA']]
    
    votos = pd.concat([votos.groupby('id')[vote_cols].sum(), pd.DataFrame(votos.groupby('id')[validos].count()).rename(columns={validos:'mesas_votadas'})], axis=1)
    df = pd.concat([locations, votos], axis=1)
    pendiente = df[df[validos].isna()]
    df = df.dropna()

    # cmap = colors.ListedColormap(cm.get_cmap('gist_rainbow_r')(np.linspace(0,.25,256)))
    cmap = colors.LinearSegmentedColormap.from_list('mas', ['#ff8546', '#3e4bf8'], N=256)

    df[validos] = df[validos].astype(int)
    df = df[df[validos] > 0]
    for partido in partidos:
        df['{}_p'.format(partido)] = df[partido] / df[validos]
    df['size'] = df[validos].apply(lambda row: math.log(row) if row > 0 else 1)
    df['color'] = df['MAS-IPSP_p'].apply(lambda mas: colors.rgb2hex(cmap(scale(mas))[:3]))
    df['recinto'] = df['recinto'].str.replace('`','')

    pendiente['size'] = pendiente['habilitados'].apply(lambda row: math.log(row) if row > 0 else 1)

    folium_map = folium.Map(location = [-16.4340009,-65.2686204],
                            zoom_start = 6,
                            tiles = "https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png",
                            attr = '<a href="https://www.openstreetmap.org/copyright">OSM</a> | Datos de cómputo del {}'.format(last_update.strftime('%Y/%m/%d a las %H:%M')))


    for row in pendiente.to_dict(orient='records'):
        folium.CircleMarker(location=[row['y'], row['x']],
                            stroke = False,
                            fill_opacity = .2,
                            radius = row['size'],
                            interactive = False,
                            className = 'pendiente',
                            fill_color='#a1a1a1').add_to(folium_map)

    for row in df.to_dict(orient='records'):
        folium.CircleMarker(location=[row['y'], row['x']],
                            stroke = False,
                            fill_opacity = .8,
                            radius = row['size'],
                            popup = tooltip(row, partidos),
                            fill_color=row['color']).add_to(folium_map)


    plugins.LocateControl(drawCircle=False,
                      drawMarker=False,
                      setView='once',
                      initialZoomLevel = 17,
                      strings = {
                          'title': 'Ir a mi ubicación',
                          'popup': "Estás a {distance} metros de este punto"
                      },).add_to(folium_map)
                      
    plugins.FloatImage('./leyenda_{}.png'.format(map_name), bottom=5, left=5).add_to(folium_map)
    folium_map.save('docs/{}.html'.format(map_name))
    fix_maps('docs/{}.html'.format(map_name))


draw_map('ALCALDESA/ALCALDE', 'alcaldias')
draw_map('GOBERNADOR(A)', 'gobernaciones')
