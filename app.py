from flask import Flask, render_template, request, redirect, session, flash
import pymysql
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory
from datetime import datetime
import random
import string


app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL DB 연결
db = pymysql.connect(
    host='localhost',
    user='root',
    password='user password', #본인의 MYSQL 비밀번호 입력하기
    database='board_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 메인 페이지 - 게시글 목록 & 검색 기능
@app.route('/')
def index():
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')

    cursor = db.cursor()

    base_sql = """
        SELECT posts.*, users.name, users.profile_image
        FROM posts
        LEFT JOIN users ON posts.user_id = users.id
    """

    if keyword and category:
        like_keyword = f"%{keyword}%"
        if category == 'title':
            base_sql += " WHERE posts.title LIKE %s"
            cursor.execute(base_sql + " ORDER BY posts.created_at DESC", (like_keyword,))
        elif category == 'content':
            base_sql += " WHERE posts.content LIKE %s"
            cursor.execute(base_sql + " ORDER BY posts.created_at DESC", (like_keyword,))
        else:  # 제목 + 내용
            base_sql += " WHERE posts.title LIKE %s OR posts.content LIKE %s"
            cursor.execute(base_sql + " ORDER BY posts.created_at DESC", (like_keyword, like_keyword))
    else:
        cursor.execute(base_sql + " ORDER BY posts.created_at DESC")

    posts = cursor.fetchall()
    return render_template('index.html', posts=posts, keyword=keyword, category=category)


# 글 작성 페이지
@app.route('/create', methods=['GET'])
def create_form():
    return render_template('create.html')

# 글 작성 처리 
@app.route('/create', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        flash("로그인 후 작성 가능합니다.")
        return redirect('/login')

    title = request.form['title']
    content = request.form['content']
    user_id = session['user_id']

    file = request.files.get('file')
    filename = None

    if file and file.filename != '':
        filename = secure_filename(file.filename)

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    cursor = db.cursor()
    sql = """
        INSERT INTO posts (title, content, user_id, file_path)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(sql, (title, content, user_id, filename))  
    db.commit()

    return redirect('/')

# 글 상세 보기
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    cursor = db.cursor()
    sql = """
        SELECT posts.*, users.name, users.profile_image
        FROM posts
        LEFT JOIN users ON posts.user_id = users.id
        WHERE posts.id = %s
    """
    cursor.execute(sql, (post_id,))
    post = cursor.fetchone()

    if not post:
        flash("게시글이 존재하지 않습니다.")
        return redirect('/')

    if post['is_private'] and not session.get(f'pw_verified_{post_id}'):
        return redirect(f'/check_password/{post_id}/view')

    return render_template('view.html', post=post)

# 글 수정 페이지(GET)
@app.route('/update/<int:post_id>', methods=['GET'])
def update_form(post_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    return render_template('update.html', post=post)

# 글 수정 처리 (POST)
@app.route('/update/<int:post_id>', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    content = request.form['content']

    cursor = db.cursor()
    sql = "UPDATE posts SET title = %s, content = %s WHERE id = %s"
    cursor.execute(sql, (title, content, post_id))
    db.commit()

    return redirect(f'/post/{post_id}')

# 글 삭제
@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    cursor = db.cursor()
    sql = "DELETE FROM posts WHERE id = %s"
    cursor.execute(sql, (post_id,))
    db.commit()
    return redirect('/')

#회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        school = request.form['school']
        birthday = request.form['birthday']
        hashed_pw = generate_password_hash(password)

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("이미 존재하는 아이디입니다.")
            return redirect('/register')

        birth_date = datetime.strptime(birthday, '%Y-%m-%d')
        age = datetime.now().year - birth_date.year - ((datetime.now().month, datetime.now().day) < (birth_date.month, birth_date.day))

        try:
            sql = "INSERT INTO users (username, password, name, school, birthday, age) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (username, hashed_pw, name, school, birthday, age))
            db.commit()
            flash("회원가입이 완료되었습니다.")
            return redirect('/login')
        except Exception as e:
            flash(f"회원가입 중 오류가 발생했습니다: {e}")
            return redirect('/register')

    return render_template('register.html')

#로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("로그인에 성공했습니다.")
            return redirect('/') 
        else:
            flash("아이디 또는 비밀번호가 틀렸습니다.")
            return redirect('/login') 

    return render_template('login.html')

#로그아웃
@app.route('/logout')
def logout():
    session.clear()
    flash("로그아웃되었습니다.")
    return redirect('/')

#게시물 비밀번호 확인
@app.route('/check_password/<int:post_id>/<action>', methods=['GET', 'POST'])
def check_password(post_id, action):
    cursor = db.cursor()
    cursor.execute("SELECT post_password FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    if not post:
        flash("게시글이 존재하지 않습니다.")
        return redirect('/')

    if request.method == 'POST':
        entered_pw = request.form['password']
        if post['post_password'] == entered_pw:
            session[f'pw_verified_{post_id}'] = True

            if action == 'view':
                return redirect(f'/post/{post_id}')
            elif action == 'update':
                return redirect(f'/update/{post_id}')
            elif action == 'delete':
                return redirect(f'/delete/{post_id}')
        else:
            flash("비밀번호가 틀렸습니다.")
            return redirect(request.url)

    return render_template('confirm.html', post_id=post_id, action=action)

#프로필
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect('/login')

    user_id = session['user_id']
    cursor = db.cursor()
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()

    return render_template('profile.html', user=user)

#프로필 수정 
@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect('/login')

    user_id = session['user_id']
    cursor = db.cursor()

    if request.method == 'POST':
        name = request.form['name']
        school = request.form['school']
        profile_image = request.files['profile_image']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        birthday = request.form['birthday']

        birth_date = datetime.strptime(birthday, '%Y-%m-%d')
        age = datetime.now().year - birth_date.year - ((datetime.now().month, datetime.now().day) < (birth_date.month, birth_date.day))

        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], current_password):
            if new_password and new_password == confirm_password:
                hashed_pw = generate_password_hash(new_password)
            else:
                flash("새 비밀번호와 비밀번호 확인이 일치하지 않습니다.")
                return redirect('/profile/edit')

            image_path = None
            if profile_image and profile_image.filename != '':
                filename = secure_filename(profile_image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_image.save(image_path)

            if image_path:
                sql = "UPDATE users SET name = %s, school = %s, profile_image = %s, password = %s, birthday = %s, age = %s WHERE id = %s"
                cursor.execute(sql, (name, school, image_path, hashed_pw, birthday, age, user_id))
            else:
                sql = "UPDATE users SET name = %s, school = %s, password = %s, birthday = %s, age = %s WHERE id = %s"
                cursor.execute(sql, (name, school, hashed_pw, birthday, age, user_id))

            db.commit()
            flash("정보가 수정되었습니다.")
            return redirect('/profile')
        else:
            flash("현재 비밀번호가 올바르지 않습니다.")
            return redirect('/profile/edit')

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    return render_template('edit_profile.html', user=user)

#프로필 사진
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#다른 유저저의 프로필 보기
@app.route('/user/<int:user_id>')
def view_user_profile(user_id):
    cursor = db.cursor()
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("존재하지 않는 사용자입니다.")
        return redirect('/')

    return render_template('user_profile.html', user=user)

# 파일 다운로드
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

#아이디, 비밀번호 찾기
@app.route('/find_account', methods=['GET', 'POST'])
def find_account():
    if request.method == 'POST':
        name = request.form['name']

        if 'find_id' in request.form:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
            user = cursor.fetchone()

            if user:
                flash(f"아이디는 {user['username']} 입니다.")
                return redirect('/login')
            else:
                flash("등록된 이름이 없습니다.")
                return redirect('/find_account')

        elif 'find_password' in request.form:
            username = request.form['username']
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE name = %s AND username = %s", (name, username))
            user = cursor.fetchone()

            if user:
                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                hashed_pw = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_pw, user['id']))
                db.commit()

                flash(f"새 비밀번호는 {new_password} 입니다.")
                return redirect('/login')
            else:
                flash("이름과 아이디가 일치하지 않습니다.")
                return redirect('/find_account')

    return render_template('find_account.html')

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)
