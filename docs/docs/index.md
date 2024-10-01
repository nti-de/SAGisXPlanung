# Anwendungsdokumentation SAGis XPlanung

SAGis XPlanung ist eine Erweiterung für die GIS-Software QGIS, die eine Erfassung und
Visualisierung von Bauleitplänen nach Richtlinien des Standards XPlanung ermöglicht

## Erste Schritte

<div class="grid cards" markdown>

-   :material-database-cog:{ .lg .middle } __Installation__

    ---

    Leitfaden zur Installation und Einrichtung von SAGis XPlanung

    [:octicons-arrow-right-24: Installation](#)


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