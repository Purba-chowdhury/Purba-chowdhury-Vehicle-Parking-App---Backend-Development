from flask import Flask, render_template, redirect, request, session, url_for,flash
from flask import current_app as app 
from datetime import datetime
from .models import *
import pytz
from sqlalchemy.orm import joinedload
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from math import ceil
import matplotlib 
matplotlib.use('Agg')  # Use non-GUI backend to avoid Tkinter error


@app.route("/")
def login_selection():
    return render_template("choose_role.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        this_user = User.query.filter_by(email=email, password = password,type = "general").first()

        if this_user:
            session["user_id"] = this_user.user_id  #  store session

            return redirect(url_for("user_dashboard", user_id=this_user.user_id))
        else:
            return render_template("login.html", error="Invalid user credentials")
        
    return render_template("login.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
                
        admin = Admin.query.filter_by(email=email, password=password).first()

        if admin:
            session["admin_id"] = admin.admin_id  # Use admin_id now
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Invalid admin credentials")

    return render_template("admin_login.html")


@app.route("/register", methods = ["GET","POST"])
def register():
    if request.method == "POST":
        Fullname = request.form["Fullname"]
        email = request.form["email"]
        password = request.form.get("password")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        this_email = User.query.filter_by(email = email).first()
        this_user = User.query.filter_by(Fullname = Fullname).first()
        if this_user or this_email:
            return "User already exist"
        else:
            user = User(Fullname= Fullname, email=email,password=password,address=address,pincode=pincode)
            db.session.add(user)
            db.session.commit()
            return render_template("register_success.html")
    return render_template("register.html")
 

@app.route("/user_dash/<int:user_id>")
def user_dashboard(user_id):
    # Ensure the latest DB state after any inserts
    db.session.expire_all()

    # Fetch the user
    this_user = User.query.get(user_id)

    # Fetch all reservations for this user
    user_reservations = (
        db.session.query(Reservation, Parking_spot, Parking_lot)
        .join(Parking_spot, Reservation.spot_id == Parking_spot.parking_spot_id)
        .join(Parking_lot, Parking_spot.lot_id == Parking_lot.parking_lot_id)
        .filter(Reservation.user_id == user_id)
        .order_by(Reservation.parking_timestamp.desc())
        .all()
    )

    print("Fetched reservations for user:", user_id, [r[0].reservation_id for r in user_reservations])  # Debugging

    return render_template("user_dash.html", this_user=this_user, reservations=user_reservations)



# @app.route("/search_parking/<int:user_id>", methods=["GET"])
# def search_parking(user_id):
#     query = request.args.get("query", "").strip()
#     this_user = User.query.get(user_id)
        
#     # Step 1: Get matching lots (based on location or pincode)
#     if query.isdigit():
#         matching_lots = Parking_lot.query.filter(Parking_lot.pincode == int(query)).all()
#     else:
#         matching_lots = Parking_lot.query.filter(
#             Parking_lot.prime_location_name.ilike(f"%{query}%")
#         ).all()

#     # Step 2: Filter lots that have at least one 'available' spot
#     available_data = []
#     for lot in matching_lots:
#         available_spots = Parking_spot.query.filter_by(
#             lot_id=lot.parking_lot_id, status='available'
#         ).all()

#         if available_spots:
#             # Add the entire list of available spots to use in template
#             available_data.append({
#                 'lot': lot,
#                 'available_spots': available_spots,
#                 'available_count': len(available_spots)
#             })

#     # Step 3: Get this user's current active reservations
#     user_reservations = (
#         db.session.query(Reservation, Parking_spot, Parking_lot)
#         .join(Parking_spot, Reservation.spot_id == Parking_spot.parking_spot_id)
#         .join(Parking_lot, Parking_spot.lot_id == Parking_lot.parking_lot_id)
#         .filter(Reservation.user_id == user_id)
#         .order_by(Reservation.parking_timestamp.desc())
#         .all()
#     )

#     return render_template("user_dash.html",
#                            this_user=this_user,
#                            search_results=available_data,
#                            searched_location=query,
#                            reservations=user_reservations)

@app.route("/search_parking/<int:user_id>", methods=["GET"])
def search_parking(user_id):
    query = request.args.get("query", "").strip()
    this_user = User.query.get(user_id)

    if query.isdigit():
        matching_lots = Parking_lot.query.filter(Parking_lot.pincode == int(query)).all()
    else:
        matching_lots = Parking_lot.query.filter(
            Parking_lot.prime_location_name.ilike(f"%{query}%")
        ).all()

    available_data = []

    for lot in matching_lots:
        booked_count = Parking_spot.query.filter_by(
            lot_id=lot.parking_lot_id, status='booked'
        ).count()

        available_spots = Parking_spot.query.filter_by(
            lot_id=lot.parking_lot_id, status='available'
        ).order_by(Parking_spot.spot_number).all()

        available_data.append({
            'lot': lot,
            'available_spots': available_spots,
            'available_count': lot.maximum_number_of_spots - booked_count
        })

    # Fetch user reservations
    user_reservations = (
        db.session.query(Reservation, Parking_spot, Parking_lot)
        .join(Parking_spot, Reservation.spot_id == Parking_spot.parking_spot_id)
        .join(Parking_lot, Parking_spot.lot_id == Parking_lot.parking_lot_id)
        .filter(Reservation.user_id == user_id)
        .order_by(Reservation.parking_timestamp.desc())
        .all()
    )

    return render_template(
        "user_dash.html",
        this_user=this_user,
        search_results=available_data,
        searched_location=query,
        reservations=user_reservations
    )


    
@app.route("/book/<int:parking_lot_id>/<int:user_id>/<int:parking_spot_id>")
def book_pl(parking_lot_id, user_id, parking_spot_id):
    this_user = User.query.get(user_id)
    lot = Parking_lot.query.get(parking_lot_id)
    spot = Parking_spot.query.filter_by(parking_spot_id=parking_spot_id, status="available").first()

    if not this_user or not lot or not spot:
        flash("This parking spot is no longer available. Please choose another one.", "danger")
        return redirect(url_for("search_parking", user_id=user_id))

    return render_template("book_the_parking_spot.html", 
                           this_user=this_user, 
                           lot=lot, 
                           spot=spot)


@app.route("/reserve", methods=["POST"])
def reserve():
    try:
        spot_id = int(request.form["spot_id"])
        lot_id = int(request.form["lot_id"])
        user_id = int(request.form["user_id"])
        vehicle_number = request.form["v_number"]

        spot = Parking_spot.query.get(spot_id)
        lot = Parking_lot.query.get(lot_id)

        if not spot or spot.status != 'available':
            return "Invalid or already booked spot", 400

        spot.status = 'booked'

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)

        new_reservation = Reservation(
            spot_id=spot_id,
            user_id=user_id,
            parking_timestamp=current_time,
            parking_hourly_rate=lot.price_per_hour,
            vehicle_number=vehicle_number
        )

        db.session.add(new_reservation)
        db.session.commit()

        return redirect(url_for('user_dashboard', user_id=user_id))

    except Exception as e:
        print("Reservation Error:", e)
        return "Invalid data", 400




# @app.route("/reserve", methods=["POST"])
# def reserve():
#     try:
#         print("Getting form data")
#         spot_id = int(request.form["spot_id"])
#         lot_id = int(request.form["lot_id"])
#         user_id = int(request.form["user_id"])
#         vehicle_number = request.form["v_number"]  # Keep as string

#         print("Fetching spot and lot")
#         spot = Parking_spot.query.get(spot_id)
#         lot = Parking_lot.query.get(lot_id)

#         if not spot or spot.status != 'available':
#             print("Spot is invalid or already booked")
#             return "Invalid or already booked spot", 400

#         print("Marking spot and lot")
#         spot.status = 'booked'
#         if lot.maximum_number_of_spots > 0:
#             lot.maximum_number_of_spots -= 1
            
#         ist = pytz.timezone('Asia/Kolkata')
#         current_time = datetime.now(ist)

#         print("Creating reservation")
#         new_reservation = Reservation(
#             spot_id=spot_id,
#             user_id=user_id,
#             parking_timestamp=current_time,
#             parking_hourly_rate=lot.price_per_hour,
#             vehicle_number=vehicle_number
#         )

#         print("Adding to DB")
#         db.session.add(new_reservation)
#         db.session.commit()

#         print("Redirecting to user_dashboard")
#         return redirect(url_for('user_dashboard', user_id=user_id))

#     except Exception as e:
#         print("Reservation Error:", e)
#         return "Invalid data", 400



    

from math import ceil

@app.route("/release/<int:user_id>/<int:reservation_id>", methods=["GET", "POST"])
def release_parking(user_id, reservation_id):
    reservation = Reservation.query.get(reservation_id)

    if request.method == "POST":
        releasing_time_str = request.form.get("r_time")
        if not releasing_time_str:
            return "Release time not provided", 400

        releasing_input_time = datetime.strptime(releasing_time_str, "%Y-%m-%dT%H:%M")
        releasing_time = reservation.parking_timestamp.replace(
            hour=releasing_input_time.hour, 
            minute=releasing_input_time.minute
        )

        if releasing_time < reservation.parking_timestamp:
            releasing_time = datetime.now()

        duration = (releasing_time - reservation.parking_timestamp).total_seconds() / 3600
        charged_hours = ceil(duration) if duration > 0 else 1

        cost_per_hour = reservation.spot.lot.price_per_hour
        total_cost = charged_hours * cost_per_hour

        reservation.leaving_time = releasing_time
        reservation.total_cost = total_cost
        reservation.spot.status = "available"

        db.session.commit()
        return redirect(url_for("user_dashboard", user_id=user_id))

    now = datetime.now()
    duration = (now - reservation.parking_timestamp).total_seconds() / 3600
    estimated_cost = ceil(duration) * reservation.spot.lot.price_per_hour

    return render_template(
        "release_the_parking_spot.html",
        reservation=reservation,
        user_id=user_id,
        now=now.strftime("%Y-%m-%dT%H:%M"),
        total_cost=estimated_cost
    )





@app.route("/user_summary")
def user_summary():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_login"))

    this_user = User.query.get(user_id)

    reservations = Reservation.query.options(
        joinedload(Reservation.spot).joinedload(Parking_spot.lot)
    ).filter_by(user_id=user_id).all()

    location_counts = {}
    for r in reservations:
        location = r.spot.lot.prime_location_name
        location_counts[location] = location_counts.get(location, 0) + 1

    location_data = [{"location": k, "count": v} for k, v in location_counts.items()]

    plot_url = ""
    if location_data:
        # Plot bar chart
        locations = [item["location"] for item in location_data]
        counts = [item["count"] for item in location_data]

        plt.figure(figsize=(6, 4))
        plt.bar(locations, counts, color="#4CAF50")
        plt.title("Reservation Count by Location")
        plt.xlabel("Location")
        plt.ylabel("Count")
        plt.xticks(rotation=30, ha='right')
        plt.tight_layout()

        # Convert plot to PNG image in base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
        buf.close()
        plt.close()

    return render_template(
        "user_summary.html",
        this_user=this_user,
        location_data=location_data,
        plot_url=plot_url
    )


@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.Fullname = request.form['Fullname']
        user.email = request.form['email']
        user.address = request.form['address']
        user.pincode = int(request.form['pincode'])

        db.session.commit()
        return redirect(url_for('user_dashboard', user_id=user.user_id))

    return render_template('edit_user.html', user=user)


@app.route("/update_user/<int:user_id>", methods=["POST"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    user.user_name = request.form["user_name"]
    user.user_email = request.form["user_email"]
    user.user_phone = request.form["user_phone"]
    user.user_password = request.form["user_password"]

    db.session.commit()
    flash("Profile updated successfully!")
    return redirect(url_for("user_dashboard", user_id=user_id))
    
    
    
# @app.route("/admin_dashboard")
# def admin_dashboard():
#     admin_id = session.get("admin_id")
#     if not admin_id:
#         return redirect(url_for("admin_login"))

#     admin = Admin.query.get(admin_id)

#     lots_data = []
#     all_lots = Parking_lot.query.all()

#     for lot in all_lots:
#         spots = Parking_spot.query.filter_by(lot_id=lot.parking_lot_id).all()
#         total_spots = len(spots)
#         occupied = sum(1 for spot in spots if spot.status == 'booked')
#         lots_data.append({
#             'lot': lot,
#             'spots': spots,
#             'occupied': occupied,
#             'total': total_spots
#         })

#     return render_template("admin_dashboard.html", admin=admin, lots_data=lots_data)

# @app.route("/admin_dashboard")
# def admin_dashboard():
#     admin_id = session.get("admin_id")
#     if not admin_id:
#         return redirect(url_for("admin_login"))

#     admin = Admin.query.get(admin_id)

#     lots_data = []
#     all_lots = Parking_lot.query.all()

#     for lot in all_lots:
#         # Fetch only booked spots within the max spot range
#         booked_spots = Parking_spot.query.filter(
#             Parking_spot.lot_id == lot.parking_lot_id,
#             Parking_spot.spot_number <= lot.maximum_number_of_spots,
#             Parking_spot.status == 'booked'
#         ).count()

#         available_spots = lot.maximum_number_of_spots - booked_spots

#         lots_data.append({
#             'lot': lot,
#             'occupied': booked_spots,
#             'available': available_spots,
#             'total': lot.maximum_number_of_spots
#         })

#     return render_template("admin_dashboard.html", admin=admin, lots_data=lots_data)

@app.route("/admin_dashboard")
def admin_dashboard():
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(admin_id)
    lots_data = []

    all_lots = Parking_lot.query.all()

    for lot in all_lots:
        booked_spots = Parking_spot.query.filter_by(
            lot_id=lot.parking_lot_id, status='booked'
        ).count()

        available_spots = lot.maximum_number_of_spots - booked_spots

        spots = Parking_spot.query.filter_by(
            lot_id=lot.parking_lot_id
        ).order_by(Parking_spot.spot_number).all()

        lots_data.append({
            'lot': lot,
            'occupied': booked_spots,
            'available': available_spots,
            'total': lot.maximum_number_of_spots,
            'spots': spots
        })

    return render_template("admin_dashboard.html", admin=admin, lots_data=lots_data)






@app.route("/new_parking_lot", methods=["GET", "POST"])
def new_parking_lot():
    #this_user = User.query.filter_by(type="admin").first()
    if "admin_id" not in session:
        return redirect("/admin_login")

    admin_id = session["admin_id"]

    if request.method == "POST":
        location = request.form.get("p_location")
        address = request.form.get("address")
        pin_code = int(request.form.get("pincode"))
        price_per_hour = float(request.form.get("price"))
        maximum_spot = int(request.form.get("spots"))

        parking_lot = Parking_lot(
            prime_location_name=location,
            price_per_hour=price_per_hour,
            address=address,
            pincode=pin_code,
            maximum_number_of_spots=maximum_spot
        )
        db.session.add(parking_lot)
        db.session.commit()  # Triggers event to create spots

        #return redirect(url_for("admin_dashboard", user_id=this_user.user_id)) 
        return redirect(url_for("admin_dashboard")) 
    return render_template("new_parking_lot.html")


  

@app.route('/admin/users')
def show_users():
    admin_id = session.get("admin_id")
    admin = Admin.query.get(admin_id)
    users = User.query.filter_by(type='general').all() 
    return render_template('admin_users.html', users=users, admin = admin)

# @app.route("/edit_parking_lot/<int:parking_lot_id>", methods=["GET", "POST"])
# def edit_parking_lot(parking_lot_id):
#     lot = Parking_lot.query.get(parking_lot_id)
#     if not lot:
#         return "Parking Lot not found"

#     if request.method == "POST":
#         try:
#             new_max = int(request.form.get("spots", "").strip())
#         except ValueError:
#             return "Invalid number of spots"

#         old_max = lot.maximum_number_of_spots

#         # Update basic lot info (keep the spot count update at the end)
#         lot.prime_location_name = request.form["p_location"]
#         lot.address = request.form["address"]
#         lot.pincode = int(request.form["pincode"])
#         lot.price_per_hour = float(request.form["price"])

#         # --- Spot sync logic ---
#         if new_max > old_max:
#             # Add new spots
#             for i in range(old_max + 1, new_max + 1):
#                 new_spot = Parking_spot(
#                     lot_id=lot.parking_lot_id,
#                     prime_location_name=lot.prime_location_name,
#                     spot_number=i,
#                     status='available'
#                 )
#                 db.session.add(new_spot)
#             lot.maximum_number_of_spots = new_max  # safe to update here

#         elif new_max < old_max:
#             # Check if spots beyond new_max can be deleted
#             extra_spots = Parking_spot.query.filter(
#                 Parking_spot.lot_id == lot.parking_lot_id,
#                 Parking_spot.spot_number > new_max
#             ).all()

#             for spot in extra_spots:
#                 if spot.status != 'available':
#                     return "Cannot remove spots that are currently booked"

#             # Safe to delete all extra available spots
#             for spot in extra_spots:
#                 db.session.delete(spot)

#             lot.maximum_number_of_spots = new_max  # update only after safe deletion

#         else:
#             lot.maximum_number_of_spots = new_max  # spot count unchanged

#         # --- 🔐 Safety Cleanup (NEW): Delete orphaned available spots beyond new max ---
#         ghost_spots = Parking_spot.query.filter(
#             Parking_spot.lot_id == lot.parking_lot_id,
#             Parking_spot.spot_number > lot.maximum_number_of_spots,
#             Parking_spot.status == 'available'
#         ).all()

#         for spot in ghost_spots:
#             db.session.delete(spot)

#         db.session.commit()

#         return redirect(url_for("admin_dashboard"))

#     return render_template("edit_parking_lot.html", lot=lot)





# @app.route("/edit_parking_lot/<int:parking_lot_id>", methods=["GET", "POST"])
# def edit_parking_lot(parking_lot_id):
#     lot = Parking_lot.query.get(parking_lot_id)
#     if not lot:
#         return "Parking Lot not found"

#     if request.method == "POST":
#         try:
#             new_max = int(request.form.get("spots", "").strip())
#         except ValueError:
#             return "Invalid number of spots"

#         old_max = lot.maximum_number_of_spots

#         # Update basic lot info
#         lot.prime_location_name = request.form["p_location"]
#         lot.address = request.form["address"]
#         lot.pincode = int(request.form["pincode"])
#         lot.price_per_hour = float(request.form["price"])
#         lot.maximum_number_of_spots = new_max

#         # --- Spot sync logic ---
#         if new_max > old_max:
#             # Add new spots
#             for i in range(old_max + 1, new_max + 1):
#                 new_spot = Parking_spot(
#                     lot_id=lot.parking_lot_id,
#                     prime_location_name=lot.prime_location_name,
#                     spot_number=i,
#                     status='available'
#                 )
#                 db.session.add(new_spot)
                

#         elif new_max < old_max:
#             extra_spots = Parking_spot.query.filter(
#                 Parking_spot.lot_id == lot.parking_lot_id,
#                 Parking_spot.spot_number > new_max
#             ).all()

#             for spot in extra_spots:
#                 if spot.status == 'available':
#                     db.session.delete(spot)
#                 else:
#                     return "Cannot remove spots that are currently booked"

#         db.session.commit()
#         return redirect(url_for("admin_dashboard"))

#     return render_template("edit_parking_lot.html", lot=lot)

@app.route("/edit_parking_lot/<int:parking_lot_id>", methods=["GET", "POST"])
def edit_parking_lot(parking_lot_id):
    lot = Parking_lot.query.get(parking_lot_id)
    if not lot:
        return "Parking Lot not found", 404

    if request.method == "POST":
        try:
            new_max = int(request.form.get("spots", "").strip())
        except ValueError:
            return "Invalid number of spots", 400

        old_max = lot.maximum_number_of_spots

        # Update lot details
        lot.prime_location_name = request.form["p_location"]
        lot.address = request.form["address"]
        lot.pincode = int(request.form["pincode"])
        lot.price_per_hour = float(request.form["price"])
        lot.maximum_number_of_spots = new_max

        if new_max > old_max:
            # Add only missing spots
            for i in range(old_max + 1, new_max + 1):
                existing = Parking_spot.query.filter_by(
                    lot_id=lot.parking_lot_id,
                    spot_number=i
                ).first()

                if not existing:
                    new_spot = Parking_spot(
                        lot_id=lot.parking_lot_id,
                        prime_location_name=lot.prime_location_name,
                        spot_number=i,
                        status='available'
                    )
                    db.session.add(new_spot)

        elif new_max < old_max:
            # Remove extra spots
            extra_spots = Parking_spot.query.filter(
                Parking_spot.lot_id == lot.parking_lot_id,
                Parking_spot.spot_number > new_max
            ).all()
            for spot in extra_spots:
                db.session.delete(spot)

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_parking_lot.html", lot=lot)




@app.route("/delete_parking_lot/<int:parking_lot_id>")
def delete_parking_lot(parking_lot_id):
    lot = Parking_lot.query.get(parking_lot_id)

    if not lot:
        return "Parking Lot not found"
    
    for spot in lot.spots:
        if spot.status == 'booked':
            return "Cannot delete lot. Some spots are still booked."

    # Delete associated spots first (if needed)
    for spot in lot.spots:
        db.session.delete(spot)

    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/view_parking_spot/<int:parking_spot_id>", methods=["GET", "POST"])
def view_parking_spot(parking_spot_id):
    spot = Parking_spot.query.get_or_404(parking_spot_id)

    # Get the reservation if the spot is booked
    booking = None
    if spot.status == "booked":
        booking = Reservation.query.filter_by(spot_id=spot.parking_spot_id).order_by(Reservation.parking_timestamp.desc()).first()

    if request.method == "POST":
        if spot.status == "booked":
            flash("Cannot delete a booked spot.", "danger")
        else:
            db.session.delete(spot)
            db.session.commit()
            flash("Spot deleted successfully.", "success")
            return redirect(url_for("admin_dashboard"))

    return render_template("view_parking_lot.html", spot=spot, booking=booking)



@app.route("/occupied_spot_details/<int:reservation_id>", methods=["GET"])
def occupied_spot_details(reservation_id):
    booking = Reservation.query.get_or_404(reservation_id)

    spot = Parking_spot.query.get_or_404(booking.spot_id)

    return render_template("occupied_parking_spot_details.html", spot=spot, booking=booking)



@app.route("/search_page", methods=["GET", "POST"])
def search_page():
    lots_data = []
    reservations = []
    query_type = request.args.get("query_type")
    query = request.args.get("query", "").strip()

    # Fetch admin using session
    admin_id = session.get("admin_id")
    admin = Admin.query.get(admin_id) if admin_id else None

    if query_type == "user_id":
        if query.isdigit():
            reservations = Reservation.query.options(
                joinedload(Reservation.spot).joinedload(Parking_spot.lot),
                joinedload(Reservation.user)
            ).filter_by(user_id=int(query)).all()
        else:
            flash("Please enter a valid user ID.")

    elif query_type == "location":
        lots = Parking_lot.query.options(joinedload(Parking_lot.spots))\
                    .filter(Parking_lot.prime_location_name.ilike(f"%{query}%")).all()
        for lot in lots:
            spots = lot.spots
            occupied = sum(1 for s in spots if s.status == 'booked')
            total = len(spots)
            lots_data.append({
                "lot": lot,
                "spots": spots,
                "occupied": occupied,
                "total": total
            })

    return render_template("admin_search_page.html", 
                           admin=admin,  
                           reservations=reservations, 
                           lots_data=lots_data, 
                           query=query, 
                           query_type=query_type)

    
    
@app.route("/admin/edit_profile", methods=["GET", "POST"])
def edit_admin_profile():
    admin_id = session.get("admin_id")
    if not admin_id:
        flash("Admin not logged in")
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(admin_id)
    if not admin:
        flash("Admin not found")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        admin.Fullname = request.form.get("Fullname")
        admin.email = request.form.get("email")
        admin.address = request.form.get("address")
        admin.pincode = request.form.get("pincode")
        db.session.commit()
        flash("Admin profile updated successfully!")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_admin.html", admin=admin)


@app.route("/admin_summary")
def admin_summary():
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(admin_id)
    all_lots = Parking_lot.query.all()

    # ----- Revenue Data -----
    revenue_data = []
    for lot in all_lots:
        total = (
            db.session.query(func.sum(Reservation.total_cost))
            .join(Parking_spot, Parking_spot.parking_spot_id == Reservation.spot_id)
            .filter(Parking_spot.lot_id == lot.parking_lot_id)
            .scalar()
        ) or 0
        revenue_data.append((lot.prime_location_name, total))

    # Revenue Chart (Bar)
    locations = [item[0] for item in revenue_data]
    revenues = [item[1] for item in revenue_data]

    plt.figure(figsize=(15, 8))
    bars = plt.bar(locations, revenues, color='#3498db')
    plt.xlabel("Location", fontsize = 30)
    plt.ylabel("Total Revenue", fontsize = 30)
    plt.title("Revenue by Parking Lot", fontsize = 30)
    plt.xticks(rotation=45, fontsize = 20)
    plt.yticks(fontsize=20)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f'{int(height)}', ha='center', va='bottom',fontsize=20)
    buf1 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    revenue_chart = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close()

    # ----- Occupancy Data -----
    occupancy_data = []
    for lot in all_lots:
        spots = Parking_spot.query.filter_by(lot_id=lot.parking_lot_id).all()
        occupied = sum(1 for s in spots if s.status == "booked")
        available = sum(1 for s in spots if s.status == "available")
        occupancy_data.append({
            "lot": lot.prime_location_name,
            "occupied": occupied,
            "available": available
        })

    # Occupancy Chart (Stacked Bar)
    labels = [item['lot'] for item in occupancy_data]
    occupied_vals = [item['occupied'] for item in occupancy_data]
    available_vals = [item['available'] for item in occupancy_data]
    x = range(len(labels))

    plt.figure(figsize=(15, 8))
    plt.bar(x, occupied_vals, label='Occupied', color='#e74c3c')
    plt.bar(x, available_vals, bottom=occupied_vals, label='Available', color='#2ecc71')
    plt.xticks(x, labels, rotation=45,fontsize = 20)
    plt.yticks(fontsize=20)
    plt.ylabel("Number of Spots",fontsize = 30)
    plt.title("Occupancy Status per Parking Lot",fontsize = 30)
    plt.legend(fontsize = 25)
    buf2 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    occupancy_chart = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close()

    # Render template
    return render_template(
        "admin_summary.html",
        admin=admin,
        revenue_data=revenue_data,
        occupancy_data=occupancy_data,
        revenue_chart=revenue_chart,
        occupancy_chart=occupancy_chart
    )
    



