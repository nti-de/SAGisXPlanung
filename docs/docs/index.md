<p align="center">
  <picture>
    <img alt="SAGis XPlanung" src="assets/icons/sagis_icon.png">
  </picture>
</p>

<h1 align="center">SAGis XPlanung</h1>

<p align="center">
  <strong>
    QGIS Erweiterung zur Erfassung und Verwaltung von XPlanGML-Dokumenten
  </strong>
</p>

<p align="center">
  <a href="https://github.com/nti-de/SAGisXPlanung/actions"><img
    src="https://github.com/nti-de/SAGisXPlanung/actions/workflows/main.yml/badge.svg"
    alt="Build"
  /></a>
  <a href="https://plugins.qgis.org/plugins/SAGisXPlanung/"><img
    src="https://img.shields.io/badge/dynamic/xml?url=https%3A%2F%2Fplugins.qgis.org%2Fplugins%2Fplugins.xml%3Fqgis%3D3.34&query=%2F%2Fpyqgis_plugin%5B%40name%3D'SAGis%20XPlanung'%5D%2Fdownloads&logo=qgis&logoColor=%23589632&label=QGIS%20Plugin%20Downloads&color=589632)"
    alt="Downloads"
  /></a>
  <a href="https://plugins.qgis.org/plugins/SAGisXPlanung/"><img
    src="https://img.shields.io/badge/dynamic/xml?url=https%3A%2F%2Fplugins.qgis.org%2Fplugins%2Fplugins.xml%3Fqgis%3D3.34&query=%2F%2Fpyqgis_plugin%5B%40name%3D'SAGis%20XPlanung'%5D%2F%40version&logo=qgis&logoColor=%23589632&label=QGIS%20Plugin%20Version&color=589632"
    alt="Version"
  /></a>
  <a href="https://plugins.qgis.org/plugins/SAGisXPlanung/"><img
    src="https://img.shields.io/badge/dynamic/xml?url=https%3A%2F%2Fplugins.qgis.org%2Fplugins%2Fplugins.xml%3Fqgis%3D3.34&query=round(%2F%2Fpyqgis_plugin%5B%40name%3D'SAGis%20XPlanung'%5D%2Faverage_vote%20*%20100)%20div%20100&suffix=%20%2F%205&logo=qgis&logoColor=%23589632&label=QGIS%20Stars&color=589632"
    alt="Rating"
  /></a>
</p>

<p align="center">
  <a href="https://www.nti-group.com/de/produkte/sagis-loesungen/sagis-xplanung/"><strong>Homepage</strong></a>
  &middot;
  <a href="https://plugins.qgis.org/plugins/SAGisXPlanung/"><strong>QGIS Plugin Repository</strong></a>
</p>

SAGis XPlanung ist eine Erweiterung für die GIS-Software [QGIS](https://www.qgis.org) zur [XPlanung](https://www.xleitstelle.de/xplanung/ueber_xplanung) - konformen 
Erfassung von Flächennutzungs-, Bebauungs-, Landschafts- und Raumordnungsplänen. 

![QGIS Screenshot](assets/screenshot_banner.png)

## Erste Schritte

<div class="grid cards" markdown>

-   :material-database-cog:{ .lg .middle } __Installation__

    ---

    Leitfaden zur Installation und Einrichtung von SAGis XPlanung

    [:octicons-arrow-right-24: Installation](setup/index.md)


-   :map:{ .lg .middle } __Ersten XPlan erfassen__

    ---

    Vorgehensweise zum Erstellen eines XPlanung konformen Datensatzes

    [:octicons-arrow-right-24: Plan erstellen](new-plan.md)

-   :material-database-import-outline:{ .lg .middle } __Import von XPlanGML-Dokumenten__

    ---

    Bestehende XPlanung konforme Datensätze importieren

    [:octicons-arrow-right-24: XPlanGML-Import](plan-import.md)

</div>

## Weitere Funktionen

<div class="grid cards" markdown>
-   [__Planinhalte hinzufügen__](add-plancontent.md)

    ---

    Erfassen von raumbezogenen Festsetzungen in einem Plan

-   [__Geometrieprüfung__](elements/plan-details.md#geometrieprufung)

    ---

    Validieren der Anforderungen an erfasste Geometrien im Standard XPlanung

-   [__Export von XPlanGML-Dokumenten__](plan-export.md)

    ---

    Erstellen von XPlanGML-Dateien aus erfassten XPlan-Datensätzen

- [__Planinhalte bearbeiten__](elements/plan-details.md#bearbeiten-von-sachdaten)

    ---

    Anpassen von Geometrie und Sachdaten bestehender Planinhalte
</div>

## Programmversionen

Die Anwendung wird in zwei verschiedenen Versionen zur Verfügung gestellt. 
Zum Überblick über die Funktionsunterschiede dient die folgende Tabelle:

|                                                             | Community-Version   | Vollversion        |
|-------------------------------------------------------------|---------------------|--------------------|
| Teilvektorielle Erfassung                                   | :heavy_check_mark:  | :heavy_check_mark: |
| Speichern externer Referenzen                               | :heavy_check_mark:  | :heavy_check_mark: |
| Import von XPlanGML-Dokumenten                              | :heavy_check_mark:  | :heavy_check_mark: |
| Visualisierung gemäß PlanZV                                 | :heavy_check_mark:  | :heavy_check_mark: |
| Export von XPlanGML-Dokumenten                              | [^abbr1]            | :heavy_check_mark: |
| Bearbeiten von XPlanung-Attributen                          | [^abbr1]            | :heavy_check_mark: |
| Erfassung neuer Planinhalte <br/>(vollvektorielle Erfassung) |                     | :heavy_check_mark: |
| Benutzerdefinierte Symbolisierung                           |                     | :heavy_check_mark: |
| Tabellen-Import (Excel)                                   |                     | :heavy_check_mark: |

Die Community-Version ist unter einer Open-Source Lizenz im Plugin-Verzeichnis vom QGIS zum 
[Download](setup/install.md#installation-aus-qgis-plugin-repository) verfügbar.


[^abbr1]: Nur für Basisobjekte möglich (teilvektorielle Erfassung)