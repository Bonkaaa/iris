# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system utilities and build tools
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    git \
    wget \
    unzip \
    tar \
    ant \
    python3 \
    python3-pip \
    python3-dev \
    python-is-python3 \
    ca-certificates \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 2. Install OpenJDK versions (8, 11, 17)
RUN add-apt-repository ppa:openjdk-r/ppa \
    && apt-get update \
    && apt-get install -y openjdk-8-jdk openjdk-11-jdk openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 3. Install Maven versions (3.2.1, 3.5.0, 3.9.8) matching dep_configs.json
ENV MAVEN_DIR=/opt/maven
ARG MAVEN_VERSIONS="3.2.1 3.5.0 3.9.8"
RUN mkdir -p $MAVEN_DIR && \
    for version in $MAVEN_VERSIONS; do \
        wget https://archive.apache.org/dist/maven/maven-3/${version}/binaries/apache-maven-${version}-bin.tar.gz -P /tmp && \
        tar -xzf /tmp/apache-maven-${version}-bin.tar.gz -C $MAVEN_DIR && \
        rm /tmp/apache-maven-${version}-bin.tar.gz; \
    done

ENV MAVEN_HOME=$MAVEN_DIR/apache-maven-3.5.0
ENV PATH=$MAVEN_HOME/bin:$PATH

# 4. Install Gradle versions (6.8.2, 7.6.4, 8.9) matching dep_configs.json
ENV GRADLE_DIR=/opt/gradle
ARG GRADLE_VERSIONS="6.8.2 7.6.4 8.9"
RUN mkdir -p $GRADLE_DIR && \
    for version in $GRADLE_VERSIONS; do \
        wget -q https://services.gradle.org/distributions/gradle-${version}-bin.zip -O /tmp/gradle-${version}-bin.zip && \
        unzip -q /tmp/gradle-${version}-bin.zip -d $GRADLE_DIR && \
        rm /tmp/gradle-${version}-bin.zip; \
    done

ENV GRADLE_HOME=$GRADLE_DIR/gradle-6.8.2
ENV PATH=$GRADLE_HOME/bin:$PATH

# 5. Set up workspace and Python dependencies
WORKDIR /iris
COPY requirements.txt /iris/
RUN pip3 install --no-cache-dir -r requirements.txt

# 6. Download and install CodeQL Action Bundle v2.23.2 (with full qlpacks & java-queries v1.8.1)
RUN curl -L -o /tmp/codeql-bundle.tar.gz https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.23.2/codeql-bundle-linux64.tar.gz && \
    tar -xzf /tmp/codeql-bundle.tar.gz -C /iris/ && \
    rm -f /tmp/codeql-bundle.tar.gz

ENV CODEQL_DIR=/iris/codeql
ENV PATH=/iris/codeql:$PATH

# 7. Copy project code
COPY . /iris/

CMD ["/bin/bash"]
