---
hide:
  - navigation
---

<div class="hero" markdown>

# SAGis XPlanung

<b>QGIS-Erweiterung zur Erfassung und Verwaltung von XPlanGML-Dokumenten</b>

SAGis XPlanung unterstützt die standardkonforme Erstellung, Bearbeitung, Validierung und Verwaltung von Flächennutzungs-, Bebauungs-, Landschafts- und Raumordnungsplänen direkt in QGIS.

<p>
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

[Jetzt starten](setup/index.md){ .md-button .md-button--primary }
[:simple-qgis: Plugin herunterladen](https://plugins.qgis.org/plugins/SAGisXPlanung/){ .md-button }

## Warum SAGis XPlanung?

<div class="grid cards" markdown>

-   :material-map-outline:{ .lg .middle }

    **XPlanung-konforme Datenerfassung**

    ---

    Erstellen und verwalten Sie Planwerke standardkonform innerhalb Ihrer bestehenden QGIS-Umgebung.

-   :material-database-import-outline:{ .lg .middle }

    **Import & Export von XPlanGML**

    ---

    Nahtloser Austausch bestehender Datensätze über standardisierte Schnittstellen.

-   :material-check-decagram:{ .lg .middle }

    **Validierung & Geometrieprüfung**

    ---

    Sicherstellung von Datenqualität und Standardkonformität während der Bearbeitung.

-   :material-palette-outline:{ .lg .middle }

    **PlanZV-konforme Visualisierung**

    ---

    Intuitive Darstellung von Planinhalten gemäß geltender Standards.

</div>

[:material-web: Mehr erfahren...](https://www.nti-group.com/de/produkte/sagis-loesungen/sagis-xplanung/){ .md-button }

---

## Erste Schritte

<div class="grid cards" markdown>

-   :material-database-cog:{ .lg .middle }

    **Installation**

    ---

    Schritt-für-Schritt Anleitung zur Installation und Einrichtung.

    [:octicons-arrow-right-24: Installation](setup/index.md)

-   :material-map-plus:{ .lg .middle }

    **Ersten XPlan erfassen**

    ---

    Erstellen Sie Ihren ersten standardkonformen Plan in wenigen Schritten.

    [:octicons-arrow-right-24: Plan erstellen](new-plan.md)

-   :material-database-import:{ .lg .middle }

    **XPlanGML importieren**

    ---

    Übernehmen Sie bestehende Planwerke direkt in SAGis XPlanung.

    [:octicons-arrow-right-24: Import starten](plan-import.md)

</div>

---

## Erweiterte Funktionen

<div class="grid cards" markdown>

-   [**Planinhalte hinzufügen**](add-plancontent.md)

    ---

    Vollständige Erfassung raumbezogener Festsetzungen.

-   [**Geometrieprüfung**](elements/plan-details.md#geometrieprufung)

    ---

    Automatische Validierung geometrischer Anforderungen.

-   [**XPlanGML Export**](plan-export.md)

    ---

    Standardisierte Ausgabe Ihrer Planwerke.

-   [**Planinhalte bearbeiten**](elements/plan-details.md#bearbeiten-von-sachdaten)

    ---

    Flexible Bearbeitung bestehender Datensätze.

</div>

---

## Versionen im Überblick

| Funktion | Community-Version | Vollversion |
|----------|------------------|-------------|
| Teilvektorielle Erfassung | :heavy_check_mark: | :heavy_check_mark: |
| Import von XPlanGML | :heavy_check_mark: | :heavy_check_mark: |
| Visualisierung gemäß PlanZV | :heavy_check_mark: | :heavy_check_mark: |
| Export von XPlanGML | Eingeschränkt | :heavy_check_mark: |
| Bearbeitung von Attributen | Eingeschränkt | :heavy_check_mark: |
| Vollvektorielle Erfassung |  | :heavy_check_mark: |
| Benutzerdefinierte Symbolisierung |  | :heavy_check_mark: |
| Tabellen-Import (Excel) |  | :heavy_check_mark: |

Die Community-Version ist kostenlos über das QGIS Plugin Repository verfügbar.


[:simple-qgis: Zum QGIS-Repository](https://plugins.qgis.org/plugins/SAGisXPlanung/){ .md-button }
[:material-github: Zum GitHub-Repository](https://github.com/nti-de/SAGisXPlanung){ .md-button }
