# SAGis XPlanung

SAGis XPlanung ist eine Erweiterung für die GIS-Software QGIS zur [XPlanung](https://www.xleitstelle.de/xplanung/ueber_xplanung) - konformen 
Erfassung von Flächennutzungsplänen, Bebauungsplänen und Raumordnungsplänen. 

## Funktionen

- Digitale Erfassung von Planwerken der Bauleitplanung (teil- und vollvektorielle Erfassungsstrategie)
- Persistentes Speichern der Planinhalte in einer Datenbank
- Verknüpfung der räumlichen Planinhalte mit externen Referenzen
- Export des Austauschformats _XPlanGML_ (Version 5.3 und 6.0)
- Import von _XPlanGML_-Dokumenten 
- Visualisierung der räumlichen Informationen von Planwerken auf dem QGIS-Kartencanvas

> [!NOTE]  
> Die hier bereitgestellte Version besitzt nicht den vollen Funktionsumfang. Bitte beachten Sie die folgende Tabelle zur Gegenüberstellung der Versionen.

|                                                              | Community-Version  | Vollversion        |
|--------------------------------------------------------------|--------------------|--------------------|
| Teilvektorielle Erfassung                                    | :heavy_check_mark: | :heavy_check_mark: |
| Speichern externer Referenzen                                | :heavy_check_mark: | :heavy_check_mark: |
| Import von XPlanGML-Dokumenten                               | :heavy_check_mark: | :heavy_check_mark: |
| Visualisierung gemäß PlanZV                                  | :heavy_check_mark: | :heavy_check_mark: |
| Export von XPlanGML-Dokumenten                               | [^abbr1]           | :heavy_check_mark: |
| Bearbeiten von XPlanung-Attributen                           | [^abbr1]           | :heavy_check_mark: |
| Erfassung neuer Planinhalte <br/>(vollvektorielle Erfassung) |                    | :heavy_check_mark: |
[^abbr1]: Nur für Basisobjekte möglich (teilvektorielle Erfassung)


## Nutzung
    
### Software-Vorraussetzungen

- QGIS >= 3.22
- PostgreSQL >= 9.6 mit PostGIS 3.1

### Installation 

SAGis XPlanung kann über das QGIS-Plugin Repository heruntergeladen werden.

Für eine erfolgreiche Ausführung des Programms müssen zudem folgende Python-Komponenten installiert werden:
- SQLAlchemy==1.4.49 (:warning: Anwendung nicht kompatibel mit SQLAlchemy 2.0)
- GeoAlchemy2==0.12.5
- lxml==4.6.3
- shapely==2.0.0
- qasync==0.22.0
- asyncpg==0.26.0

<details><summary><b>Anleitung anzeigen</b></summary>

1. Suchen Sie das Installationsverzeichnis von QGIS (Zumeist `C:\OSGeo4W\` oder `C:\Program Files\QGIS 3.*'`)

2. Im Verzeichnis befindet sich die _OSGeo4W-Shell_ (Datei mit dem Namen `OSGeo4W.bat`). Starten Sie die _OSGeo4W-Shell_ und führen Sie den folgenden Befehl im sich öffnenden Programm aus:

    ```sh
    o4w_env & python3 -m pip install sqlalchemy==1.4.46 GeoAlchemy2 qasync shapely==2.0.0 lxml asyncpg
    ```

</details>

### Beispieldaten

> [!NOTE]  
> Zum Testen stellt die [Leitstelle XPlanung/XBau](https://xleitstelle.de) im folgenden Repository Testdaten im XPlanGML-Format zur Verfügung: https://bitbucket.org/geowerkstatt-hamburg/xplan-testdaten/src/master/

<details><summary><b>Visualisierung Beispielplan mit SAGis XPlanung</b></summary>
<div>
  <img style="height: auto" src="docs/toc.png" width="24%" /> 
  <img style="height: auto" src="docs/BPlan001_5-3.png" width="45%" />
</div>
</details>

