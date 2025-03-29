# Makefile to build Lambda package or layer for Python 3.7

PYTHON_VERSION=3.9
IMAGE_NAME=lambda-py37-builder
CONTAINER_NAME=lambda-py37-container
REQUIREMENTS=requirements.txt
S3_BUCKET=rhr79-history-learning-lambda-code
OUTPUT_ZIP=lambda_package.zip

.PHONY: all clean layer function

layer: docker-build docker-copy-layer

install: layer upload

docker-build:
	docker build \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t $(IMAGE_NAME) -f Dockerfile .

rebuild:
	docker build --no-cache \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t $(IMAGE_NAME) -f Dockerfile .


docker-copy-layer:
	docker create --name $(CONTAINER_NAME) $(IMAGE_NAME)
	docker cp $(CONTAINER_NAME):/opt/app/lambda_package ./
	docker rm $(CONTAINER_NAME)
	mkdir -p layer/python
	mv lambda_package/* layer/python/
	cd layer && zip -r lxml_layer.zip python
	rm -rf layer/python

upload:
	aws s3 cp layer/lxml_layer.zip s3://$(S3_BUCKET)/lambda-layers/lxml_layer.zip
	zip paragraphs_lambda.zip *.py
	aws s3 cp paragraphs_lambda.zip s3://$(S3_BUCKET)/lambda-packages/paragraphs_lambda.zip
	aws lambda update-function-code --function-name "history-learning-paragraphs" \
		--s3-bucket $(S3_BUCKET) --s3-key "lambda-packages/paragraphs_lambda.zip"

clean:
	rm -rf lambda_package lambda_package.zip layer lxml_layer.zip
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi -f $(IMAGE_NAME) 2>/dev/null || true
