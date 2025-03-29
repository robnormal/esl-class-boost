FROM amazonlinux:latest

RUN yum -y update && \
    yum -y groupinstall "Development Tools" && \
    yum -y install gcc libxml2-devel libxslt-devel zip \
                   python3 python3-devel python3-pip

RUN python3 --version

# Create layer directory
WORKDIR /opt/app
COPY requirements.txt .
RUN mkdir -p lambda_package && \
    pip3 install -r requirements.txt -t lambda_package/

# Zip the layer
RUN zip -r lxml_layer.zip lambda_package
