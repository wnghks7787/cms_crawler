docker_hub_library 사용법

docker_puller.cpp: 크롤링된 version 파일을 통해 도커를 설치하는 코드
docker_version_crawler.sh: 도커에 존재하는 버전을 크롤링하는 쉘스크립트
    - ./docker_hub_library_version에 파일 저장
    - docker_hub_library.csv에 긁어올 라이브러리 저장

## 시작하기 앞서
파이썬을 이용하므로 Miniconda 설치를 준비해주어야 한다.

## 간단 사용 설명
docker images가 존재하지 않는다면, docker_version_crawler.sh를 이용하여 다운로드 가능한 CMS 버전을 먼저 체크해준 뒤, docker_puller.cpp 코드를 통해 도커 이미지들을 다운로드한다.    
docker images가 존재하고 compose_files가 존재하지 않는다면, compose_builder.py를 통해 compsoe_files를 만들어준다.   
compose_files도 존재한다면 main.py를 통해 대규모로 docker up/down을 진행할 수 있다. 이 때 main.py를 실행시키면 assets를 다운로드 받을 수 있게 된다.     
이 외에도 대규모 테스팅(wasabo, versionseek 등)을 위해서는 compose_files가 반드시 있어야 한다.

## 폴더 구조
폴더는 다음과 같이 나누어진다.
1. Docker Images를 다운로드 받는 폴더
2. Docker Images를 프로세스 하는 폴더
3. 각종 Fingerprint에 관련된 폴더
4. Resources 폴더


### Docker_Image_Puller
이 폴더는 Docker Images를 다운로드 하는 코드가 들어있는 폴더이다.
```docker_version_crawler.sh``` 파일을 통해 저장할 docker images의 버전들을 가져온다. 이 정보들은 ```resources/docker_hub_library.csv``` 에 존재하는 파일 정보를 읽어온 뒤, 해당하는 버전 정보들을 가지고 오게 된다. 가져온 정보는 ```resources/docker_hub_library_version```에 저장된다.  
```docker_puller.cpp``` 코드는 위에서 얻어진 정보를 읽어온 뒤, 실제로 docker_pull을 수행하는 부분이다. 두 시간에 80개씩 다운로드 할 수 있도록 설정되어있다. 이는 도커 허브 정책에 의한 것으로, 정책이 변경되거나 이 부분을 변경하면 완전히 다운로드되지 않을 수 있으므로 잘 확인하고 충분한 시간을 확보하고 실행하는 것이 좋다.

### Docker_compose_Builder
이 폴더는 다운로드된 Docker Images를 처리하는 폴더이다. 
```tools.py``` 의 경우, 각종 사용 툴이 들어있다.    
```crawl_fingerprints.py``` 코드는 만들어진 웹페이지의 에셋(JS, CSS, 이미지파일 등)을 다운로드 하는데 사용한다.

#### Initial_page_builder
이곳의 ```main.py``` 에서 ```crawl_fingerprints.py``` 코드를 이용하여 에셋과 http, html 등을 받아온다.  
```mediawiki``` 파일은 기존 방식과 달라 사용하지 않는다. (박상아 학생에게 문의) 
```compose_builder.py``` 파일을 통해 ```compose_file_autobuilder.py``` 코드에 접근한다. 즉, ```python compose_builder.py``` 를 사용하면 ```compose_fuiles``` 폴더 안에 ```docker-compose```를 하기 위한 준비가 완료된다.    
포트는 10000번부터 할당한다.    

다시 말해, 우선 ```compose_builder.py```를 실행시켜 ```compose_files```를 생성해주어야 한다. 이후, 생성된 ```compose.yml``` 파일들은 ```main.py```를 실행시키면 자동으로 docker compose를 수행해줄 것이다. 이렇게 만들어진 파일들은 ```fingerprintable_file``` 이라는 이름으로 저장된다. 

이 때, ```initial_page_builder.sh``` 를 호출하게 되는데, 이는 여러 CMS들의 초기설정을 진행하기 위함이다. 이 쉘코드는 wordpress의 경우에는 자체적으로 curl 을 사용하여 초기설정을 진행하지만, 그 외(Joomla, Drupal, Mediawiki 등)은 playwright을 통해 설정을 건너뛰어 주어야 한다.   
이를 위해 ```playwrigiht_builder``` 가 존재하며, 만약 필요한 autobuilder가 있다면 여기 추가해주면 된다.


### Fingerprinte
이 폴더는 각종 fingerprinting rules가 들어있는 폴더이다.

```http_fingerprinter.py```, ```html_fingerprinter.py```는 각각 http header, html을 토대로 버전별 차이점을 생성해낸다.
```resource_json_builder.py```의 경우, 각 버전별로 가지고 있는 리소스를 hash 형태로 변환하여 ```fingerprint_json``` 폴더에 저장한다. 이는 동 파일 안에 있는 ```resource_fingerprint.py```를 통해 버전별 diff를 생성해낸다.

### Resources
이 폴더는 실행에 필요한 여러 리소스를 모아두는 폴더이다.