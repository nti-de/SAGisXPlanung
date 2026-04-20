import asyncio
import inspect
import logging
import os
import subprocess
import sys
from typing import Union, Type
from urllib.parse import urlparse

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt import QtGui
from qgis.gui import QgsLayerTreeViewIndicator
from qgis.utils import iface

from SAGisXPlanung import Session, Base
from SAGisXPlanung.BPlan.BP_Aufschuettung_Abgrabung_Bodenschaetze.feature_types import BP_AbgrabungsFlaeche, \
    BP_AufschuettungsFlaeche
from SAGisXPlanung.BPlan.BP_Basisobjekte.codelists import BP_SonstPlanArt, BP_Status
from SAGisXPlanung.BPlan.BP_Basisobjekte.data_types import BP_VeraenderungssperreDaten
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich, BP_Objekt, BP_TextAbschnitt
from SAGisXPlanung.BPlan.BP_Bebauung.codelists import BP_DetailArtDerBaulNutzung, BP_DetailDachform, \
    BP_DetailSondernutzung, BP_DetailZweckbestGemeinschaftsanlagen, BP_NutzungNichtUeberbaubGrundstFlaeche
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung, BP_KomplexeSondernutzung, \
    BP_KomplexeZweckbestNebenanlagen, BP_KomplexeZweckbestGemeinschaftsanlagen
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze, BP_BauLinie, \
    BP_BesondererNutzungszweckFlaeche, BP_NebenanlagenFlaeche, BP_UeberbaubareGrundstuecksFlaeche, \
    BP_NebenanlagenAusschlussFlaeche, BP_WohngebaeudeFlaeche, BP_GemeinschaftsanlagenFlaeche, \
    BP_NichtUeberbaubareGrundstuecksflaeche, BP_GebaeudeStellung, BP_AbstandsFlaeche
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.data_types import BP_KomplexeZweckbestSpielSportanlage, \
    BP_KomplexeZweckbestGemeinbedarf
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.feature_types import BP_GemeinbedarfsFlaeche, \
    BP_SpielSportanlagenFlaeche
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.data_types import BP_KomplexeZweckbestGruen, \
    BP_KomplexeZweckbestLandwirtschaft, BP_KomplexeZweckbestWald
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.feature_types import BP_GruenFlaeche, \
    BP_LandwirtschaftsFlaeche, BP_WaldFlaeche
from SAGisXPlanung.BPlan.BP_Laerm.data_types import BP_EmissionskontingentLaerm, BP_EmissionskontingentLaermGebiet, \
    BP_Richtungssektor
from SAGisXPlanung.BPlan.BP_Laerm.feature_types import BP_RichtungssektorGrenze, BP_ZusatzkontingentLaerm, \
    BP_ZusatzkontingentLaermFlaeche
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung, \
    BP_SchutzPflegeEntwicklungsFlaeche, BP_AusgleichsFlaeche, BP_AusgleichsMassnahme, BP_EingriffsBereich
from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_FlaecheOhneFestsetzung, BP_Wegerecht, \
    BP_NutzungsartenGrenze, BP_GenerischesObjekt, BP_KennzeichnungsFlaeche, BP_HoehenMass, BP_AbstandsMass
from SAGisXPlanung.BPlan.BP_Umwelt.feature_types import BP_Immissionsschutz, BP_TechnischeMassnahmenFlaeche
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.data_types import BP_KomplexeZweckbestVerEntsorgung
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.feature_types import BP_VerEntsorgung
from SAGisXPlanung.BPlan.BP_Verkehr.feature_types import BP_StrassenVerkehrsFlaeche, BP_StrassenbegrenzungsLinie, \
    BP_VerkehrsflaecheBesondererZweckbestimmung, BP_BereichOhneEinAusfahrtLinie, BP_EinfahrtPunkt, \
    BP_EinfahrtsbereichLinie
from SAGisXPlanung.BPlan.BP_Wasser.codelists import BP_DetailZweckbestWasserwirtschaft
from SAGisXPlanung.BPlan.BP_Wasser.feature_types import BP_GewaesserFlaeche, BP_WasserwirtschaftsFlaeche
from SAGisXPlanung.FPlan.FP_Aufschuettung_Abgrabung_Bodenschaetze.feature_types import FP_Abgrabung, FP_Aufschuettung
from SAGisXPlanung.FPlan.FP_Basisobjekte.codelists import FP_SonstPlanArt, FP_Status
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan, FP_Bereich, FP_Objekt, FP_TextAbschnitt
from SAGisXPlanung.FPlan.FP_Bebauung.codelists import FP_DetailArtDerBaulNutzung
from SAGisXPlanung.FPlan.FP_Bebauung.data_types import FP_KomplexeSondernutzung
from SAGisXPlanung.FPlan.FP_Bebauung.feature_types import FP_BebauungsFlaeche, FP_KeineZentrAbwasserBeseitigungFlaeche
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.codelists import FP_DetailZweckbestGemeinbedarf
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.data_types import FP_KomplexeZweckbestGemeinbedarf, \
    FP_KomplexeZweckbestSpielSportanlage
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.feature_types import FP_Gemeinbedarf, FP_SpielSportanlage
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.data_types import FP_KomplexeZweckbestGruen, \
    FP_KomplexeZweckbestLandwirtschaft, FP_KomplexeZweckbestWald
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.feature_types import FP_Gruen, FP_Landwirtschaft, FP_WaldFlaeche
from SAGisXPlanung.FPlan.FP_Naturschutz.feature_types import FP_SchutzPflegeEntwicklung, FP_AusgleichsFlaeche, \
    FP_AnpassungKlimawandel
from SAGisXPlanung.FPlan.FP_Sonstiges.codelists import XP_DetailTechnVorkehrungImmissionsschutz, \
    FP_DetailZweckbestimmungNachLandesrecht, FP_DetailMassnahmeKlimawandel
from SAGisXPlanung.FPlan.FP_Sonstiges.feature_types import FP_GenerischesObjekt, FP_Kennzeichnung, \
    FP_PrivilegiertesVorhaben, FP_Nutzungsbeschraenkung, FP_NutzungsbeschraenkungsFlaeche, FP_FlaecheOhneDarstellung, \
    FP_VorbehalteFlaeche, FP_UnverbindlicheVormerkung, FP_DarstellungNachLandesrecht, FP_TextlicheDarstellungsFlaeche, \
    FP_TextAbschnittFlaeche
from SAGisXPlanung.FPlan.FP_Ver_und_Entsorgung.codelists import FP_DetailZweckbestVerEntsorgung, \
    FP_ZentralerVersorgungsbereichAuspraegung
from SAGisXPlanung.FPlan.FP_Ver_und_Entsorgung.data_types import FP_KomplexeZweckbestVerEntsorgung
from SAGisXPlanung.FPlan.FP_Ver_und_Entsorgung.feature_types import FP_VerEntsorgung, FP_ZentralerVersorgungsbereich
from SAGisXPlanung.FPlan.FP_Verkehr.feature_types import FP_Strassenverkehr
from SAGisXPlanung.FPlan.FP_Wasser.feature_types import FP_Gewaesser, FP_Wasserwirtschaft
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Plan, LP_Bereich, LP_Objekt, LP_TextAbschnitt
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.data_types import LP_EingriffsregelungKomplex, \
    LP_TypBioVerbundKomplex
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.feature_types import LP_BiotopverbundBiotopvernetzung, \
    LP_Eingriffsregelung
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanungZEM.codelists import LP_BioVfBiotoptyp_BKompV, \
    LP_BioVfBiotoptyp_LandesKS, LP_BioVf_FFH_LRT
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanungZEM.data_types import LP_AdressatKomplex, \
    LP_BiologischeVielfaltKomplex, LP_BiologischeVielfaltTypKomplex, LP_BioVfBiotoptypKomplex, \
    LP_BioVfPflanzenArtKomplex, LP_BioVfTiereArtKomplex, LP_BodenKomplex, LP_ErholungKomplex, LP_KlimaKomplex, \
    LP_LandschaftsbildKomplex, LP_LuftKomplex, LP_NutzungseinschraenkungKomplex, LP_SchutzgutKomplex, LP_SPEKomplex, \
    LP_WasserKomplex, LP_ZielDimNatSchLaPflKomplex
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanungZEM.feature_types import LP_ZieleErfordernisseMassnahmen
from SAGisXPlanung.LPlan.LP_SchutzgebieteBestandteileNaturschutzrecht.codelists import LP_DetailGesetzlGeschBiotopLR
from SAGisXPlanung.LPlan.LP_SchutzgebieteBestandteileNaturschutzrecht.feature_types import \
    LP_SchutzBestimmterTeileVonNaturUndLandschaft
from SAGisXPlanung.LPlan.LP_Sonstiges.codelists import LP_ZweckbestimmungGenerischeObjekte
from SAGisXPlanung.LPlan.LP_Sonstiges.feature_types import LP_TextAbschnittObjekt, LP_GenerischesObjekt
from SAGisXPlanung.RPlan.RP_Basisobjekte.feature_types import RP_Bereich, RP_Plan, RP_TextAbschnitt
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte.feature_types import SO_TextAbschnitt
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen import SO_Schienenverkehrsrecht, SO_Denkmalschutzrecht
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.codelists import \
    SO_DetailKlassifizNachDenkmalschutzrecht, SO_DetailKlassifizNachSchienenverkehrsrecht, \
    SO_DetailKlassifizNachLuftverkehrsrecht, SO_DetailKlassifizNachSonstigemRecht, \
    SO_DetailKlassifizNachBodenschutzrecht, SO_DetailKlassifizBauverbot, SO_DetailKlassifizBaubeschraenkung, \
    SO_DetailKlassifizNachForstrecht, SO_SonstGebietsArt, SO_SonstRechtsstandGebietTyp
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.data_types import SO_KomplexeZweckbestStrassenverkehr, \
    SO_KomplexeFestlegungGewaesser
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.feature_types import SO_Strassenverkehr, SO_Gewaesser, \
    SO_Wasserwirtschaft, SO_Luftverkehrsrecht, SO_SonstigesRecht, SO_Strassenverkehrsrecht, SO_Wasserrecht, \
    SO_Bodenschutzrecht, SO_Bauverbotszone, SO_Baubeschraenkung, SO_Forstrecht, SO_Gebiet
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete import SO_SchutzgebietWasserrecht, SO_SchutzgebietSonstigesRecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.codelists import SO_DetailKlassifizSchutzgebietSonstRecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.feature_types import SO_SchutzgebietNaturschutzrecht
from SAGisXPlanung.SonstigePlanwerke.SO_Sonstiges.codelists import SO_DetailKlassifizGelaendemorphologie, \
    SO_SonstGrenzeTypen
from SAGisXPlanung.SonstigePlanwerke.SO_Sonstiges.feature_types import SO_Gelaendemorphologie, SO_Grenze
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt, XP_PPO, XP_PTO, \
    XP_Nutzungsschablone
from SAGisXPlanung.XPlan.XP_Raster.feature_types import XP_Rasterdarstellung
from SAGisXPlanung.XPlan.codelists import CodeListValue, XP_MimeTypes
from SAGisXPlanung.XPlan.data_types import (XP_SpezExterneReferenz, XP_ExterneReferenz, XP_VerfahrensMerkmal,
                                            XP_Gemeinde,
                                            XP_Plangeber, XP_GesetzlicheGrundlage, XP_SPEMassnahmenDaten,
                                            XP_Hoehenangabe, XP_VerbundenerPlan, XP_GenerAttribut, XP_DatumAttribut,
                                            XP_DoubleAttribut, XP_StringAttribut, XP_IntegerAttribut, XP_URLAttribut)
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt, XP_TextAbschnitt
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
    'XP_TextAbschnitt': XP_TextAbschnitt,
    'XP_Rasterdarstellung': XP_Rasterdarstellung,

    'BP_Objekt': BP_Objekt,
    'BP_GenerischesObjekt': BP_GenerischesObjekt,
    'BP_HoehenMass': BP_HoehenMass,
    'BP_FlaecheOhneFestsetzung': BP_FlaecheOhneFestsetzung,
    'BP_BesondererNutzungszweckFlaeche': BP_BesondererNutzungszweckFlaeche,
    'BP_AbstandsFlaeche': BP_AbstandsFlaeche,
    'BP_GemeinbedarfsFlaeche': BP_GemeinbedarfsFlaeche,
    'BP_SpielSportanlagenFlaeche': BP_SpielSportanlagenFlaeche,
    'BP_GemeinschaftsanlagenFlaeche': BP_GemeinschaftsanlagenFlaeche,
    'BP_NichtUeberbaubareGrundstuecksflaeche': BP_NichtUeberbaubareGrundstuecksflaeche,
    'BP_GruenFlaeche': BP_GruenFlaeche,
    'BP_LandwirtschaftsFlaeche': BP_LandwirtschaftsFlaeche,
    'BP_WaldFlaeche': BP_WaldFlaeche,
    'BP_StrassenVerkehrsFlaeche': BP_StrassenVerkehrsFlaeche,
    'BP_VerkehrsflaecheBesondererZweckbestimmung': BP_VerkehrsflaecheBesondererZweckbestimmung,
    'BP_StrassenbegrenzungsLinie': BP_StrassenbegrenzungsLinie,
    'BP_GewaesserFlaeche': BP_GewaesserFlaeche,
    'BP_VerEntsorgung': BP_VerEntsorgung,
    'BP_AnpflanzungBindungErhaltung': BP_AnpflanzungBindungErhaltung,
    'BP_AusgleichsFlaeche': BP_AusgleichsFlaeche,
    'BP_AusgleichsMassnahme': BP_AusgleichsMassnahme,
    'BP_EingriffsBereich': BP_EingriffsBereich,
    'BP_SchutzPflegeEntwicklungsFlaeche': BP_SchutzPflegeEntwicklungsFlaeche,
    'BP_Wegerecht': BP_Wegerecht,
    'BP_BaugebietsTeilFlaeche': BP_BaugebietsTeilFlaeche,
    'BP_BauGrenze': BP_BauGrenze,
    'BP_BauLinie': BP_BauLinie,
    'BP_GebaeudeStellung': BP_GebaeudeStellung,
    'BP_Dachgestaltung': BP_Dachgestaltung,
    'BP_KomplexeZweckbestGruen': BP_KomplexeZweckbestGruen,
    'BP_KomplexeZweckbestSpielSportanlage': BP_KomplexeZweckbestSpielSportanlage,
    'BP_KomplexeZweckbestGemeinbedarf': BP_KomplexeZweckbestGemeinbedarf,
    'BP_KomplexeZweckbestGemeinschaftsanlagen': BP_KomplexeZweckbestGemeinschaftsanlagen,
    'BP_KomplexeZweckbestLandwirtschaft': BP_KomplexeZweckbestLandwirtschaft,
    'BP_KomplexeZweckbestWald': BP_KomplexeZweckbestWald,
    'BP_KomplexeZweckbestVerEntsorgung': BP_KomplexeZweckbestVerEntsorgung,
    'BP_EmissionskontingentLaerm': BP_EmissionskontingentLaerm,
    'BP_EmissionskontingentLaermGebiet': BP_EmissionskontingentLaermGebiet,
    'BP_Richtungssektor': BP_Richtungssektor,
    'BP_RichtungssektorGrenze': BP_RichtungssektorGrenze,
    'BP_ZusatzkontingentLaerm': BP_ZusatzkontingentLaerm,
    'BP_ZusatzkontingentLaermFlaeche': BP_ZusatzkontingentLaermFlaeche,
    'BP_KomplexeZweckbestNebenanlagen': BP_KomplexeZweckbestNebenanlagen,
    'BP_KomplexeSondernutzung': BP_KomplexeSondernutzung,
    'BP_VeraenderungssperreDaten': BP_VeraenderungssperreDaten,
    'BP_NutzungsartenGrenze': BP_NutzungsartenGrenze,
    'BP_AbstandsMass': BP_AbstandsMass,
    'BP_BereichOhneEinAusfahrtLinie': BP_BereichOhneEinAusfahrtLinie,
    'BP_EinfahrtPunkt': BP_EinfahrtPunkt,
    'BP_EinfahrtsbereichLinie': BP_EinfahrtsbereichLinie,
    'BP_NebenanlagenFlaeche': BP_NebenanlagenFlaeche,
    'BP_Immissionsschutz': BP_Immissionsschutz,
    'BP_TechnischeMassnahmenFlaeche': BP_TechnischeMassnahmenFlaeche,
    'BP_AbgrabungsFlaeche': BP_AbgrabungsFlaeche,
    'BP_AufschuettungsFlaeche': BP_AufschuettungsFlaeche,
    'BP_KennzeichnungsFlaeche': BP_KennzeichnungsFlaeche,
    'BP_UeberbaubareGrundstuecksFlaeche': BP_UeberbaubareGrundstuecksFlaeche,
    'BP_TextAbschnitt': BP_TextAbschnitt,
    'BP_NebenanlagenAusschlussFlaeche': BP_NebenanlagenAusschlussFlaeche,
    'BP_WohngebaeudeFlaeche': BP_WohngebaeudeFlaeche,
    'BP_WasserwirtschaftsFlaeche': BP_WasserwirtschaftsFlaeche,

    'FP_Objekt': FP_Objekt,
    'FP_GenerischesObjekt': FP_GenerischesObjekt,
    'FP_BebauungsFlaeche': FP_BebauungsFlaeche,
    'FP_KeineZentrAbwasserBeseitigungFlaeche': FP_KeineZentrAbwasserBeseitigungFlaeche,
    'FP_KomplexeSondernutzung': FP_KomplexeSondernutzung,
    'FP_Gemeinbedarf': FP_Gemeinbedarf,
    'FP_SpielSportanlage': FP_SpielSportanlage,
    'FP_Gruen': FP_Gruen,
    'FP_Landwirtschaft': FP_Landwirtschaft,
    'FP_WaldFlaeche': FP_WaldFlaeche,
    'FP_Strassenverkehr': FP_Strassenverkehr,
    'FP_Gewaesser': FP_Gewaesser,
    'FP_Wasserwirtschaft': FP_Wasserwirtschaft,
    'FP_VerEntsorgung': FP_VerEntsorgung,
    'FP_Abgrabung': FP_Abgrabung,
    'FP_Aufschuettung': FP_Aufschuettung,
    'FP_SchutzPflegeEntwicklung': FP_SchutzPflegeEntwicklung,
    'FP_AusgleichsFlaeche': FP_AusgleichsFlaeche,
    'FP_Kennzeichnung': FP_Kennzeichnung,
    'FP_TextlicheDarstellungsFlaeche': FP_TextlicheDarstellungsFlaeche,
    'FP_TextAbschnittFlaeche': FP_TextAbschnittFlaeche,
    'FP_KomplexeZweckbestGemeinbedarf': FP_KomplexeZweckbestGemeinbedarf,
    'FP_KomplexeZweckbestSpielSportanlage': FP_KomplexeZweckbestSpielSportanlage,
    'FP_KomplexeZweckbestGruen': FP_KomplexeZweckbestGruen,
    'FP_KomplexeZweckbestLandwirtschaft': FP_KomplexeZweckbestLandwirtschaft,
    'FP_KomplexeZweckbestWald': FP_KomplexeZweckbestWald,
    'FP_KomplexeZweckbestVerEntsorgung': FP_KomplexeZweckbestVerEntsorgung,
    'FP_PrivilegiertesVorhaben': FP_PrivilegiertesVorhaben,
    'FP_TextAbschnitt': FP_TextAbschnitt,
    'FP_Nutzungsbeschraenkung': FP_Nutzungsbeschraenkung,
    'FP_NutzungsbeschraenkungsFlaeche': FP_NutzungsbeschraenkungsFlaeche,
    'FP_FlaecheOhneDarstellung': FP_FlaecheOhneDarstellung,
    'FP_VorbehalteFlaeche': FP_VorbehalteFlaeche,
    'FP_UnverbindlicheVormerkung': FP_UnverbindlicheVormerkung,
    'FP_DarstellungNachLandesrecht': FP_DarstellungNachLandesrecht,
    'FP_AnpassungKlimawandel': FP_AnpassungKlimawandel,
    'FP_ZentralerVersorgungsbereich': FP_ZentralerVersorgungsbereich,

    'SO_Objekt': SO_Objekt,
    'SO_Strassenverkehrsrecht': SO_Strassenverkehrsrecht,
    'SO_Schienenverkehrsrecht': SO_Schienenverkehrsrecht,
    'SO_Denkmalschutzrecht': SO_Denkmalschutzrecht,
    'SO_Bodenschutzrecht': SO_Bodenschutzrecht,
    'SO_Luftverkehrsrecht': SO_Luftverkehrsrecht,
    'SO_SchutzgebietWasserrecht': SO_SchutzgebietWasserrecht,
    'SO_SchutzgebietSonstigesRecht': SO_SchutzgebietSonstigesRecht,
    'SO_SchutzgebietNaturschutzrecht': SO_SchutzgebietNaturschutzrecht,
    'SO_Gelaendemorphologie': SO_Gelaendemorphologie,
    'SO_Grenze': SO_Grenze,
    'SO_Wasserwirtschaft': SO_Wasserwirtschaft,
    'SO_Gewaesser': SO_Gewaesser,
    'SO_Wasserrecht': SO_Wasserrecht,
    'SO_KomplexeFestlegungGewaesser': SO_KomplexeFestlegungGewaesser,
    'SO_Strassenverkehr': SO_Strassenverkehr,
    'SO_KomplexeZweckbestStrassenverkehr': SO_KomplexeZweckbestStrassenverkehr,
    'SO_SonstigesRecht': SO_SonstigesRecht,
    'SO_Bauverbotszone': SO_Bauverbotszone,
    'SO_Baubeschraenkung': SO_Baubeschraenkung,
    'SO_Forstrecht': SO_Forstrecht,
    'SO_Gebiet': SO_Gebiet,
    'SO_TextAbschnitt': SO_TextAbschnitt,

    # 5.1 LP_Basisobjekte
    'LP_Objekt': LP_Objekt,
    'LP_TextAbschnitt': LP_TextAbschnitt,
    # 5.2 LP_SchutzgebieteBestandteileNaturschutzrecht
    'LP_SchutzBestimmterTeileVonNaturUndLandschaft': LP_SchutzBestimmterTeileVonNaturUndLandschaft,
    'LP_DetailGesetzlGeschBiotopLR': LP_DetailGesetzlGeschBiotopLR,
    # 5.3 LP_PlaninhalteLandschaftsplanung
    'LP_BiotopverbundBiotopvernetzung': LP_BiotopverbundBiotopvernetzung,
    'LP_Eingriffsregelung': LP_Eingriffsregelung,
    'LP_EingriffsregelungKomplex': LP_EingriffsregelungKomplex,
    'LP_TypBioVerbundKomplex': LP_TypBioVerbundKomplex,
    # 5.4 LP_PlaninhalteLandschaftsplanungZEM
    'LP_AdressatKomplex': LP_AdressatKomplex,
    'LP_BiologischeVielfaltKomplex': LP_BiologischeVielfaltKomplex,
    'LP_BiologischeVielfaltTypKomplex': LP_BiologischeVielfaltTypKomplex,
    'LP_BioVfBiotoptypKomplex': LP_BioVfBiotoptypKomplex,
    'LP_BioVfPflanzenArtKomplex': LP_BioVfPflanzenArtKomplex,
    'LP_BioVfTiereArtKomplex': LP_BioVfTiereArtKomplex,
    'LP_BodenKomplex': LP_BodenKomplex,
    'LP_ErholungKomplex': LP_ErholungKomplex,
    'LP_KlimaKomplex': LP_KlimaKomplex,
    'LP_LandschaftsbildKomplex': LP_LandschaftsbildKomplex,
    'LP_LuftKomplex': LP_LuftKomplex,
    'LP_NutzungseinschraenkungKomplex': LP_NutzungseinschraenkungKomplex,
    'LP_SchutzgutKomplex': LP_SchutzgutKomplex,
    'LP_SPEKomplex': LP_SPEKomplex,
    'LP_WasserKomplex': LP_WasserKomplex,
    'LP_ZielDimNatSchLaPflKomplex': LP_ZielDimNatSchLaPflKomplex,
    'LP_ZieleErfordernisseMassnahmen': LP_ZieleErfordernisseMassnahmen,
    'LP_BioVfBiotoptyp_BKompV': LP_BioVfBiotoptyp_BKompV,
    'LP_BioVfBiotoptyp_LandesKS': LP_BioVfBiotoptyp_LandesKS,
    'LP_BioVf_FFH_LRT': LP_BioVf_FFH_LRT,
    # 5.5 LP_Sonstiges
    'LP_GenerischesObjekt': LP_GenerischesObjekt,
    'LP_TextAbschnittObjekt': LP_TextAbschnittObjekt,
    'LP_ZweckbestimmungGenerischeObjekte': LP_ZweckbestimmungGenerischeObjekte,

    'RP_TextAbschnitt': RP_TextAbschnitt,

    'CodeListValue': CodeListValue,
    'XP_MimeTypes': XP_MimeTypes,
    'BP_SonstPlanArt': BP_SonstPlanArt,
    'BP_Status': BP_Status,
    'BP_DetailArtDerBaulNutzung': BP_DetailArtDerBaulNutzung,
    'BP_DetailDachform': BP_DetailDachform,
    'BP_DetailSondernutzung': BP_DetailSondernutzung,
    'BP_DetailZweckbestGemeinschaftsanlagen': BP_DetailZweckbestGemeinschaftsanlagen,
    'BP_NutzungNichtUeberbaubGrundstFlaeche': BP_NutzungNichtUeberbaubGrundstFlaeche,
    'BP_DetailZweckbestWasserwirtschaft': BP_DetailZweckbestWasserwirtschaft,

    'FP_SonstPlanArt': FP_SonstPlanArt,
    'FP_Status': FP_Status,
    'FP_DetailArtDerBaulNutzung': FP_DetailArtDerBaulNutzung,
    'FP_DetailZweckbestVerEntsorgung': FP_DetailZweckbestVerEntsorgung,
    'FP_DetailZweckbestGemeinbedarf': FP_DetailZweckbestGemeinbedarf,
    'FP_DetailZweckbestimmungNachLandesrecht': FP_DetailZweckbestimmungNachLandesrecht,
    'FP_DetailMassnahmeKlimawandel': FP_DetailMassnahmeKlimawandel,
    'FP_ZentralerVersorgungsbereichAuspraegung': FP_ZentralerVersorgungsbereichAuspraegung,

    'SO_DetailKlassifizNachDenkmalschutzrecht': SO_DetailKlassifizNachDenkmalschutzrecht,
    'SO_DetailKlassifizNachBodenschutzrecht': SO_DetailKlassifizNachBodenschutzrecht,
    'SO_DetailKlassifizNachSchienenverkehrsrecht': SO_DetailKlassifizNachSchienenverkehrsrecht,
    'SO_DetailKlassifizNachLuftverkehrsrecht': SO_DetailKlassifizNachLuftverkehrsrecht,
    'SO_DetailKlassifizNachSonstigemRecht': SO_DetailKlassifizNachSonstigemRecht,
    'SO_DetailKlassifizBauverbot': SO_DetailKlassifizBauverbot,
    'SO_DetailKlassifizBaubeschraenkung': SO_DetailKlassifizBaubeschraenkung,
    'SO_SonstGebietsArt': SO_SonstGebietsArt,
    'SO_SonstRechtsstandGebietTyp': SO_SonstRechtsstandGebietTyp,
    'SO_DetailKlassifizNachForstrecht': SO_DetailKlassifizNachForstrecht,
    'SO_DetailKlassifizSchutzgebietSonstRecht': SO_DetailKlassifizSchutzgebietSonstRecht,
    'SO_DetailKlassifizGelaendemorphologie': SO_DetailKlassifizGelaendemorphologie,
    'SO_SonstGrenzeTypen': SO_SonstGrenzeTypen,

    'XP_DetailTechnVorkehrungImmissionsschutz': XP_DetailTechnVorkehrungImmissionsschutz,

    'XP_GenerAttribut': XP_GenerAttribut,
    'XP_DatumAttribut': XP_DatumAttribut,
    'XP_DoubleAttribut': XP_DoubleAttribut,
    'XP_StringAttribut': XP_StringAttribut,
    'XP_IntegerAttribut': XP_IntegerAttribut,
    'XP_URLAttribut': XP_URLAttribut,
}


PRE_FILLED_CLASSES = [
    XP_Gemeinde,
    XP_Plangeber,
    XP_GesetzlicheGrundlage
]

ObjectBaseType = Union[Type[BP_Objekt], Type[FP_Objekt], Type[LP_Objekt], Type[SO_Objekt]]
OBJECT_BASE_TYPES = [
    BP_Objekt, FP_Objekt, LP_Objekt, SO_Objekt
]

PLAN_BASE_TYPES = [
    BP_Plan, FP_Plan, LP_Plan, RP_Plan
]

BEREICH_BASE_TYPES = [
    BP_Bereich, FP_Bereich, LP_Bereich, RP_Bereich
]


def save_to_db(obj, expire_on_commit=True):
    """ Fügt ein Objekt der Datenbank hinzu """
    with Session.begin() as session:
        session.expire_on_commit = expire_on_commit
        session.add(obj)


async def save_to_db_async(obj):
    """ Async Version der save_to_db Methode"""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, save_to_db, obj)


def query_existing(obj, session=None):
    """
    Prüft ob ein gegebenes XPlanung-Objekt bereits in der Datenbank existiert.
    Falls ja, wird dieses zurückgegeben, ansonsten None
    """
    obj_class = obj.__class__
    if session is None:
        with Session.begin() as session:
            session.expire_on_commit = False
            candidates = session.query(obj_class).all()
    else:
        candidates = session.query(obj_class).all()

    return next((x for x in candidates if x == obj), None)


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
    msg.setIcon(QMessageBox.Icon.Warning)

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
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
    msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
    ret = msg.exec()
    if ret == QMessageBox.StandardButton.Cancel:
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


def caller_name(skip=1):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    # Avoid circular refs and frame leaks
    #  https://docs.python.org/2.7/library/inspect.html#the-interpreter-stack
    del parentframe, stack

    return ".".join(name)


def open_directory_explorer(dir_path: str, create_dir=False):
    if create_dir:
        os.makedirs(dir_path, exist_ok=True)

    if sys.platform == "win32":  # win
        os.startfile(dir_path)
    elif sys.platform == "darwin":  # mac
        subprocess.Popen(["open", dir_path])
    else:  # linux
        subprocess.Popen(["xdg-open", dir_path])
