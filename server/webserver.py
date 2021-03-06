## !/usr/bin/env python
"""
Author : Hwancheol Kang
Project : Alpha-search
Date : January 5, 2018
Description :
This script is for responding for web-client's request, Using flask and redis.
"""
from __future__ import print_function
import json, os, uuid, redis, pymysql, math
import numpy as np
from flask import Flask, request, make_response, render_template
# import custom modules
import Decorator_for_HTTP
from OpenCafeFinder import findOpenCafes
from Review_filter import getFilteredReviews
# Flask app should start in global layout
app = Flask(__name__)

# Generate Redis Object
redis_obj = redis.StrictRedis(host="localhost", port=6379, db=0)

# Connect to MySQL and Generete dictionary cursor from connection
sql_conn = pymysql.connect(host='localhost',user='gaeul',password='alpha',db='CAFE',charset='utf8mb4')
curs = sql_conn.cursor(pymysql.cursors.DictCursor)

def makeQuery(entities):
    query = "select * from CAFES where " + "wi_fi_available=" + entities['wifi'] + " and parking_available=" + entities['parking']
    return query

def getDatafromDB(query) :
    curs.execute(query)
    data = curs.fetchall()
    return data

def filterbyradius(cafe_list, latitude, longitude) :
    MAX_CAFE_NUM = 20
    MAX_RADIUS = 3000
    filtered_list = []
    for cafe in cafe_list :
        if(getDistance(float(latitude), float(longitude), cafe['latitude'], cafe['longitude']) < MAX_RADIUS) :
            filtered_list.append(cafe)
        if(len(filtered_list) == MAX_CAFE_NUM) : 
            break
    return filtered_list
    
def getDistance(lat1, lon1, lat2, lon2) :
    theta = lon1 - lon2
    dist = np.sin(convertDeg2Rad(lat1)) * np.sin(convertDeg2Rad(lat2)) + np.cos(convertDeg2Rad(lat1)) * np.cos(convertDeg2Rad(lat2)) * np.cos(convertDeg2Rad(theta))
    dist = np.arccos(dist);  
    dist = convertRad2Deg(dist);  
      
    dist = dist * 60 * 1.1515;   
    dist = dist * 1.609344;    
    dist = dist * 1000.0;     

    return dist;  

def convertDeg2Rad(degree) :
    return (degree * math.pi) / 180

def convertRad2Deg(radian) :
    return (radian * 180) / np.pi

@app.route('/mappedcafes/<token>/<latitude>/<longitude>', methods = ['POST', 'GET', 'OPTIONS'])
@Decorator_for_HTTP.crossdomain(origin='*')
def getCafes(token, latitude, longitude) :
    # Get data mapped token from redis table 
    entities = json.loads(redis_obj.get(token).decode("utf-8"))
    # Generate a query
    query = makeQuery(entities)
    # Request to query the DB
    cafe_list = getDatafromDB(query)
    reviews_list = getFilteredReviews()
    open_cafe_list = findOpenCafes(filterbyradius(cafe_list, latitude, longitude))
    for open_cafe in open_cafe_list :
        open_cafe['reviews'] = eval(reviews_list[open_cafe['id']]['reviews_filtered'])
        open_cafe['review_count'] = reviews_list[open_cafe['id']]['review_count']
    response = app.response_class(
        response=json.dumps(open_cafe_list),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/<token>', methods = ['POST', 'GET', 'OPTIONS'])
@Decorator_for_HTTP.crossdomain(origin='*')
def index(token) :
    return render_template("index.html", token=token)

def run() :
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'))

if __name__ == '__main__' :
    run()