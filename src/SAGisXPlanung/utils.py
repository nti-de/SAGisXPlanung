import asyncio
import logging
import os
from urllib.parse import urlparse

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt import QtGui
from qgis.gui import QgsLayerTreeViewIndicator
from qgis.utils import iface

from SAGisXPlanung import Session, Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.data_types import BP_VeraenderungssperreDaten
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich, BP_Objekt
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung, BP_KomplexeSondernutzung, \
    BP_KomplexeZweckbestNebenanlagen
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze, BP_BauLinie, \
    BP_BesondererNutzungszweckFlaeche, BP_NebenanlagenFlaeche
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.data_types import BP_KomplexeZweckbestSpielSportanlage, \
    BP_KomplexeZweckbestGemeinbedarf
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.feature_types import BP_GemeinbedarfsFlaeche, \
    BP_SpielSportanlagenFlaeche
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.data_types import BP_KomplexeZweckbestGruen, \
    BP_KomplexeZweckbestLandwirtschaft, BP_KomplexeZweckbestWald
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.feature_types import BP_GruenFlaeche, \
    BP_LandwirtschaftsFlaeche, BP_WaldFlaeche
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung, \
    BP_SchutzPflegeEntwicklungsFlaeche
from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_FlaecheOhneFestsetzung, BP_Wegerecht, \
    BP_NutzungsartenGrenze, BP_GenerischesObjekt
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.data_types import BP_KomplexeZweckbestVerEntsorgung
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.feature_types import BP_VerEntsorgung
from SAGisXPlanung.BPlan.BP_Verkehr.feature_types import BP_StrassenVerkehrsFlaeche, BP_StrassenbegrenzungsLinie, \
    BP_VerkehrsflaecheBesondererZweckbestimmung, BP_BereichOhneEinAusfahrtLinie, BP_EinfahrtPunkt
from SAGisXPlanung.BPlan.BP_Wasser.feature_types import BP_GewaesserFlaeche
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan, FP_Bereich, FP_Objekt
from SAGisXPlanung.FPlan.FP_Bebauung.data_types import FP_KomplexeSondernutzung
from SAGisXPlanung.FPlan.FP_Bebauung.feature_types import FP_BebauungsFlaeche
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.data_types import FP_KomplexeZweckbestGemeinbedarf, \
    FP_KomplexeZweckbestSpielSportanlage
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.feature_types import FP_Gemeinbedarf, FP_SpielSportanlage
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.data_types import FP_KomplexeZweckbestGruen, \
    FP_KomplexeZweckbestLandwirtschaft, FP_KomplexeZweckbestWald
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.feature_types import FP_Gruen, FP_Landwirtschaft, FP_WaldFlaeche
from SAGisXPlanung.FPlan.FP_Sonstiges.feature_types import FP_GenerischesObjekt
from SAGisXPlanung.FPlan.FP_Verkehr.feature_types import FP_Strassenverkehr
from SAGisXPlanung.FPlan.FP_Wasser.feature_types import FP_Gewaesser
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Plan, LP_Bereich
from SAGisXPlanung.RPlan.RP_Basisobjekte.feature_types import RP_Bereich, RP_Plan
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen import SO_Schienenverkehrsrecht, SO_Denkmalschutzrecht
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.data_types import SO_KomplexeZweckbestStrassenverkehr, \
    SO_KomplexeFestlegungGewaesser
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.feature_types import SO_Strassenverkehr, SO_Gewaesser, \
    SO_Wasserwirtschaft, SO_Luftverkehrsrecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete import SO_SchutzgebietWasserrecht
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt, XP_PPO, XP_PTO, \
    XP_Nutzungsschablone
from SAGisXPlanung.XPlan.data_types import (XP_SpezExterneReferenz, XP_ExterneReferenz, XP_VerfahrensMerkmal,
                                            XP_Gemeinde,
                                            XP_Plangeber, XP_GesetzlicheGrundlage, XP_SPEMassnahmenDaten,
                                            XP_Hoehenangabe, XP_VerbundenerPlan)
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.XPlan.simple_depth import XP_SimpleGeometry

logger = logging.getLogger(__name__)

CLASSES = {
    'XP_Plan': XP_Plan,
    'BP_Plan': BP_Plan,
    'FP_Plan': FP_Plan,
    'RP_Plan': RP_Plan,
    'LP_Plan': LP_Plan,
    'XP_Bereich': XP_Bereich,
    'FP_Bereich': FP_Bereich,
    'BP_Bereich': BP_Bereich,
    'RP_Bereich': RP_Bereich,
    'LP_Bereich': LP_Bereich,
    'XP_VerbundenerPlan': XP_VerbundenerPlan,

    'XP_Objekt': XP_Objekt,
    'XP_ExterneReferenz': XP_ExterneReferenz,
    'XP_Gemeinde': XP_Gemeinde,
    'XP_Plangeber': XP_Plangeber,
    'XP_GesetzlicheGrundlage': XP_GesetzlicheGrundlage,
    'XP_VerfahrensMerkmal': XP_VerfahrensMerkmal,
    'XP_SpezExterneReferenz': XP_SpezExterneReferenz,
    'XP_SPEMassnahmenDaten': XP_SPEMassnahmenDaten,
    'XP_AbstraktesPraesentationsobjekt': XP_AbstraktesPraesentationsobjekt,
    'XP_PPO': XP_PPO,
    'XP_PTO': XP_PTO,
    'XP_Nutzungsschablone': XP_Nutzungsschablone,
    'XP_Hoehenangabe': XP_Hoehenangabe,
    'XP_SimpleGeometry': XP_SimpleGeometry,

    'BP_Objekt': BP_Objekt,
    'BP_GenerischesObjekt': BP_GenerischesObjekt,
    'BP_FlaecheOhneFestsetzung': BP_FlaecheOhneFestsetzung,
    'BP_BesondererNutzungszweckFlaeche': BP_BesondererNutzungszweckFlaeche,
    'BP_GemeinbedarfsFlaeche': BP_GemeinbedarfsFlaeche,
    'BP_SpielSportanlagenFlaeche': BP_SpielSportanlagenFlaeche,
    'BP_GruenFlaeche': BP_GruenFlaeche,
    'BP_LandwirtschaftsFlaeche': BP_LandwirtschaftsFlaeche,
    'BP_WaldFlaeche': BP_WaldFlaeche,
    'BP_StrassenVerkehrsFlaeche': BP_StrassenVerkehrsFlaeche,
    'BP_VerkehrsflaecheBesondererZweckbestimmung': BP_VerkehrsflaecheBesondererZweckbestimmung,
    'BP_StrassenbegrenzungsLinie': BP_StrassenbegrenzungsLinie,
    'BP_GewaesserFlaeche': BP_GewaesserFlaeche,
    'BP_VerEntsorgung': BP_VerEntsorgung,
    'BP_AnpflanzungBindungErhaltung': BP_AnpflanzungBindungErhaltung,
    'BP_SchutzPflegeEntwicklungsFlaeche': BP_SchutzPflegeEntwicklungsFlaeche,
    'BP_Wegerecht': BP_Wegerecht,
    'BP_BaugebietsTeilFlaeche': BP_BaugebietsTeilFlaeche,
    'BP_BauGrenze': BP_BauGrenze,
    'BP_BauLinie': BP_BauLinie,
    'BP_Dachgestaltung': BP_Dachgestaltung,
    'BP_KomplexeZweckbestGruen': BP_KomplexeZweckbestGruen,
    'BP_KomplexeZweckbestSpielSportanlage': BP_KomplexeZweckbestSpielSportanlage,
    'BP_KomplexeZweckbestGemeinbedarf': BP_KomplexeZweckbestGemeinbedarf,
    'BP_KomplexeZweckbestLandwirtschaft': BP_KomplexeZweckbestLandwirtschaft,
    'BP_KomplexeZweckbestWald': BP_KomplexeZweckbestWald,
    'BP_KomplexeZweckbestVerEntsorgung': BP_KomplexeZweckbestVerEntsorgung,
    'BP_KomplexeZweckbestNebenanlagen': BP_KomplexeZweckbestNebenanlagen,
    'BP_KomplexeSondernutzung': BP_KomplexeSondernutzung,
    'BP_VeraenderungssperreDaten': BP_VeraenderungssperreDaten,
    'BP_NutzungsartenGrenze': BP_NutzungsartenGrenze,
    'BP_BereichOhneEinAusfahrtLinie': BP_BereichOhneEinAusfahrtLinie,
    'BP_EinfahrtPunkt': BP_EinfahrtPunkt,
    'BP_NebenanlagenFlaeche': BP_NebenanlagenFlaeche,

    'FP_Objekt': FP_Objekt,
    'FP_GenerischesObjekt': FP_GenerischesObjekt,
    'FP_BebauungsFlaeche': FP_BebauungsFlaeche,
    'FP_KomplexeSondernutzung': FP_KomplexeSondernutzung,
    'FP_Gemeinbedarf': FP_Gemeinbedarf,
    'FP_SpielSportanlage': FP_SpielSportanlage,
    'FP_Gruen': FP_Gruen,
    'FP_Landwirtschaft': FP_Landwirtschaft,
    'FP_WaldFlaeche': FP_WaldFlaeche,
    'FP_Strassenverkehr': FP_Strassenverkehr,
    'FP_Gewaesser': FP_Gewaesser,
    'FP_KomplexeZweckbestGemeinbedarf': FP_KomplexeZweckbestGemeinbedarf,
    'FP_KomplexeZweckbestSpielSportanlage': FP_KomplexeZweckbestSpielSportanlage,
    'FP_KomplexeZweckbestGruen': FP_KomplexeZweckbestGruen,
    'FP_KomplexeZweckbestLandwirtschaft': FP_KomplexeZweckbestLandwirtschaft,
    'FP_KomplexeZweckbestWald': FP_KomplexeZweckbestWald,

    'SO_Objekt': SO_Objekt,
    'SO_Schienenverkehrsrecht': SO_Schienenverkehrsrecht,
    'SO_Denkmalschutzrecht': SO_Denkmalschutzrecht,
    'SO_Luftverkehrsrecht': SO_Luftverkehrsrecht,
    'SO_SchutzgebietWasserrecht': SO_SchutzgebietWasserrecht,
    'SO_Wasserwirtschaft': SO_Wasserwirtschaft,
    'SO_Gewaesser': SO_Gewaesser,
    'SO_KomplexeFestlegungGewaesser': SO_KomplexeFestlegungGewaesser,
    'SO_Strassenverkehr': SO_Strassenverkehr,
    'SO_KomplexeZweckbestStrassenverkehr': SO_KomplexeZweckbestStrassenverkehr
}

PRE_FILLED_CLASSES = [
    XP_Gemeinde,
    XP_Plangeber,
    XP_GesetzlicheGrundlage
]

OBJECT_BASE_TYPES = [
    BP_Objekt, FP_Objekt, SO_Objekt
]


def save_to_db(obj, expire_on_commit=True):
    """ Fügt ein Objekt der Datenbank hinzu """
    try:
        with Session.begin() as session:
            session.expire_on_commit = expire_on_commit
            session.add(obj)
    except Exception as e:
        logger.exception(e)


async def save_to_db_async(obj):
    """ Async Version der save_to_db Methode"""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, save_to_db, obj)


def query_existing(obj):
    """
    Prüft ob ein gegebenes XPlanung-Objekt bereits in der Datenbank existiert.
    Falls ja, wird dieses zurückgegeben, ansonsten None
    """
    with Session.begin() as session:
        session.expire_on_commit = False
        objects_from_db = session.query(obj.__class__).all()
        obj_from_db = next((x for x in objects_from_db if x == obj), None)
    return obj_from_db


def createXPlanungIndicators():
    xp_indicator = QgsLayerTreeViewIndicator(iface.layerTreeView())
    xp_indicator.setToolTip('Diese Gruppe stellt ein XPlanung konform erfasstes Planwerk dar.')
    xp_indicator.setIcon(QtGui.QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                  'gui/resources/xplanung_icon.png'))))
    reload_indicator = QgsLayerTreeViewIndicator(iface.layerTreeView())
    reload_indicator.setToolTip('Planwerk aktualisieren')
    reload_indicator.setIcon(QtGui.QIcon(':/images/themes/default/mActionRefresh.svg'))

    return xp_indicator, reload_indicator


def confirmObjectDeletion(obj) -> bool:
    """
    Generiert eine MessageBox zur Bestätigung des Löschens eines beliebigen XPlanung-Objekts.
    Überprüft dabei ob abhängige Objekte bestehen.

    Returns
    -------
    bool:
        True, wenn Löschen bestätigt wurde;
        False, wenn Vorgang abgebrochen wurde
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)

    has_dependencies = False
    for rel in obj.__class__.relationships():
        if getattr(obj, rel[0]):
            has_dependencies = True
            break
    if not has_dependencies:
        msg.setText(f"Wollen Sie das Objekt unwideruflich löschen?"
                    f"<ul><li>ID: {obj.id} </li>"
                    f"<li> Objektklasse: <code>{obj.__class__.__name__}</code> </li></ul>")
    else:
        msg.setText(f"Objekt besitzt andere abhängige Objekte. Trotzdem Löschen?"
                    f"<ul><li>ID: {obj.id} </li>"
                    f"<li> Objektklasse: <code>{obj.__class__.__name__}</code> </li></ul>")
    msg.setWindowTitle("Löschvorgang bestätigen")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    msg.setDefaultButton(QMessageBox.Cancel)
    ret = msg.exec_()
    if ret == QMessageBox.Cancel:
        return False

    return True


def full_version_required_warning():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(f"Diese Funktion ist nur in der Vollversion verfügbar."
                f"<br>"
                f"Bei Interesse an der Vollversion, wenden Sie sich an <a href='"'mailto:info-de@nti.biz'"'>info-de@nti.biz</a>.")
    msg.setWindowTitle("Funktion nicht verfügbar.")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setDefaultButton(QMessageBox.Ok)
    msg.exec_()


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
