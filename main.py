import os
import logging
from routes.discovery import discovery
from routes.enhancement import enhancement
from flask import Flask, request, render_template


logger = logging.getLogger(__name__)
app = Flask(__name__)

app.register_blueprint(discovery)
app.register_blueprint(enhancement)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/', methods=['GET'])
def init():
    return render_template('home.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error_404.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000, debug=True)
