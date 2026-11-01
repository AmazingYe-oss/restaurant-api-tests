FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
ARG MAVEN_PROXY_HOST
ARG MAVEN_PROXY_PORT=7890
RUN if [ -n "$MAVEN_PROXY_HOST" ]; then mkdir -p /root/.m2 && printf '<settings><proxies><proxy><id>build-proxy</id><active>true</active><protocol>http</protocol><host>%s</host><port>%s</port><nonProxyHosts>localhost|127.0.0.1</nonProxyHosts></proxy></proxies></settings>' "$MAVEN_PROXY_HOST" "$MAVEN_PROXY_PORT" > /root/.m2/settings.xml; fi
COPY src src
RUN --mount=type=cache,target=/root/.m2/repository mvn -B -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN sed -i 's|http://archive.ubuntu.com|https://archive.ubuntu.com|g; s|http://security.ubuntu.com|https://security.ubuntu.com|g' /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get -o Acquire::Retries=3 update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 appuser
COPY --from=build /workspace/target/reservation-api-*.jar app.jar
USER appuser
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar", "--spring.profiles.active=docker"]
