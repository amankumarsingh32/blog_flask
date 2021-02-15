import json
import math
import os
from datetime import datetime

from flask import Flask, render_template, request, session, redirect, flash
from flask_mail import Mail

# import SQLAlchemy library for database connection
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

dir_path = os.path.dirname(os.path.realpath(__file__))

config_path = dir_path + '/config.json'

with open(config_path, 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)

upload_path = dir_path + params["upload_location"]

app.config['UPLOAD_FOLDER'] = upload_path

app.secret_key = "aman@1213#"

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['mail_username'],
    MAIL_PASSWORD=params['mail_password']
)

mail = Mail(app)

# URI to connect to sql databse
app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]

# create databse object
db = SQLAlchemy(app)


# create class to access database table for data entry
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(30), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    subheading = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    img_file = db.Column(db.String(50), nullable=True)
    posted_by = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)


@app.route("/")
def index():
    posts = Posts.query.filter_by().all()

    last = math.ceil(len(posts) / int(params["no_of_posts"]))  # total no of pages 1 to last

    page = request.args.get('page')  # argunent from url gets stored, initally None on page load , page=None

    if not str(page).isnumeric():
        page = 1

    page = int(page)

    posts = posts[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]  # how many post to display in 1 page

    if page == 1:
        prev = '#'
        next = "/?page=" + str(page + 1)

    elif page == last:
        prev = '/?page=' + str(page - 1)
        next = '#'

    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


# send the contact form using POST request to database
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        date = datetime.now()

        entry = Contacts(name=name, email=email, phone=phone, msg=message, date=date)
        db.session.add(entry)
        db.session.commit()

        mail.send_message(
            subject="New Message from " + name,
            sender=email,
            recipients=[params["mail_username"], ],
            body=message + '\n' + phone + '\n' + email
        )
        flash("Message Successfully sent! We'll get back to you soon.")

        return redirect("/contact")
    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user' in session and session['user'] == params['admin_username']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('pass')

        if params['admin_username'] == username and params['admin_password'] == password:
            session["user"] = username
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            flash(params['login_error_msg'], 'danger')
            return render_template('login.html', params=params)

    return render_template('login.html', params=params)


@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if "user" in session and session["user"] == params["admin_username"]:
        if request.method == "POST":
            slug = request.form.get('slug')
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            content = request.form.get('content')
            posted_by = request.form.get('posted_by')
            date = datetime.now()
            if request.files['file1']:
                img_file = request.files['file1']
                print(img_file)
                img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(img_file.filename)))
                img_file = secure_filename(img_file.filename)
            else:
                if sno == '0':
                   img_file = 'NULL'
                else:
                    post = Posts.query.filter_by(sno=sno).first()
                    img_file = post.img_file

            if sno == '0':
                post = Posts(slug=slug, title=title, subheading=subheading, content=content, posted_by=posted_by,
                             date=date, img_file=img_file)
                db.session.add(post)
                db.session.commit()
                flash("Post Added Successfully!", "success")
                return redirect('/dashboard')

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.slug = slug
                post.title = title
                post.subheading = subheading
                post.content = content
                post.img_file = img_file

                db.session.commit()
                flash("Post Edited Successfully!", "warning")
                return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

    return render_template('login.html', params=params)


@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if "user" in session and session["user"] == params["admin_username"]:
        if request.method == "POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded Successfully"


@app.route("/logout")
def logout():
    session.pop("user")
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if "user" in session and session["user"] == params["admin_username"]:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        flash("Post Deleted Successfully!", "danger")
    return redirect("/dashboard")


if __name__ == '__main__':
    app.run()
