docker_hub_library 사용법

docker_puller.cpp: 크롤링된 version 파일을 통해 도커를 설치하는 코드
docker_version_crawler.sh: 도커에 존재하는 버전을 크롤링하는 쉘스크립트
    - ./docker_hub_library_version에 파일 저장
    - docker_hub_library.csv에 긁어올 라이브러리 저장


## 폴더 구조
폴더는 다음과 같이 나누어진다.
1. Docker Images를 다운로드 받는 폴더
2. Docker Images를 프로세스 하는 폴더
3. 각종 Fingerprint에 관련된 폴더
4. Resources 폴더


### Docker_Image_Puller
이 폴더는 Docker Images를 다운로드 하는 코드가 들어있는 폴더이다.
```docker_version_crawler.sh``` 파일을 통해 저장할 docker images의 버전들을 가져온다.   
```resources/docker_hub_library.csv``` 에 존재하는 파일 정보를 읽어온 뒤, 해당하는 버전 정보들을 가지고 온다. 가져온 정보는 ```resources/docker_hub_library_version```에 저장된다.  
```docker_puller.cpp``` 코드는 위에서 얻어진 정보를 읽어온 뒤, 실제로 docker_pull을 수행하는 부분이다. 두 시간에 80개씩 다운로드 할 수 있도록 설정되어있다. 이는 도커 허브 정책에 의한 것으로, 정책이 변경되거나 이 부분을 변경하면 완전히 다운로드되지 않을 수 있으므로 잘 확인하고 충분한 시간을 확보하고 실행하는 것이 좋다.

### Docker_compose_Builder
이 폴더는 다운로드된 Docker Images를 처리하는 폴더이다.

### Fingerprinte
이 폴더는 각종 fingerprinting ruels가 들어있는 폴더이다.

### Resources
이 폴더는 실행에 필요한 여러 리소스를 모아두는 폴더이다.