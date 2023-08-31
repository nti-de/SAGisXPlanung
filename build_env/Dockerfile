FROM qgis/qgis:latest

LABEL Description="Docker Image with SAGis XPlanung dependencies"

WORKDIR /app
ENV DISPLAY=:99

COPY . .

RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install pytest pytest-cov pytest-qt pytest-mock pytest-asyncio nest-asyncio alembic

ENTRYPOINT ["sh"]