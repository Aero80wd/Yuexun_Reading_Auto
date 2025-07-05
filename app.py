from flask import Flask
import uuid
import views
from views import *
from flask_bootstrap import Bootstrap5
from flask_sslify import SSLify
app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4().hex
bootstrap = Bootstrap5(app)
app.register_blueprint(main)
ssl = SSLify(app)
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8765)