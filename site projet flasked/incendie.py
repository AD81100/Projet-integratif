from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import os
import sqlite3



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return redirect(url_for('index'))

@app.route('/france.html')
def france():
    return render_template('france.html')

@app.route('/corse.html')
def corse():
    return render_template('corse.html')

@app.route('/paca.html')
def paca():
    return render_template('paca.html')

@app.route('/aquitaine.html')
def aquitaine():
    return render_template('aquitaine.html')


@app.route('/occitanie.html')
def occitanie():
    return render_template('occitanie.html')

@app.route('/bourgogne.html')
def bourgogne():
    color = "red"
    return render_template('bourgogne.html', color=color)

@app.route('/information.html')
def information():
    return render_template('information.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')



if __name__ == '__main__':
    app.run()
    
    
    

