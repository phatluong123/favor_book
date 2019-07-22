from flask import Flask, render_template, request, redirect, session, flash
import re, datetime
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key='alo'
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
password_regex = re.compile(r'^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]+$')


@app.route("/")
def index():
    return render_template("registration_login.html")


@app.route('/register', methods=['POST'])
def add_info():
    is_valid = True
    if len(request.form['first_name']) < 2:
        flash("First name at least 2 characters",  'first')
        is_valid = False
    if len(request.form['last_name']) < 2:
        flash("Last name at least 2 characters",'last')
        is_valid = False
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid email, please re-enter", 'email_error')
        is_valid = False
    email=request.form['email']
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email": request.form["email"]}
    mysql = connectToMySQL('favor_book')
    users_email=mysql.query_db(query, data)
    count=0
    for user_email in users_email:
        if user_email['email'] == email:
            count+=1
    if count==0:
        pass
    if count!=0:
        flash("email exist", 'email')
        is_valid = False
    # if not password_regex.match(request.form['password1']) or len(request.form['password1']) < 8:
    #     flash("Password at least 8 characters and must have 1 Upper case, 1 Lower case, 1 special (@#$), and 1 digit ", 'password1')
    #     is_valid = False
    if (request.form['password1']) != (request.form['password2']):
        flash("Password not match", 'password2')
        is_valid = False
    if not is_valid:
        return redirect("/")
    else:

        pw_hash = bcrypt.generate_password_hash(request.form['password1'])
        data = {
            'fn': request.form['first_name'],
            'ln': request.form['last_name'],
            'email': request.form['email'],
            'pw_hash': pw_hash
        }
        query='INSERT INTO users (first_name, last_name, email, pw_hash) VALUES (%(fn)s, %(ln)s, %(email)s, %(pw_hash)s )'
        mysql=connectToMySQL('favor_book')
        user_id = mysql.query_db(query, data)
        session['user_id']=user_id
        return redirect('/books')


@app.route('/login', methods=['POST'])
def logged_in():
    mysql = connectToMySQL('favor_book')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email": request.form["login_email"]}
    result = mysql.query_db(query, data)
    if len(result) >0:
        if bcrypt.check_password_hash(result[0]['pw_hash'], request.form['login_password']):
            session['user_id'] = result[0]['id']
            return redirect('/books')
    else :
        flash('Email or password wrong', 'login_error')
        return redirect("/")

@app.route('/books')
def success_log_in():
    user_id = session['user_id']
    query = (f'select users.first_name, users.last_name, favor.book_id, favor.user_id from users join favor on favor.user_id = users.id where user_id ={user_id}')
    mysql = connectToMySQL('favor_book')
    user = mysql.query_db(query)
    user_name = user[0]['first_name']
    query2= 'select books.id as book_id, books.title, users.first_name from books join users on users.id  = books.user_id'
    mysql = connectToMySQL('favor_book')
    books = mysql.query_db(query2)
    print(books)
    print(user)
    for book in books:
        for user_favor in user:
            if user_favor['book_id'] == book['book_id']:
                book['favor']='this'
                print(book['favor'])
    return render_template('logged.html',user_name=user_name, books=books)


@app.route('/books/add', methods=['POST'])
def add_to_favor():
    is_valid = True

    if len(request.form['book_title']) < 1:
        flash("Title cannot be empty", 'title')
        is_valid = False
    if len(request.form['description']) < 5:
        flash("Description at least 5 characters", 'description')
        is_valid = False
    if not is_valid:
        return redirect("/books")
    else:
        data1={
            'title':request.form['book_title'],
            'description':request.form['description'],
            'user_id': session['user_id']
        }

        query = 'insert into books(title, description, user_id) Values(%(title)s, %(description)s, %(user_id)s)'
        mysql = connectToMySQL('favor_book')
        new_book_id= mysql.query_db(query, data1)
        data={
            'book_id':new_book_id,
            'user_id':session['user_id']
        }
        query='insert into favor (user_id, book_id) Values(%(user_id)s, %(book_id)s)'
        mysql = connectToMySQL('favor_book')
        mysql.query_db(query, data)
        return redirect("/books")


@app.route('/books/<book_id>/add_to_favor')
def addtofavor(book_id):
    data = {
        'book_id': int(book_id),
        'user_id': session['user_id']
    }
    query = 'insert into favor (user_id, book_id) Values(%(user_id)s, %(book_id)s)'
    mysql = connectToMySQL('favor_book')
    mysql.query_db(query, data)
    return redirect("/books")


@app.route('/books/<book_id>')
def detail(book_id):
    user_id = session['user_id']
    query=f'select * from users where id ={user_id}'
    mysql = connectToMySQL('favor_book')
    user = mysql.query_db(query)

    query = f'select * from  (select books.id as book_id , books.title, books.description, books.created_at, ' \
        f'books.updated_at,users.id as user_id, users.first_name, users.last_name from books ' \
        f'join users on users.id = books.user_id)as t where book_id ={book_id}'
    mysql = connectToMySQL('favor_book')
    book = mysql.query_db(query)

    query=f'select  users.first_name, users.last_name, favor.book_id, favor.user_id from favor ' \
        f'join users on users.id = favor.user_id where book_id={book_id}'
    mysql = connectToMySQL('favor_book')
    thisbook_favor_by = mysql.query_db(query)
    count=0
    for name in thisbook_favor_by:
        if name['user_id'] == session['user_id']:
            count+=1
    return render_template('book.html', book=book, user=user, thisbook_favor_by=thisbook_favor_by, count=count)


@app.route('/books/update/description/<book_id>', methods=['POST'])
def update(book_id):
    data={
        'des':request.form['description']
    }
    query=f'UPDATE books SET description = %(des)s WHERE (`id` = {book_id});'
    mysql = connectToMySQL('favor_book')
    mysql.query_db(query, data)
    return redirect(f'/books/{book_id}')


@app.route('/delete/<book_id>')
def delete(book_id):
    query=f'Delete from books where id = {book_id}'
    mysql = connectToMySQL('favor_book')
    mysql.query_db(query)
    return redirect('/books')


@app.route('/unfollow/<book_id>')
def unflollow(book_id):
    user_id = session['user_id']
    query=f'delete from favor where book_id={book_id} and user_id={user_id}'
    mysql = connectToMySQL('favor_book')
    mysql.query_db(query)
    return redirect(f'/books/{book_id}')


@app.route('/books/users')
def showbook():
    user_id = session['user_id']
    query=f'select * from (select books.title, users.first_name, users.last_name, favor.user_id, favor.book_id ' \
        f'from favor join books on favor.book_id = books.id ' \
        f'join users on users.id = favor.user_id)as t where user_id = {user_id}'
    mysql = connectToMySQL('favor_book')
    books=mysql.query_db(query)
    return render_template('allbooks.html', books=books)


@app.route('/logout')
def logout():
    flash('You have been log out')
    return redirect('/')



if __name__ == "__main__":
    app.run(debug=True)


