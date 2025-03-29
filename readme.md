
## Flask 기반 게시판 프로젝트

Flask와 MySQL을 활용하여 구현한 웹 게시판 프로젝트입니다.  
회원가입, 로그인, 글 작성/수정/삭제, 비밀글, 파일 업/다운로드, 프로필 기능까지 포함된 실전형 CRUD 웹 서비스입니다.

---

## 🧩 주요 기능

- 게시글 작성 / 수정 / 삭제
- 게시글 검색 (제목, 내용, 제목+내용)
- 비밀글 설정 및 비밀번호 인증
- 파일 업로드 & 다운로드
- 회원가입 (이름, 학교, 생일 입력 포함)
- 로그인 / 로그아웃
- 내 프로필 확인 및 정보 수정
- 다른 회원 프로필 조회
- 프로필 이미지 업로드 및 출력
- 아이디 / 비밀번호 찾기 기능

---

## ⚙️ 실행 방법

1. **패키지 설치**

```bash
pip install flask pymysql werkzeug
```

2. **MySQL 설정**

```sql
CREATE DATABASE board_db;
```

** `app.py` 내부의 MySQL 접속 정보(host/user/password 등)는 본인 환경에 맞게 수정 필요

3. **프로젝트 실행**

```bash
python app.py
```

4. **웹 접속**

```
http://localhost:5000/
```

---

## 💡 내가 공부한 주요 내용

이 프로젝트를 통해 다음과 같은 내용을 집중적으로 학습하고 실습했습니다:

### 📁 Flask 핵심

- `render_template`, `request`, `redirect`, `session`, `flash` 사용법
- `request.form`, `request.files` 활용
- `url_for()`로 URL 생성 및 경로 관리
- RESTful 방식의 라우팅 처리 (`/post/<id>`, `/user/<id>` 등)

### 🛠️ MySQL 연동

- `pymysql`을 활용한 MySQL 접속
- `cursor.execute()`, `fetchone()`, `fetchall()` 사용
- SQL문 직접 작성 (ORM 없이)

### 🔐 보안

- `werkzeug.security`의 `generate_password_hash`, `check_password_hash`로 비밀번호 암호화
- `secure_filename()`으로 업로드된 파일 이름 안전 처리
- `session`을 통한 로그인 상태 유지

### 🎨 HTML & Jinja2

- Jinja2 문법(`{{ }}`, `{% if %}`)을 사용해 동적 템플릿 구성
- 조건부 렌더링, 반복문 사용하여 게시글 리스트 출력

### 📂 파일 업로드 & 다운로드

- `request.files.get()`을 통한 파일 수신
- `send_from_directory()`로 서버 파일 다운로드 지원
