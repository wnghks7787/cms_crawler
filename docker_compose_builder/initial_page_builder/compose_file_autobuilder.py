import os, sys, pathlib

BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PARENT_DIR)

import tools

# 환경변수 설정
DEFAULT_FILE_PATH = os.environ.get("PWD") + "/compose_files"
DB_HOST = ''
DB_USER = ''
DB_PASSWORD = ''
DB_NAME = ''

def setENV(repo):
    global DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

    if repo == 'wordpress':
        DB_HOST = 'WORDPRESS_DB_HOST'
        DB_USER = 'WORDPRESS_DB_USER'
        DB_PASSWORD = 'WORDPRESS_DB_PASSWORD'
        DB_NAME = 'WORDPRESS_DB_NAME'
    elif repo == 'joomla':
        DB_HOST = 'JOOMLA_DB_HOST'
        DB_USER = 'JOOMLA_DB_USER'
        DB_PASSWORD = 'JOOMLA_DB_PASSWORD'
        DB_NAME = 'JOOMLA_DB_NAME'
    elif repo == 'drupal':
        DB_HOST = 'DRUPAL_DB_HOST'
        DB_USER = 'DRUPAL_DB_USER'
        DB_PASSWORD = 'DRUPAL_DB_PASSWORD'
        DB_NAME = 'DRUPAL_DB_NAME'
    elif repo == 'prestashop' or repo == 'qloapps_docker':
        DB_HOST = 'DB_SERVER'
        DB_USER = 'DB_USER'
        DB_PASSWORD = 'DB_PASSWD'
        DB_NAME = 'DB_NAME'

# ./compose_files/{repo}-{version}/ 기본 파일 생성.
# 예시: ./compose_files/wordpress-6.8.2/var/
def make_file_path(repo, version):
    # compose_files/{repo}-{version}/var/
    mysql_dir = f"{DEFAULT_FILE_PATH}/{repo}-{version}/var/lib/mysql"
    html_dir = f"{DEFAULT_FILE_PATH}/{repo}-{version}/var/www/html"
    
    pathlib.Path(mysql_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(html_dir).mkdir(parents=True, exist_ok=True)

    return mysql_dir, html_dir

# cms별로 필요로 하는 db 버전이 다르기 때문에 이를 맞춰줘야 함
def check_db_version(repo):
    db = ''
    version = ''

    if repo == 'wordpress':
        db = 'mariadb'
        version = '10.3'
    elif repo == 'joomla':
        db = 'mariadb'
        version = '10.4'
    elif repo == 'drupal':
        db = 'mariadb'
        version = '10.6'
    elif repo == 'prestashop':
        db = 'mariadb'
        version = '10.3'
    elif repo == 'qloapps_docker':
        db = 'mariadb'
        version = '10.3'

    return db, version

def compose_file_builder(repo, version, suffix=0):

    repo_name = repo.split('/')
    repo_name = repo_name[-1]

    db_name, db_version = check_db_version(repo_name)
    setENV(repo_name)

    # 파일 경로 생성
    mysql_dir, html_dir = make_file_path(repo_name, version)

    current_file_dir = f"{DEFAULT_FILE_PATH}/{repo_name}-{version}"
    current_file = f"{tools.sanitize_name(repo_name)}-{version}.yml"
    current_file_path = os.path.join(current_file_dir, current_file)

    # .yml 파일 생성
    pathlib.Path(current_file_path).touch(exist_ok=True)

    

    # .yml 파일에 내용 쓰기
    with open(current_file_path, "w") as f:
        f.write(
        f"""version: "3.9"

services:
  {repo_name}-{version}-db:
    image: {db_name}:{db_version}
    volumes:
      - {mysql_dir}
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: password_root
      MYSQL_DATABASE: db-{repo_name}-{version}
      MYSQL_USER: user
      MYSQL_PASSWORD: password_user
    ports:
      - "{3400+suffix}:3306"

  {repo_name}-{version}:
    depends_on:
      - {repo_name}-{version}-db
    image: {repo}:{version}
    volumes:
      - {html_dir}
    restart: always
    environment:
      {DB_HOST}: {repo_name}-{version}-db:3306
      {DB_USER}: user
      {DB_PASSWORD}: password_user
      {DB_NAME}: db-{repo_name}-{version}
    ports:
      - "{10000+suffix}:80"
"""
        )




# 테스트용
if __name__ == "__main__":
    compose_file_builder("webkul/qloapps_docker", "1.6.1", 1)