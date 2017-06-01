import argparse
import json
import urllib.request
import csv, sqlite3
import codecs
from operator import itemgetter
import time
import math

# Функция получения дистанции до объекта пешком (максимум 3 точки - больше не надо т.к. цель найти ближайшие)
# На вход подается delta - расстояние до объекта, рассчитанное геометрически
# origin - начальная точка и destinations - список финальных точкек маршрута
# Возвращает список объектов [индекс в массиве входных данных, дистанция до объекта пешком]
def getDistanceByDelta(delta, origin, destinations):
    distances = []
    i = 0 # итератор числа выходных данных
    for index, d in delta:
        request_count = 0 # счетчик числа попыток
        while request_count < 3: # 3 попытки на получение данных, чтобы не запрашивать вечно.
            # Если будет прерывание, то на разбор пойдёт фигня
            # На 10-й запрос идёт отказ, поэтому проверяются только 3 ближайших
            # Идёт запрос в гугл, приходит json-форматированнный ответ c данными
            link = "https://maps.google.com/maps/api/directions/json?origin=" + origin + "&destination=" + destinations[
                index-1][1]+","+ destinations[index-1][2] + "&mode=walking&sensor=false&key=AIzaSyDTLDpnBXSVZEhBjJQBw1YwJJ2TRmIOn0Y"
            response = urllib.request.urlopen(link)
            string_json = response.read().decode('utf-8')
            data = json.loads(string_json)
            if (data['status'] == 'OK'):    # Если ОК, то выходим, иначе перезапрашиваемещё ещё раз
                print(data)
                break
            #time.sleep(2) # 2 секунды ждем
            request_count+=1
        # Разбор json подготовка выходного списка
        # TODO разбор не учитывает прерывание по числу попыток получения данных в гугл
        # TODO for item, value in data['routes'][0]['legs'][0]['distance'].items(): IndexError: list index out of range
        if data['status'] == 'OK':
            for item, value in data['routes'][0]['legs'][0]['distance'].items():
                if item == 'value': distances.append([index, value])
            i += 1
            if i > 2:
                break
        print(data)
    return distances

API_KEY = 'AIzaSyDTLDpnBXSVZEhBjJQBw1YwJJ2TRmIOn0Y'
DirApiKey = 'AIzaSyA8RrWPKPUNaDdTNWglooCKr7FiI2mYON0'
DistMatrixApiKey = 'AIzaSyAhd_HPKuSjlRRez04onPxERCy47GUEYDI'

import geopy
import geopy.distance

def getGeoPyCoord(coordinate, coordinate_list):
    pts = [ geopy.Point(p[0],p[1]) for p in coordinate_list ]
    onept = geopy.Point(coordinate[0],coordinate[1])
    alldist = [ (p,geopy.distance.distance(p, onept).km) for p in pts ]
    nearest_point = min(alldist, key=lambda x: (x[1]))[0] # or you can sort in by distance with sorted function
    return nearest_point[0], nearest_point[1]


def getDistance(origin, coordinate, csvf, sqlitef):
    originX = origin[:origin.index(',')]    # Разрезание координат на X и Y составляющие
    originY = origin[origin.index(',')+1:]
    destinations = []
    row_counter = 0
    print('read')
    if coordinate:  # Если указана одна координата
        coordinateX = coordinate[:coordinate.index(',')]
        coordinateY = coordinate[coordinate.index(',')+1:]
        destinations.append([row_counter, coordinateX, coordinateY])
    elif csvf: # Если указан файл csv
        print("csv")
        with codecs.open(csvf, encoding='utf-8') as csvfile:
             reader = csv.reader(csvfile, delimiter=',', quotechar='"')
             for row in reader:
                if row_counter > 0:
                    coordinateX = row[2][:row[2].index(',')]
                    coordinateY = row[2][row[2].index(',') + 1:]
                    destinations.append([row_counter, coordinateX, coordinateY])
                row_counter+=1
    elif sqlitef: # Если указан файл БД
        print("Поддержка sqlite не реализована")
    else :  # Если нет хотя бы одного необходимого параметра - прерывание
        print("Не указан ни один из необходимых параметров!")
        exit(-1)
    print('calc')
    distances = []
    # Геометрическое рассояние между точками
    delta = []
    for index, destinationX, destinationY in destinations :
        d = math.sqrt((float(destinationX) - float(originX))**2+(float(destinationY) - float(originY))**2)
        delta.append([index, d])
    delta.sort(key=itemgetter(1))  # Сортировка для упорядочивания по геометрической удалённости
    print('Near Points',delta[0],delta[1],delta[2])
    distances = getDistanceByDelta(delta, origin, destinations)

    if coordinate:
        return(["raw", distances])
    elif csv:
        return(["csv", distances])
    elif sqlitef:
        return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--origin", required=True, help="Ваша коодината")
    ap.add_argument("-d", "--destination", required=False, help="Места назначения (координаты)")
    ap.add_argument("-c", "--csv", required=False, help="Файл БД в формате CSV")
    ap.add_argument("-s", "--sqlite", required=False, help="Файл БД в формате SQLite3")

    # example coord:    --origin "59.931882,30.361689" --destination "59.933607,30.362837"
    # example csv:      -o "59.931882,30.361689" -c "dest.csv"
    # example sql:      -o "59.931882,30.361689" -s "dest.db"
    args = vars(ap.parse_args())

    origin = args["origin"]
    coordinate = args["destination"]
    csvf = args["csv"]
    sqlitef = args["sqlite"]

    getDistance(origin, coordinate, csvf, sqlitef)