from .database import db
from datetime import datetime
from sqlalchemy import event

class User(db.Model):
  user_id = db.Column(db.Integer, primary_key=True)
  Fullname = db.Column(db.String(), unique=True, nullable=False)
  email = db.Column(db.String(),unique = True, nullable=False)
  password = db.Column(db.String(), nullable=False)
  address = db.Column(db.String(), unique=False, nullable= False)
  pincode= db.Column(db.Integer, unique=False, nullable=False)
  type = db.Column(db.String(), default='general')
  

class Parking_lot(db.Model):
  __tablename__ = 'parking_lot'
  parking_lot_id=db.Column(db.Integer, unique=True, primary_key=True)
  prime_location_name= db.Column(db.String(), unique=True, nullable=False)
  price_per_hour=db.Column(db.Float, nullable=False)
  address=db.Column(db.String(), unique=False, nullable=False)
  pincode= db.Column(db.Integer, unique=False, nullable=False)
  maximum_number_of_spots=db.Column(db.Integer, nullable=False)
  status = db.Column(db.String(), default='available')
  spots = db.relationship('Parking_spot', back_populates='lot',  cascade="all, delete-orphan",lazy=True)
  
  
class Parking_spot(db.Model):
    __tablename__ = 'parking_spot'
    parking_spot_id = db.Column(db.Integer, unique=True, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.parking_lot_id'), nullable=False)
    prime_location_name = db.Column(db.String(), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(), nullable=False, default='available')  # 'booked' or 'available'
    lot = db.relationship("Parking_lot", back_populates="spots")
    

@event.listens_for(db.session, 'after_flush')
def create_parking_spots(session, context):
    for obj in session.new:
        if isinstance(obj, Parking_lot):
            for i in range(1, obj.maximum_number_of_spots + 1):
                new_spot = Parking_spot(
                    lot_id=obj.parking_lot_id,
                    prime_location_name=obj.prime_location_name,
                    spot_number=i,
                    status='available'
                )
                session.add(new_spot)

        
        
class Reservation(db.Model):
    reservation_id = db.Column(db.Integer, primary_key=True, unique=True) 
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.parking_spot_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.now)
    leaving_time = db.Column(db.DateTime, nullable=True)
    parking_hourly_rate = db.Column(db.Float, nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    total_cost = db.Column(db.Float, nullable=True)
    spot = db.relationship("Parking_spot", backref=db.backref("reservations", cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("reservations", cascade="all, delete-orphan"))
    
    
class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True)
    Fullname = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), unique=False, nullable= False)
    pincode= db.Column(db.Integer, unique=False, nullable=False)
    type = db.Column(db.String(), default='admin')



  
  
