# AI Gallery

AI Gallery는 사진을 공유할 수 있는 SNS 스타일의 웹 애플리케이션입니다. 사용자는 사진을 업로드하고, 이를 모두에게 공개하거나 친구들에게만 공개할 수 있습니다.

## 기능

- 사용자 등록 및 로그인
- 프로필 관리
- 이미지 업로드 및 관리
- 이미지 공개 설정(모두 공개/친구만 공개)
- 친구 관계 관리
- 이미지에 대한 댓글 및 좋아요 기능

## 기술 스택

- **백엔드**: Django, Django REST Framework
- **인증**: JWT (JSON Web Tokens)
- **문서화**: Swagger/OpenAPI
- **테스트**: pytest

## 설치 및 실행

### 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 데이터베이스 설정

```bash
python manage.py migrate
```

### 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 서버 실행

```bash
python manage.py runserver
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## 테스트 실행

```bash
pytest
``` 