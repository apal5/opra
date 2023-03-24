### Steps to set-up
1. Git clone this repository
2. Clone [OPRA Dependencies](https://github.com/tomjmwang/opra_dependencies/tree/master/python_packages) to local machine's python libraries
3. Install all the python dependencies based on the requirement.txt file.
```
pip3 install -r requirements.txt
```

Docker build
Building base image
```
docker build -f docker/Dockerfile.base -t oprabase .
```
Running base image
```
docker run -ti --name obcontainer -p 8080:8080 oprabase .
```

```
docker build -f docker/Dockerfile -t opraimage .
```
Docker run
```
docker run -ti --name opra-container -p 8080:8080  opraimage .
```