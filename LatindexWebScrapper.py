import requests
import json
import csv
import html
import urllib.parse

def letUserPick(_nombreOpcion, _opciones):
    print(f'Elija un {_nombreOpcion}')
    for idx, element in enumerate(_opciones):
        print("{}) {}".format(idx+1,element))
    i = int(input("Enter number: "))
    if 0 < i <= len(_opciones):
        print(f'{_nombreOpcion}: {_opciones[i-1]}')
        return(_opciones[i-1])
    else:
        print('Elija un numero de la lista de opciones.')
        letUserPick(_nombreOpcion, _opciones)

def setupPayload(_subtema, _pais):
    subtemas = { 'Literatura': 6.12, 'Lingüistica': 6.11 }
    return f'buscar=nivel_tema%3A{subtemas[_subtema]}+AND+nombre_largo%3A%22{urllib.parse.quote(_pais)}%22+AND+situacion%3AC&inicio=0&rows=10000'

def getSearchPost(_subtema, _pais):
    url = 'https://www.latindex.org/latindex/bAvanzada/rslt'
    headers = { 'content-type' : 'application/x-www-form-urlencoded' }
    return requests.post(url, data=setupPayload(_subtema, _pais), headers=headers)

def downloadCSV(_folio):
    payload = f'folio={_folio}'
    headers = {'content-type' : 'application/x-www-form-urlencoded'}
    return requests.post('https://www.latindex.org/latindex/extraccionFicha', data=payload, headers=headers)

def setupFilename(_pais, _subtema):
    return f'revistas_{_pais.replace(" ","_")}_{_subtema}.csv'

def writeFinalCSV(_filename, _dictList):
    f = open(_filename, "w")
    writer = csv.DictWriter(f, fieldnames=set().union(*(d.keys() for d in _dictList)), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(_dictList)
    f.close()
    print(f'Se escribió correctamente el archivo: {_filename}')

opcionesPaises = ['Antigua y Barbuda','Argentina','Bahamas','Barbados','Belice','Bolivia','Brasil','Chile','Colombia','Costa Rica','Cuba','Ecuador','El Salvador','España','Guatemala','Guyana','Haití','Honduras','Islas Vírgenes de los Estados Unidos','Jamaica','Martinica','México','Nicaragua','Organismos Internacionales','Panamá','Paraguay','Perú','Portugal','Puerto Rico','República Dominicana','Trinidad y Tobago','Uruguay','Venezuela'];
opcionesSubtemas = ['Literatura', 'Lingüistica']
# Obtenemos parámetros de entrada
pais = letUserPick('país', opcionesPaises)
subtema = letUserPick('subtema', opcionesSubtemas)

# Búsqueda en latindex
try:
    response = getSearchPost(subtema, pais)
    response.raise_for_status()
except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
else:
    print('Lista de revistas obtenida!')

# Parsear resultado de busqueda
revistas = (json.loads(('{"lista": '+response.text+'}').replace(",,",",").replace(",]", "]")))
print(f'Se obtuvieron {len(revistas["lista"])} revistas')

i = 0
dictList = []
for revista in revistas['lista']:
    # Descargar csv de una revista
    try:
        download = downloadCSV(revista["folio"])
        download.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        print(f'{i} -> Obtenido folio {revista["folio"]}')
    with open('tmp.csv', 'wb') as tmp:
        tmp.write(download.content.decode('latin1').encode('utf-8'))
        tmp.close()
        reader = csv.reader(open('tmp.csv', 'r'))
        d = {}
        # Generamos un dict con los datos del csv
        for row in reader:
            if len(row) > 1:
                head, tail = row[0], row[1:]
                # Es el momento de unescape y unir posibles valorse con clave repetida
                if head not in d.keys():
                    d[head] = html.unescape(', '.join(tail))
                else:
                    d[head] += html.unescape("; "+', '.join(tail))
    # Agregamos el dict a dictList
    dictList.append(d)
    print(f'{i+1} -> Escrito folio {revista["folio"]}')
    i += 1

# Escribimos en un archivo todos los datos
filename = setupFilename(pais, subtema)
writeFinalCSV(filename, dictList)

# curl -d "folio=7581" -X POST https://www.latindex.org/latindex/extraccionFicha

# curl -d "buscar=nivel_tema%3A6.11+AND+nombre_largo%3A%22Chile%22+AND+situacion%3AC&inicio=0&rows=100000" -H "Content-type: application/x-www-form-urlencoded;" -X POST https://www.latindex.org/latindex/bAvanzada/rslt
