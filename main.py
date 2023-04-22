import os
from flask import Flask, render_template, redirect, request, abort
from werkzeug.utils import secure_filename

from data import db_session
from data.users import User
from data.products import Products
from form.LoginForm import LoginForm
from form.ProductsForm import ProductsForm
from form.user import RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    products = db_sess.query(Products)
    return render_template("index.html", products=products)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/products', methods=['GET', 'POST'])
@login_required
def add_products():
    form = ProductsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = Products()
        products.title = form.title.data
        products.content = form.content.data
        products.price = form.price.data
        file = form.file.data
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                               secure_filename(file.filename)))
        products.photo = file.filename
        current_user.products.append(products)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('products.html', title='Добавление товара', form=form)


@app.route('/products/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_products(id):
    form = ProductsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id,
                                                  Products.user == current_user
                                                  ).first()
        if products:
            form.title.data = products.title
            form.content.data = products.content
            form.price.data = products.price
            form.file.data = products.photo
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id,
                                                  Products.user == current_user
                                                  ).first()
        if products:
            products.title = form.title.data
            products.content = form.content.data
            products.price = form.price.data
            file = form.file.data
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                   secure_filename(file.filename)))
            products.photo = file.filename
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('products.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/products_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).filter(Products.id == id,
                                              Products.user == current_user
                                              ).first()
    if products:
        db_sess.delete(products)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/account')


@app.route("/account")
@login_required
def account():
    db_sess = db_session.create_session()
    products = db_sess.query(Products)
    if current_user.fav != '':
        list_of_fav = current_user.fav.split(';')
        fav = []
        for i in list_of_fav:
            fav.append(int(i))

    else:
        fav = []
    return render_template("account.html", products=products, fav=fav)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/delete_account/<int:id>')
@login_required
def delete_account(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(id)
    db_sess.query(Products).filter(Products.user_id == id).delete()
    db_sess.delete(user)
    db_sess.commit()
    return redirect("/")


@app.route('/add_to_favourite/<int:id>')
@login_required
def add_to_fav(id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).filter(Products.id == id).first()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if current_user.fav != '':
        list_of_fav = current_user.fav.split(';')
        for i in list_of_fav:
            if products.id == int(i):
                return redirect("/")
        list_of_fav.append(str(products.id))
        fav = ';'.join(list_of_fav)
        user.fav = fav
    else:
        current_user.fav = str(products.id)
    db_sess.commit()
    return redirect("/")


def main():
    db_session.global_init("db/base.db")
    app.run()


if __name__ == '__main__':
    main()
