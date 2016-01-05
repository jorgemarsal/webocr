from webocr.tasks import create_service


if __name__ == "__main__":
    service = {
        "url": "http://github.com/jorgemarsal/hello-node"
    }
    conf = {}
    create_service(service, conf)
