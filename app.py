from flask import Flask
from application.database import db 
app = None

def create_app():
  app= Flask(__name__)
  app.debug = True
  app.secret_key = "my_super_secret_key_123"
  app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3" 
  db.init_app(app) 
  app.app_context().push()
  return app

app = create_app()
from application.controllers import * 

if __name__ == '__main__':
  app.run()