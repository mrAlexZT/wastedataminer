# -*- coding: utf-8 -*-
from datetime import datetime, date

import flask
from flask import Flask, request
from flask_restful import Resource, Api
from flask_restful import reqparse
import werkzeug
import time
import uuid
import codecs
import csv
import logging
from map_utils import getDistance
from map_utils import getGeoPyCoord
import os
import numpy as np
import tensorflow as tf
from transliterate import translit
import json

import CONFIG

app = Flask(__name__)
api = Api(app)

logger = logging.getLogger('Server')
ch = logging.StreamHandler()
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

# CONFIG includes:
# _VERSION_ = "v0.2.2"
# _FOLDER_4_LEARN_ = "files4learning"
# _FOLDER_4_RCGN_ = "files4recognition"
# _IMAGE_FULL_PATH_ = 'image.jpg'
# _MODEL_FULL_PATH_ = 'output_graph.pb'
# _LABELS_FULL_PATH_ = 'output_labels.txt'
# _LOG_FULL_PATH_ ="test_serv"+_VERSION_+"_req_times"
# _PLACE_WASTE_DB_ = "place-waste.csv"
# _WASTE_DB_ = "waste_db.csv"
# _THREADED_RUN_ = True

_VERSION_           = CONFIG._VERSION_
_FOLDER_4_LEARN_    = CONFIG._FOLDER_4_LEARN_
_FOLDER_4_RCGN_     = CONFIG._FOLDER_4_RCGN_
_IMAGE_FULL_PATH_   = CONFIG._IMAGE_FULL_PATH_
_MODEL_FULL_PATH_   = CONFIG._MODEL_FULL_PATH_
_LABELS_FULL_PATH_  = CONFIG._LABELS_FULL_PATH_
_LOG_FULL_PATH_     = CONFIG._LOG_FULL_PATH_
_PLACE_WASTE_DB_    = CONFIG._PLACE_WASTE_DB_
_WASTE_DB_          = CONFIG._WASTE_DB_
_THREADED_RUN_      = CONFIG._THREADED_RUN_


def create_graph():
    """Creates a graph from saved GraphDef file and returns a saver."""
    # Creates graph from saved graph_def.pb.
    with tf.gfile.FastGFile(_MODEL_FULL_PATH_, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')


def run_inference_on_image(_IMAGE_FULL_PATH_):
    logger.debug(">run_inference_on_image %s" % _IMAGE_FULL_PATH_)
    answer = None

    if not tf.gfile.Exists(_IMAGE_FULL_PATH_):
        logger.debug('>File does not exist %s', _IMAGE_FULL_PATH_)
        # tf.logging.fatal('File does not exist %s', imagePath)
        return answer

    image_data = tf.gfile.FastGFile(_IMAGE_FULL_PATH_, 'rb').read()

    # Creates graph from saved GraphDef.
    create_graph()

    with tf.Session() as sess:

        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
        predictions = np.squeeze(predictions)

        # top_k = predictions.argsort()[-5:][::-1]  # Getting top 5 predictions
        top_k = predictions.argsort()[::-1]              # Getting all predictions
        f = open(_LABELS_FULL_PATH_, 'r')
        lines = f.readlines()
        labels = [str(w).replace("\n", "") for w in lines]
        for node_id in top_k:
            human_string = str(labels[node_id])
            score = predictions[node_id]
            logger.debug('\t%s (score = %.5f)' % (human_string, score))

        answer = labels[top_k[0]]
        return answer, str(predictions[top_k[0]])


class NearWastePlace(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('class', type=str, help='Class of shared waste')
            parser.add_argument('latitude', type=str, help='Class of shared waste')
            parser.add_argument('longitude', type=str, help='Class of shared waste')
            args = parser.parse_args()
            _latitude = args['latitude']
            _longitude = args['longitude']

            print(_latitude)
            print(_longitude)

            with codecs.open(_PLACE_WASTE_DB_, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                i = 0
                db_place = []
                for row in reader:
                    if i > 0:
                        db_id = i
                        db_country = 'Россия'
                        db_city = row[0]
                        db_metro = row[1]
                        db_region_city = row[1]
                        db_latitude = row[2][:row[2].index(',')]
                        db_longitude = row[2][row[2].index(',') + 1:]
                        db_address = row[3]
                        db_schedule = row[4]
                        db_comment = 'Комментарий'
                        db_social = row[5]
                        db_place.append({
                            'id': db_id,
                            'country': db_country,
                            'city': db_city,
                            'metro': db_metro,
                            'region_city': db_region_city,
                            'latitude': db_latitude,
                            'longitude': db_longitude,
                            'address': db_address,
                            'schedule': db_schedule,
                            'comment': db_comment,
                            'social': db_social
                        })
                    i += 1
                    pass

            coords = []
            for place in db_place:
                coords.append((place['latitude'], place['longitude']))

            print('db_place')
            near_place = []
            other_place = coords

            near_place.append(getGeoPyCoord((_latitude, _longitude), coords))
            print(near_place)

            '''
            place_list = getDistance(origin=_latitude + "," + _longitude, coordinate=None, csvf=_PLACE_WASTE_DB_,
                                     sqlitef=None)
            print(place_list)

            near_place = []
            other_place = []
            id_list = []
            for rec in place_list[1]:
                id_list.append(rec[0])
                pass

            print(id_list)
            print("**1**")
            for rec in db_place:
                print(rec['id'])
                if rec['id'] in id_list:
                    print("---1")
                    for obj in place_list[1]:
                        print(obj)
                        if obj[0] == rec['id']:
                            dist = obj[1]
                    print(dist)
                    # print (place_list[1] [x for i in id_list if x == rec['id']])
                    print("---1-")
                    near_place.append({'place': rec, 'distance': dist})
                else:
                    print("---2")
                    other_place.append({'place': rec})
            print("4--")
            """
            placeitems: {
            country:
            city:
            metro:
            place:
            latitude:
            longitude:
            address:
            schedule:
            comment:
            social:
            }
            """
            '''
            print('result=%s' % near_place)
            return {'StatusCode': '200', 'Message': 'Operation successful', 'NearPlace': near_place,
                    'OtherPlace': other_place}
            pass
        except Exception as e:
            return {'error': str(e)}
            pass


class CollectionsPoint(Resource):
    def post(self):
        try:
            # Parse the arguments
            print("1")
            parser = reqparse.RequestParser()
            print("2")
            parser.add_argument('class', type=str, help='Class of shared waste')
            parser.add_argument('district', type=str, help='A district of the city')
            parser.add_argument('metro', type=str, help='Metro')
            args = parser.parse_args()

            _district = args['district']
            _metro = args['metro']

            result = []
            with codecs.open(_PLACE_WASTE_DB_, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                i = 0
                for row in reader:
                    if i > 0:
                        if ((_metro in row[1].split(',') or _district in row[1].split(',')) or
                                (_metro == "" and _district == "")):
                            db_id = i
                            db_country = 'Россия'
                            db_city = row[0]
                            db_metro = row[1]
                            db_region_city = row[1]
                            db_latitude = row[2][:row[2].index(',')]
                            db_longitude = row[2][row[2].index(',') + 1:]
                            db_address = row[3]
                            db_schedule = row[4]
                            db_comment = 'Комментарий'
                            db_social = row[5]
                            result.append({
                                'id': db_id,
                                'country': db_country,
                                'city': db_city,
                                'metro': db_metro,
                                'region_city': db_region_city,
                                'latitude': db_latitude,
                                'longitude': db_longitude,
                                'address': db_address,
                                'schedule': db_schedule,
                                'comment': db_comment,
                                'social': db_social
                            })
                    i += 1

            return {'StatusCode': '200', 'Message': 'Operation successful', 'Places': result}
        except Exception as e:
            return {'error': str(e)}


class UploadFile4Recognition(Resource):
    def put(self):
        try:
            logger.debug("\n>UploadFile4Recognition")
            req_income_datetime = datetime.now()
            # Parse the arguments
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str, help='user_id')
            parser.add_argument('filename', type=str, help='Class of shared waste')
            parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files',
                                help='Class of shared waste')
            args = parser.parse_args()
            logger.debug(">Income query with args: %s" % args)
            _userid = args['user_id']
            _file = args['file'].stream
            _filename = "garbage.jpg"
            request_id = uuid.uuid1().__str__()
            fn = "[{}]-[{}]-[{}]-{}".format(request_id, _userid, time.time(), _filename)
            # TODO Не работает, крашится на транслите и ничего не пишет
            # fn = "[{}]-[{}]-[{}]-{}".format(request_id, _userid, time.time(), translit(_filename, reversed=True))
            full_fn = _FOLDER_4_RCGN_ + os.sep + fn
            with open(full_fn, 'wb') as fout:
                fout.write(_file.getvalue())
            fout.close()

            score = "No score"
            result = 'Not classified'
            waste_id = 'No id'
            reason = ''
            resp = "CNN is not work correctly!"

            recognition_start_datetime = datetime.now()
            try:
                resp, score = run_inference_on_image(full_fn)
                # resp = bresp[2:-3]
                logger.debug(">Result: %s with %s" % (resp, score))
                os.rename(full_fn, str(_FOLDER_4_RCGN_ + os.sep + resp + "-" + fn))
            except Exception as e:
                print(e)
                reason = 'Exception: %s' % e

            recognition_complete_datetime = datetime.now()

            try:
                with codecs.open(_WASTE_DB_, encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                    for rec in reader:
                        if str(rec[0]).isdigit():
                            #  if str(rec[3]).lower() in resp.lower() or resp.lower() in str(rec[3]).lower():
                            if int(rec[0]) == int(resp):
                                result = rec[5]
                                waste_id = rec[0]
                                reason = ''
                                break
                            else:
                                reason = 'Not found info in %s for response=%s' % (_WASTE_DB_, resp)

            except Exception as e:
                print(e)
                reason = 'Exception: %s' % e
                # if 'disposable paper cups resize' in resp:
                #     result = "бумажный стаканчик"
                # if 'lame foil' in resp:
                #     result = "фольга мятая"
                # if 'glass bottle' in resp:
                #     result = "бутылка из-под напитков"
                # if 'plastic bottle' in resp:
                #     result = "прозрачный ПЭТ-контейнер"
                # if 'stupid' in resp:
                #     result = "неудалось определить класс отходов"
                # if 'receipt' in resp:
                #     result = "чековая лента"
                # if 'aluminium cup' in resp:
                #     result = "алюминиевая банка"
                # if 'plastic bag' in resp:
                #     result = "ПП мягкий цветной пластик"
                # if 'shreddered paper' in resp:
                #     result = "бумажные обрезки"
                # # result = result.encode('utf-8')
                logger.debug(">Result: %s with probability = %s" % (result, score))
                pass
            complete_datetime = datetime.now()
            # Prepare to write log
            req_times = ""
            logFullPath = _LOG_FULL_PATH_ + os.sep + \
                          "backend_" + _VERSION_[1:] + os.sep + \
                          str(date.today()) + os.sep + \
                          _userid
            print(logFullPath)
            if not os.path.exists(logFullPath):
                logger.debug(">New DIRs will be created")
                os.makedirs(logFullPath)
            req_times_filename = logFullPath + os.sep + "timings.csv"

            if not os.path.exists(req_times_filename):
                logger.debug(">New log file will be created")
                req_times = "sep=,"+os.linesep+"request_id," \
                                               "req_income_datetime," \
                                               "recognition_start_datetime," \
                                               "recognition_complete_datetime," \
                                               "complete_datetime," \
                                               "income_stage_duration," \
                                               "recognition_stage_duration," \
                                               "postrecognition_stage_duration," \
                                               "whole_duration," \
                                               "result"+os.linesep

            # Запись в лог для последующего анализа и отладки
            logger.debug(">Open log with name %s" % req_times_filename)
            f = open(req_times_filename, 'a+')
            req_times += (str(request_id) + "," +                                                   # Номер запроса
                          str(req_income_datetime) + "," +                                          # Дата вхождения
                          str(recognition_start_datetime) + "," +                                   # Дата начала определения
                          str(recognition_complete_datetime) + "," +                                # Дата окончания определения
                          str(complete_datetime) + "," +                                            # Дата завершения обработки запроса
                          str(recognition_start_datetime - req_income_datetime) + "," +             # Время прошедшее от вхождения до начала определения типа
                          str(recognition_complete_datetime - recognition_start_datetime) + "," +   # Время затраченное на определение типа
                          str(complete_datetime - recognition_complete_datetime) + "," +            # Время пост обработки (приведение типов)
                          str(complete_datetime - req_income_datetime) + "," +                      # Общее затраченное время на обработку
                          str(result))
            if f:
                f.write(req_times+""+os.linesep)
                f.flush()
                f.close()
            # Окончание записи в лог
            print('Reason for this image %s!' % reason)
            if waste_id == 'No id':
                result+=". "+reason
            return {'StatusCode': '200',
                    'Cnn_result': resp,
                    'Message': result,
                    'Score': score,
                    'Id': waste_id,
                    'Callback_id': request_id}
        except Exception as e:
            return {'error': str(e)}


# TODO Сомнительная фигня т.к. все классы выводить стрёмно, ибо из более 100
class GetList(Resource):
    def get(self):
        db_list = []
        # тут по идее должен быть файл новой базы - _WASTE_DB_ = "waste_db.csv"
        with codecs.open(_WASTE_DB_, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            i = 0
            for rec in reader:
                if i > 0:
                    db_list.append({'id': rec[0], 'detailed type eng': rec[3], 'detailed type ru': rec[5]})
                i += 1
        # return {'StatusCode': '200', 'Message': db_list}
        return flask.jsonify(db_list)


class GetTaskResult(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('task_id', required=True, type=str, help='user_id')
            args = parser.parse_args()
            _taskid = args['task_id']

            return {'StatusCode': '200', 'Message': _taskid}
        except Exception as e:
            return {'error': str(e)}


class UploadFile4Learn(Resource):
    def post(self):
        try:
            # Parse the arguments
            print("1")
            parser = reqparse.RequestParser()
            print("2")
            parser.add_argument('user_id',
                                type=str,
                                help='user_id')
            parser.add_argument('source',
                                type=str,
                                help='user_id')
            parser.add_argument('filename',
                                type=str,
                                help='filename')
            parser.add_argument('descr',
                                type=str,
                                help='descr')
            parser.add_argument('file',
                                type=werkzeug.datastructures.FileStorage,
                                location='files',
                                help='Class of shared waste')
            args = parser.parse_args()
            print(args)
            _userid = args['user_id']
            _source = args['source']
            _filename = args['filename']
            _file = args['file'].stream

            print(args)

            # check exists folder for storage file

            if not os.path.exists(_FOLDER_4_LEARN_):
                os.makedirs(_FOLDER_4_LEARN_)

            if _source == 'bot':
                filename = _FOLDER_4_LEARN_ + os.sep + _filename
            else:
                _filename = "garbage.jpg"
                request_id = uuid.uuid1().__str__()
                fn = "[{}]-[{}]-[{}]-{}".format(request_id, _userid, time.time(), _filename)
                # TODO Не работает, крашится на транслите и ничего не пишет
                # fn = "[{}]-[{}]-[{}]-{}".format(request_id, _userid, time.time(), translit(_filename, reversed=True))
                filename = _FOLDER_4_LEARN_ + os.sep + fn
            with open(filename, 'wb') as fout:
                fout.write(_file.getvalue())
            fout.close()
            return {'StatusCode': '200', 'Message': 'File saved'}

        except Exception as e:
            print(e)
            return {'error': str(e)}


api.add_resource(CollectionsPoint, '/api/CollectionsPoint')
api.add_resource(UploadFile4Recognition, '/api/UploadFile4Recognition')
api.add_resource(UploadFile4Learn, '/api/UploadFile4Learning')
api.add_resource(GetTaskResult, '/api/CallBack')
#TODO Сомнительная фигня т.к. все классы выводить стрёмно, ибо из более 100
api.add_resource(GetList, '/api/List')
api.add_resource(NearWastePlace, '/api/NearWastePlace')


apires = []
apires.append({'Waste Collections Points': '/api/CollectionsPoint'})
apires.append({'Upload File for Recognition': '/api/UploadFile4Recognition'})
apires.append({'Upload File for Learn': '/api/UploadFile4Learning'})
apires.append({'Get Task Result': '/api/CallBack'})
apires.append({'Get List of Waste': '/api/List'})
apires.append({'Waste Place Near You': '/api/NearWastePlace'})


# data = [
#     "Hello!!",
#     {"Web resources":
#         [
#             {'Our site': 'http://openrecycle.github.io'},
#             {'GitHub': 'https://github.com/openrecycle'},
#             {'Social network': 'https://vk.com/openrecycle'},
#             {'Telegram': 'https://t.me/openrecycle'}
#         ]
#     },
#     "For any questions, please, write us in vk or telegram. Thank you a lot!!",
#     {"API resources":
#         [
#             {'Waste Collections Points': '/api/CollectionsPoint'},
#             {'Upload File for Recognition': '/api/UploadFile4Recognition'},
#             {'Upload File for Learn': '/api/UploadFile4Learning'},
#             {'Get Task Result': '/api/CallBack'},
#             {'Get List of Waste': '/api/List'},
#             {'Waste Place Near You': '/api/NearWastePlace'}
#         ]
#     }
# ]


def build_links():
    root = str(request.url_root)
    return [
        "Welcome to API for Open Recycle Community! " + _VERSION_,
        "Hello!!",
        {"Web resources":
            [
                {'Our site': 'http://openrecycle.github.io'},
                {'GitHub': 'https://github.com/openrecycle'},
                {'Social network': 'https://vk.com/openrecycle'},
                {'Telegram': 'https://t.me/openrecycle'}
            ]
        },
        "For any questions, please, write us in vk or telegram. Thank you a lot!!",
        {"API resources":
            [
                {'Waste Collections Points': root+'api/CollectionsPoint'},
                {'Upload File for Recognition': root+'api/UploadFile4Recognition'},
                {'Upload File for Learn': root+'api/UploadFile4Learning'},
                {'Get Task Result': root+'api/CallBack'},
                {'Get List of Waste': root+'api/List'},
                {'Waste Place Near You': root+'api/NearWastePlace'}
            ]
        }
    ]


@app.route("/")
def api_root():
    return "Welcome to API for Open Recycle Community! " + _VERSION_ + "" \
           "</br>Please, go to " + str(request.url_root) + "about for additional info."


@app.route("/about")
def about():
    response = flask.jsonify(build_links())
    return response


@app.errorhandler(404)
def page_not_found(e):
    return flask.jsonify(error=404, text=str(e), about_api=build_links()), 404


app.config['PROFILE'] = True
# app.config['SERVER_NAME'] = '0.0.0.0'
app.config['TRAP_HTTP_EXCEPTIONS'] = True


if __name__ == '__main__':
    app.run(debug=False, threaded=_THREADED_RUN_, host="0.0.0.0", port=48777)
