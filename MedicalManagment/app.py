import math
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import sqlalchemy
from flask import Flask, render_template, request, url_for, redirect, make_response
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    UserMixin,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pdfkit
from flask import *

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
app = Flask(__name__)
app.secret_key = "bhautikkotadiya"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/medical"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Medicine(db.Model, UserMixin):
    medicine_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    expiry_date = db.Column(db.Date)


class Sell(db.Model, UserMixin):
    invoice_number = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    sell_date = db.Column(db.Date)
    type_of_pay = db.Column(db.String(100))
    total = db.Column(db.Integer)


class Purchase(db.Model, UserMixin):
    purchase_number = db.Column(db.Integer, primary_key=True)
    where_purchase = db.Column(db.String(100))
    total_purchase = db.Column(db.Integer)
    type_of_pay = db.Column(db.String(100))
    date = db.Column(db.Date)


@login_manager.user_loader
def load_user(user_id):
    user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar()
    return user


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/home")
def home1():
    flash('Welcome To Medcare', 'welcome-msg')

    return render_template("index.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        useremail = request.form.get("useremail")
        userpassword = request.form.get("userpassword")
        userconfirmpassword = request.form.get("userconfirmpassword")
        if userpassword != userconfirmpassword:
            flash('Password Does Not Match!', 'error-msg')
            return render_template("forgot.html")
        newpass = generate_password_hash(
            request.form.get("userpassword"), method="pbkdf2:sha256", salt_length=8
        )
        fuser = User.query.filter_by(email=useremail).first()
        if fuser:
            fuser.password = newpass
            db.session.commit()
            flash('Password Change Succesfully!', 'successful-msg')

            return redirect(url_for("home"))
        else:
            flash('Your Account Not Found!!', 'error-msg')
            return render_template("signup.html")

    else:
        return render_template("forgot.html")


@app.route("/logout")
def logout():
    logout_user()
    flash('Logout Successful Done!!', 'info-msg')
    return redirect(url_for("home"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        useremail = request.form.get("useremail")
        userpassword = generate_password_hash(
            request.form.get("userpassword"), method="pbkdf2:sha256", salt_length=8
        )
        try:
            entry = User(name=username, email=useremail, password=userpassword)
            db.session.add(entry)
            db.session.commit()
            login_user(entry)
            flash('Signin Successful Done!!', 'successful-msg')
            return render_template("index.html")
        except sqlalchemy.exc.IntegrityError:
            flash('Your Account Already Exist\nPlease Login!', 'info-msg')
            return render_template("login.html")

    else:
        return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        useremail = request.form.get("useremail")
        userpassword = request.form.get("userpassword")
        fuser = User.query.filter_by(email=useremail).first()
        if fuser:
            if check_password_hash(fuser.password, userpassword):
                login_user(fuser)
                flash('Login Done!', 'successful-msg')
                return render_template("index.html")
            else:
                flash('Enter Valid Password!!', 'error-msg')
                return render_template("login.html")
        else:
            flash('Your Account Not Found!', 'error-msg')
            return render_template("signup.html")

    else:
        return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    total_customer = Sell.query.all()
    total_purchase = Purchase.query.all()
    total_medicine = Medicine.query.all()
    date = datetime.now().strftime("%Y-%m-%d")
    expiry_medicine = 0
    outofstock = 0
    total_sale = 0
    today_purchase = 0
    for x in total_purchase:
        checkdate = str(x.date)
        if checkdate.find(date) != -1:
            print(checkdate, " ", date)
            print(checkdate.find(date))
            today_purchase = today_purchase + int(x.total_purchase)
    for x in total_customer:
        if str(x.sell_date) == date:
            total_sale = total_sale + x.total
    for x in total_medicine:
        if x.quantity == 0:
            outofstock = outofstock + 1
        if x.expiry_date < date:
            expiry_medicine = expiry_medicine + 1

    return render_template(
        "dashboard.html",
        total_customer=len(total_customer),
        total_medicine=len(total_medicine),
        expiry_medicine=expiry_medicine,
        outodstock=outofstock,
        total_sale=total_sale,
        today_purchase=today_purchase
    )


@app.route("/addmedicine", methods=["GET", "POST"])
@login_required
def addmedicine():
    if request.method == "GET":
        return render_template("addmedicine.html", name=current_user.name)
    if request.method == "POST":
        try:
            medicinne_name = request.form.get("medicinename")
            medicinne_price = request.form.get("medicineprice")
            medicinne_quantity = request.form.get("medicinequantity")
            medicinne_expirydate = request.form.get("expirydate")
            entry = Medicine(
                name=medicinne_name,
                price=medicinne_price,
                quantity=medicinne_quantity,
                expiry_date=medicinne_expirydate,
            )
            db.session.add(entry)
            db.session.commit()
            flash('Medicine Succesfully Add', 'successful-msg')
            return render_template("addmedicine.html")
        except IntegrityError:
            return redirect(url_for('managemedicine'))


@app.route("/managemedicine", methods=["GET", "POST"])
@login_required
def managemedicine():
    if request.method == "GET":
        all_medicine = Medicine.query.all()
        return render_template(
            "managemedicine.html", name=current_user.name, medicine_array=all_medicine
        )


@app.route("/delete/<int:id>", methods=["GET"])
@login_required
def delete(id):
    fuser = Medicine.query.filter_by(medicine_id=id).first()
    db.session.delete(fuser)
    db.session.commit()
    flash('SuccessFully Delete!', 'successful-msg')
    return redirect(url_for("managemedicine"))


@app.route("/edit/<int:medicine_id>", methods=["GET"])
@login_required
def edit(medicine_id):
    if request.method == "GET":
        fuser = Medicine.query.filter_by(medicine_id=medicine_id).first()
        return render_template("editmedicine.html", medicine_data=fuser)


@app.route("/editmedicine/<int:medicine_id>", methods=["GET", "POST"])
@login_required
def editmedicine(medicine_id):
    if request.method == "POST":
        fuser = Medicine.query.filter_by(medicine_id=medicine_id).first()
        medicinne_name = request.form.get("medicinename")
        medicinne_price = request.form.get("medicineprice")
        medicinne_quantity = request.form.get("medicinequantity")
        medicinne_expirydate = request.form.get("expirydate")
        fuser.name = medicinne_name
        fuser.price = medicinne_price
        fuser.quantity = medicinne_quantity
        fuser.expiry_date = medicinne_expirydate
        db.session.commit()
        flash('SuccessFully Edit!', 'successful-msg')
        return redirect(url_for("managemedicine"))


@app.route("/newinvoice", methods=["GET", "POST"])
@login_required
def invoice():
    if request.method == "GET":
        medicine = Medicine.query.all()
        medicine_name_arr = []
        for x in medicine:
            if x.name not in medicine_name_arr:
                medicine_name_arr.append(x.name)
        return render_template("newinvoice.html", mecicin=medicine)


cartarr = []


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cartview():
    if request.method == "GET":
        sum = 0
        for x in cartarr:
            sum = sum + (x.price) * (x.quantity)
        return render_template("cart.html", cart_arr=cartarr, total_bill=sum)


@app.route("/cart/<int:medicine_id>", methods=["GET"])
@login_required
def cart(medicine_id):
    if request.method == "GET":
        fuser = Medicine.query.filter_by(medicine_id=medicine_id).first()
        for x in cartarr:
            if x.medicine_id == medicine_id:
                flash('Already In Cart!', 'info-msg')
                return redirect(url_for("invoice"))

        if fuser.quantity <= 0:
            flash('Not Enough Quantity', 'error-msg')
            return redirect(url_for('invoice'))

        newmedicine = fuser
        newmedicine.quantity = 1
        cartarr.append(newmedicine)
        flash('SuccessFully Add In  Cart!', 'successful-msg')
        return redirect(url_for("invoice"))


@app.route("/cartremove/<int:medicine_id>", methods=["GET"])
@login_required
def cartremove(medicine_id):
    if request.method == "GET":
        for x in cartarr:
            if x.medicine_id == medicine_id:
                cartarr.remove(x)
        flash('SuccessFully Remove From Cart!', 'successful-msg')
        return redirect(url_for("cartview"))


@app.route("/increase/<int:medicine_id>", methods=["GET"])
@login_required
def increase(medicine_id):

    if request.method == "GET":
        for x in cartarr:
            if x.medicine_id == medicine_id:
                x.quantity = x.quantity + 1
        flash('Increase Quantity', 'info-msg')
        return redirect(url_for("cartview"))


@app.route("/decrease/<int:medicine_id>", methods=["GET"])
@login_required
def decrease(medicine_id):
    if request.method == "GET":
        for x in cartarr:
            if x.medicine_id == medicine_id:
                if x.quantity == 1:
                    return redirect(url_for("cartview"))
                else:
                    x.quantity = x.quantity - 1

        flash('Decrease Quantity', 'info-msg')

        return redirect(url_for("cartview"))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        total = 0
        for x in cartarr:
            total = total + (x.price * x.quantity)
        if total == 0:
            return redirect(url_for("cartview"))

        discount = request.form.get('discount')
        customername = request.form.get("customer_name")
        date = request.form.get("invoice-date")
        pay_type = request.form.get('payment_mode')
        medicine = Medicine.query.all()
        discountcal = math.ceil(total - total * (int(discount) / 100))
        for x in cartarr:
            findmedi = Medicine.query.filter_by(medicine_id=x.medicine_id).first()
            if x.quantity > findmedi.quantity:
                flash(f'Not Enough Quantity,You Only Sell {x.quantity} Quantity', 'error-msg')
                return redirect(url_for('cartview'))

        for x in cartarr:
            findmedi = Medicine.query.filter_by(medicine_id=x.medicine_id).first()
            findmedi.quantity = findmedi.quantity - x.quantity

        entry = Sell(customer_name=customername, sell_date=date, total=discountcal, type_of_pay=pay_type)
        db.session.add(entry)
        db.session.commit()
        renders = render_template("pdf.html", purchase_items=cartarr, total=total, discount=(total - discountcal),
                                  finalpay=discountcal, date=date, name=customername, seller=current_user.email,
                                  typeofpay=pay_type, invoice_no=4)
        pdf = pdfkit.from_string(renders, configuration=config, options={"enable-local-file-access": ""})
        response = make_response(pdf)
        response.headers['content-Type'] = 'application/pdf'
        response.headers['content-Disposition'] = "attachment; filename=invoice.pdf"
        cartarr.clear()
        flash('Items Successfully Purchased !!', 'successful-msg')
        return response


@app.route("/salesreport", methods=["GET", "POST"])
@login_required
def salesreport():
    if request.method == "GET":
        sell_items = Sell.query.all()
        return render_template("salesreport.html", sell_item=sell_items)


@app.route("/purchasereport", methods=["GET", "POST"])
@login_required
def purchasereport():
    if request.method == "GET":
        purchase_items = Purchase.query.all()
        print(purchase_items)
        return render_template("purchasereport.html", purchase_items=purchase_items)


@app.route('/viewexpired', methods=["GET", "POST"])
@login_required
def viewexpired():
    if request.method == 'GET':
        total_medicine = Medicine.query.all()
        exp_arr = []
        date = datetime.now().strftime("%Y-%m-%d")
        for x in total_medicine:
            if x.expiry_date < date:
                exp_arr.append(x)
    return render_template('viewexpired.html', exp_arr=exp_arr)


@app.route("/deleteexpired/<int:id>", methods=["GET"])
@login_required
def deleteexpired(id):
    fuser = Medicine.query.filter_by(medicine_id=id).first()
    db.session.delete(fuser)
    db.session.commit()
    flash('SuccessFully Remove From Stock!', 'successful-msg')
    return redirect(url_for("viewexpired"))


@app.route("/addpurchase", methods=["GET", "POST"])
@login_required
def addpurchase():
    if request.method == "GET":
        return render_template("addpurchase.html")
    if request.method == 'POST':
        my_date = "30-May-2020-15:59:02"
        d = datetime.strptime(my_date, "%d-%b-%Y-%H:%M:%S")
        final_date = d.strftime("%Y-%m-%d-%H:%M:%S")
        where_purchase = request.form.get('where_purchase')
        total_purchase = request.form.get('total_purchase')
        payment_type = request.form.get('payment_type')
        entry = Purchase(where_purchase=where_purchase, total_purchase=total_purchase, type_of_pay=payment_type,
                         date=final_date)
        db.session.add(entry)
        db.session.commit()
        flash('Purchase Detail add succesfully!', 'successful-msg')
        return render_template("addpurchase.html")


@app.route('/pdf/<int:id>', methods=['GET', 'POST'])
@login_required
def pdfgen(id):
    if request.method == 'POST':
        purchase_items = Purchase.query.all()
        renders = render_template("pdf.html", purchase_items=purchase_items)
        pdf = pdfkit.from_string(str(renders), configuration=config, options={"enable-local-file-access": ""})
        response = make_response(pdf)
        response.headers['content-Type'] = 'application/pdf'
        response.headers['content-Disposition'] = "attachment; filename={}.pdf".format(3)
        return response


if __name__ == "__main__":
    app.run(debug=True)
