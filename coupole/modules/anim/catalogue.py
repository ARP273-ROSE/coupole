"""Catalogue des 94 animations : les 92 de ClassAction (University of Nebraska-Lincoln Astronomy Education, Apache 2.0),
la machine d'Anticythère, adaptée d'Anticythere3D (du même auteur ; fichier d'origine « Anticythere3D »), et
« Orion en 3D », propre à Coupole.

Chaque entrée : identifiant ClassAction, thème, titre d'origine (anglais), fichier Flash d'origine, et la classe
Python qui la refait (« module:Classe » dans ``animations/``) ou None si elle est encore à venir.  Les noms et
descriptions FR/EN sont dans ``textes.py`` (clés ``anim_nom_<id>`` et ``anim_desc_<id>``, id en minuscules).
Pour ajouter une animation d'un lot suivant : écrire ``animations/<id>.py`` et renseigner sa classe ici."""
from __future__ import annotations

import importlib

# Ordre pédagogique des thèmes (catalogue et filtre) : de l'introduction et du ciel vu de la Terre jusqu'à la
# cosmologie ; même ordre que Coupole Web.
THEMES = ('intro', 'coordsmotion', 'lunarcycles', 'ancientastro', 'renaissance', 'solar', 'solarsystemdebris',
          'sunsolarenergy', 'light', 'telescopes', 'stellarprops', 'binaryvariablestars', 'extrasolarplanets',
          'ismstarformation', 'milkyway', 'cosmology')

# (id, thème, titre d'origine, fichier d'origine, classe ou None)
ANIMATIONS = (
    ('hammerthrower', 'extrasolarplanets', 'Hammer Thrower Comparison', 'extrasolarplanets/hammerthrower.swf', 'lanceur_marteau:LanceurMarteau'),
    ('eclipsingbinarysim', 'binaryvariablestars', 'Eclipsing Binary Simulator',
     'binaryvariablestars/eclipsingbinarysim.swf', 'binaire_eclipses:BinaireEclipses'),
    ('gravalgebra', 'renaissance', 'Gravity Algebra', 'renaissance/gravalgebra.swf',
     'algebre_gravitation:AlgebreGravitation'),
    ('lightcurve', 'binaryvariablestars', 'Lightcurve Simulator', 'binaryvariablestars/lightcurve.swf',
     'courbe_lumiere:CourbeLumiere'),
    ('centerofmass', 'binaryvariablestars', 'Center of Mass Simulator', 'binaryvariablestars/centerofmass.swf',
     'centre_masse:CentreMasse'),
    ('solarsystemproperties', 'solar', 'Solar System Properties Explorer', 'solar/solarsystemproperties.swf',
     'proprietes_planetes:ProprietesPlanetes'),
    ('formationtemps', 'solar', 'Planet Formation Temperatures Plot', 'solar/formationtemps.swf',
     'temperatures_formation:TemperaturesFormation'),
    ('daylightsimulator', 'coordsmotion', 'Daylight Simulator', 'coordsmotion/daylightsimulator.swf',
     'jour_nuit:JourNuit'),
    ('celestialhorizon', 'coordsmotion', 'Celestial and Horizon Systems Comparison',
     'coordsmotion/celestialhorizon.swf', 'repere_celeste_horizon:RepereCelesteHorizon'),
    ('siderealTimeAndHourAngleDemo', 'coordsmotion', 'Sidereal Time and Hour Angle Demonstrator',
     '200level/siderealTimeAndHourAngleDemo.swf', 'angle_horaire:AngleHoraire'),
    ('antikythera', 'ancientastro', 'Antikythera Mechanism', 'Anticythere3D', 'anticythere:Anticythere'),
    ('orion3d', 'ismstarformation', 'Orion in 3D', 'Coupole', 'orion3d:Orion3D'),
    ('smallangledemo', 'ancientastro', 'Small-Angle Approximation Demonstrator', 'ancientastro/smallangledemo.swf',
     'petits_angles:PetitsAngles'),
    ('dipperclock', 'ancientastro', 'Big Dipper Clock', 'ancientastro/dipperclock.swf',
     'horloge_grande_ourse:HorlogeGrandeOurse'),
    ('heliacalrisingsim', 'ancientastro', 'Heliacal Rising Simulator', 'ancientastro/heliacalrisingsim.swf',
     'lever_heliaque:LeverHeliaque'),
    ('wagonwheel', 'binaryvariablestars', 'Aliasing in Wagon Wheels', 'binaryvariablestars/wagonwheel.swf',
     'repliement:Repliement'),
    ('daylighthoursexplorer', 'coordsmotion', 'Daylight Hours Explorer', 'coordsmotion/daylighthoursexplorer.swf',
     'duree_jour:DureeJour'),
    ('meridaltdiagram', 'coordsmotion', 'Meridional Altitude Simulator', 'coordsmotion/meridaltdiagram.swf',
     'hauteur_meridienne:HauteurMeridienne'),
    ('latsim', 'coordsmotion', 'Declination Ranges Simulator', 'coordsmotion/latsim.swf', 'plages:PlagesDeclinaison'),
    ('seasonsim', 'coordsmotion', 'Ecliptic Simulator', 'coordsmotion/seasonsim.swf', 'ecliptique:Ecliptique'),
    ('transitmovie', 'coordsmotion', 'Union Seasons Demonstrator', 'coordsmotion/transitmovie.swf',
     'ombre_batiment:OmbreBatiment'),
    ('altazimuth', 'coordsmotion', 'Azimuth/Altitude Demonstrator', 'coordsmotion/altazimuth.swf',
     'azimut_hauteur:AzimutHauteur'),
    ('obliquity', 'coordsmotion', 'Obliquity Simulator', 'coordsmotion/obliquity.swf', 'obliquite:Obliquite'),
    ('zodiac', 'coordsmotion', 'Ecliptic (Zodiac) Simulator', 'coordsmotion/zodiac.swf', 'zodiaque:Zodiaque'),
    ('longlat', 'coordsmotion', 'Longitude/Latitude Demonstrator', 'coordsmotion/longlat.swf',
     'longitude_latitude:LongitudeLatitude'),
    ('radecdemo', 'coordsmotion', 'Celestial-Equatorial (RA/Dec) Demonstrator', 'coordsmotion/radecdemo.swf',
     'alpha_delta:AlphaDelta'),
    ('sunpaths', 'coordsmotion', 'Paths of the Sun', 'coordsmotion/sunpaths.swf',
     'trajectoires_soleil:TrajectoiresSoleil'),
    ('sunmotions', 'coordsmotion', 'Sun Motions Demonstrator', 'coordsmotion/sunmotions.swf',
     'mouvements_soleil:MouvementsSoleil'),
    ('sunsrays', 'coordsmotion', "Sun's Rays Simulator", 'coordsmotion/sunsrays.swf', 'rayons_soleil:RayonsSoleil'),
    ('horizon', 'coordsmotion', "Sun's Position on Horizon", 'coordsmotion/horizon.swf', 'lever_horizon:LeverHorizon'),
    ('bigdipper', 'coordsmotion', 'Big Dipper 3D', 'coordsmotion/bigdipper.swf', 'grande_ourse:GrandeOurse'),
    ('eclipticsimulator', 'coordsmotion', 'Seasons Simulator (NAAP)', 'coordsmotion/eclipticsimulator.swf',
     'saisons:Saisons'),
    ('celhorcomp', 'coordsmotion', 'Coordinate Systems Comparison', 'coordsmotion/celhorcomp.swf',
     'comparaison_reperes:ComparaisonReperes'),
    ('balloon', 'cosmology', 'Balloon Universe', 'cosmology/balloon.swf', 'ballon_univers:BallonUnivers'),
    ('ca_extrasolarplanets_graph', 'extrasolarplanets', 'Radial Velocity Graph',
     'extrasolarplanets/ca_extrasolarplanets_graph.swf', 'vitesse_radiale:CourbeVitesseRadiale'),
    ('ca_extrasolarplanets_starwobble', 'extrasolarplanets', 'Influence of Planets on the Sun',
     'extrasolarplanets/ca_extrasolarplanets_starwobble.swf', 'barycentre_solaire:BarycentreSolaire'),
    ('pulsarPeriodSim', 'extrasolarplanets', 'Pulsar Period Simulator', 'extrasolarplanets/pulsarPeriodSim001.swf',
     'pulsar:Pulsar'),
    ('radialvelocitydemo', 'extrasolarplanets', 'Extrasolar Planet Radial Velocity Demonstrator',
     'extrasolarplanets/radialvelocitydemo.swf', 'vitesse_radiale:SpectreVitesseRadiale'),
    ('transitsimulator', 'extrasolarplanets', 'Transit Simulator (NAAP)', 'extrasolarplanets/transitsimulator.swf',
     'transits:Transits'),
    ('radialvelocitysimulator', 'extrasolarplanets', 'Radial Velocity Simulator (NAAP)',
     'extrasolarplanets/radialvelocitysimulator.swf', 'vitesses_radiales:VitessesRadiales'),
    ('lookbacktimesim', 'intro', 'Lookback Time Simulator', 'intro/lookbacktimesim.swf',
     'regard_passe:RegardPasse'),
    ('meltednail', 'light', 'Blackbody Curves of Melting', 'light/meltednail.swf', 'clou_fondu:ClouFondu'),
    ('spectrum010', 'light', 'Spectrum Explorer', 'light/spectrum010.swf', 'explorateur_spectres:ExplorateurSpectres'),
    ('emspectrum', 'light', 'EM Spectrum Module', 'light/emspectrum.swf', 'spectre_em:SpectreEM'),
    ('bbexplorer', 'light', 'Blackbody Curves (NAAP)', 'light/bbexplorer.swf', 'corps_noir:CorpsNoir'),
    ('dopplershift', 'light', 'Doppler Shift Demonstrator', 'light/dopplershift.swf', 'effet_doppler:EffetDoppler'),
    ('filters', 'light', 'Filters Simulator (NAAP)', 'light/filters.swf', 'filtres:Filtres'),
    ('hydrogenatom', 'light', 'Hydrogen Atom Simulator (NAAP)', 'light/hydrogenatom.swf', 'atome_hydrogene:AtomeHydrogene'),
    ('threeviewsspectra', 'light', 'Three Views Spectrum Demonstrator', 'light/threeviewsspectra.swf', 'kirchhoff:Kirchhoff'),
    ('basketball', 'lunarcycles', 'Basketball Phases Simulator', 'lunarcycles/basketball.swf',
     'ballon_phases:BallonPhases'),
    ('eclipsetable', 'lunarcycles', 'Eclipse Table', 'lunarcycles/eclipsetable.swf', 'table_eclipses:TableEclipses'),
    ('fullmoondec', 'lunarcycles', 'Full Moon Declination Simulator', 'lunarcycles/fullmoondec.swf',
     'pleine_lune_declinaison:PleineLuneDeclinaison'),
    ('lunar_applet', 'lunarcycles', 'Lunar Phases Simulator (NAAP)', 'lunarcycles/lunarapplet.swf',
     'phases_lune:PhasesLune'),
    ('lunar_phaser', 'lunarcycles', 'Lunar Phase Vocabulary', 'lunarcycles/lunar_phaser.swf',
     'vocabulaire_phases:VocabulairePhases'),
    ('mooninc', 'lunarcycles', 'Moon Inclination', 'lunarcycles/mooninc.swf', 'inclinaison_lune:InclinaisonLune'),
    ('moonphases', 'lunarcycles', 'Three Views Simulator', 'lunarcycles/moonphases.swf',
     'trois_vues:TroisVues'),
    ('phaseDemonstrator', 'lunarcycles', 'Phase Positions Demonstrator', 'lunarcycles/phaseDemonstrator.swf',
     'positions_phases:PositionsPhases'),
    ('positionsdemonstrator', 'lunarcycles', 'Moon Phases and the Horizon Diagram',
     'lunarcycles/positionsdemonstrator.swf', 'lune_horizon:LuneHorizon'),
    ('shadowsim', 'lunarcycles', 'Eclipse Shadow Simulator', 'lunarcycles/shadowsim.swf', 'ombres:OmbresEclipse'),
    ('synodiclag', 'lunarcycles', 'Synodic Lag', 'lunarcycles/synodiclag.swf', 'retard_synodique:RetardSynodique'),
    ('tidesim', 'lunarcycles', 'Tidal Bulge Simulation', 'lunarcycles/tidesim.swf', 'marees:Marees'),
    ('milkywayrotationalvelocity', 'milkyway', 'Milky Way Rotational Velocity',
     'milkyway/milkywayrotationalvelocity.swf', 'rotation_galaxie:RotationGalaxie'),
    ('trafficdensity', 'milkyway', 'Traffic Density Analogy', 'milkyway/trafficdensity.swf',
     'ondes_densite:OndesDensite'),
    ('venusphases', 'renaissance', 'Phases of Venus', 'renaissance/venusphases.swf', 'phases_venus:PhasesVenus'),
    ('ptolemaic', 'renaissance', 'Ptolemaic Phases of Venus', 'renaissance/ptolemaic.swf',
     'phases_venus:PhasesVenusPtolemee'),
    ('marsorbit', 'renaissance', 'Ptolemaic Orbit of Mars', 'renaissance/marsorbit.swf', 'mars_ptolemee:MarsPtolemee'),
    ('pathtracer', 'renaissance', 'Epicycles Demo', 'renaissance/pathtracer.swf', 'epicycles:Epicycles'),
    ('retrograde', 'renaissance', 'Retrograde Motion', 'renaissance/retrograde.swf', 'retrograde:Retrograde'),
    ('keplers_third', 'renaissance', "Kepler's Third Law", 'renaissance/keplers_third.swf', 'kepler3:Kepler3'),
    ('synodiccalculator', 'renaissance', 'Synodic Period Calculator', 'renaissance/synodiccalculator.swf',
     'periode_synodique:PeriodeSynodique'),
    ('configurationssimulator', 'renaissance', 'Planetary Configurations Simulator (NAAP)',
     'renaissance/configurationssimulator.swf', 'configurations:Configurations'),
    ('kepler', 'renaissance', 'Planetary Orbit Simulator (NAAP)', 'renaissance/kepler.swf', 'kepler:OrbiteKepler'),
    ('ellipsedemo', 'renaissance', 'Eccentricity Demonstrator', 'renaissance/ellipsedemo.swf', 'excentricite:Excentricite'),
    ('stellarmag', 'stellarprops', 'Distance Modulus Explorer', 'stellarprops/stellarmag.swf',
     'module_distance:ModuleDistance'),
    ('stellarvel', 'stellarprops', 'Stellar Velocity Calculator', 'stellarprops/stellarvel.swf',
     'vitesse_etoile:VitesseEtoile'),
    ('parallaxdiag', 'stellarprops', 'Parallax Calculator', 'stellarprops/parallaxdiag.swf', 'parallaxe:Parallaxe'),
    ('spectroparallax', 'stellarprops', 'Spectroscopic Parallax Simulator', 'stellarprops/spectroparallax.swf',
     'parallaxe_spectro:ParallaxeSpectro'),
    ('stellarlum', 'stellarprops', 'Stellar Luminosity Calculator', 'stellarprops/stellarlum.swf',
     'luminosite_etoile:LuminositeEtoile'),
    ('lightdetector', 'stellarprops', 'Flux Simulator', 'stellarprops/lightdetector.swf', 'flux_lumineux:FluxLumineux'),
    ('hrexplorer', 'stellarprops', 'HR Explorer (NAAP)', 'stellarprops/hrexplorer.swf', 'diagramme_hr:DiagrammeHR'),
    ('fusion01', 'sunsolarenergy', 'Proton-Proton Animation', 'sunsolarenergy/fusion01.swf', 'fusion:FusionPP'),
    ('fusion02', 'sunsolarenergy', 'CNO Cycle Animation', 'sunsolarenergy/fusion02.swf', 'fusion:FusionCNO'),
    ('telescope10', 'telescopes', 'Telescope Simulator', 'telescopes/telescope10.swf', 'telescope:Telescope'),
    ('buckets', 'telescopes', 'CCD Simulator', 'telescopes/buckets.swf', 'ccd:CCD'),
    ('drivingthroughsnow', 'solarsystemdebris', 'Driving Through Snow', 'solarsystemdebris/drivingthroughsnow.swf',
     'neige:Neige'),
    ('antipodesexplorer', 'coordsmotion', 'Antipodes Explorer', 'coordsmotion/antipodesexplorer.swf',
     'antipodes:Antipodes'),
    ('sunmotionsoverview', 'coordsmotion', 'Sun Motions Overview', 'coordsmotion/sunmotionsoverview.swf',
     'trajectoires_soleil:VueEnsembleSoleil'),
    ('gravcalc', 'renaissance', "Newton's Law of Gravity Calculator", 'renaissance/gravcalc.swf', 'gravitation:Gravitation'),
    ('earthorbitplot', 'renaissance', 'Earth Orbit Plot', 'renaissance/earthorbitplot.swf', 'orbites_terre:OrbitesTerre'),
    ('lunarphasequizzer', 'lunarcycles', 'Lunar Phase Quizzer', 'lunarcycles/lunarphasequizzer.swf',
     'questionnaire_phases:QuestionnairePhases'),
    ('snellslaw', 'telescopes', "Snell's Law Demonstrator", 'telescopes/snellslaw.swf', 'snell:Snell'),
    ('galacticredshift', 'cosmology', 'Galactic Redshift Simulator', 'cosmology/galacticredshift.swf',
     'decalage_galaxie:DecalageGalaxie'),
    ('moonbisector', 'lunarcycles', 'Moon Phases With Bisectors', 'lunarcycles/moonbisector.swf',
     'plans_bissecteurs:PlansBissecteurs'),
    ('siderealSolarTime', 'coordsmotion', 'Sidereal and Solar Time Simulator', 'coordsmotion/siderealSolarTime.swf',
     'temps_sideral:TempsSideral'),
)

# Lot 1 (0.3.0) : sphère céleste, repères, Soleil, saisons, Lune, éclipses, orbites, distances (ordre du catalogue)
LOT1 = ('longlat', 'sunmotions', 'eclipticsimulator', 'lunar_applet', 'sunsrays', 'altazimuth', 'radecdemo',
        'celhorcomp', 'siderealTimeAndHourAngleDemo', 'seasonsim', 'obliquity', 'zodiac', 'siderealSolarTime',
        'latsim', 'shadowsim', 'marsorbit', 'pathtracer', 'retrograde', 'kepler', 'parallaxdiag', 'stellarmag')
# Lot 1 bis (0.3.0) : les autres animations « Coordonnées et mouvements » (sauf transitmovie, un film)
LOT1_BIS = ('daylighthoursexplorer', 'meridaltdiagram', 'sunpaths', 'sunmotionsoverview', 'horizon', 'daylightsimulator',
            'antipodesexplorer', 'bigdipper', 'celestialhorizon')
# Lot 2 (0.3.1) : la Lune, la Renaissance, l'astronomie antique, et l'ombre d'un bâtiment (au lieu du film transitmovie)
LOT2 = ('lunar_phaser', 'basketball', 'moonphases', 'phaseDemonstrator', 'positionsdemonstrator', 'lunarphasequizzer',
        'moonbisector', 'fullmoondec', 'synodiclag', 'tidesim', 'mooninc', 'eclipsetable',
        'venusphases', 'ptolemaic', 'configurationssimulator', 'synodiccalculator', 'keplers_third', 'ellipsedemo',
        'gravalgebra', 'gravcalc', 'earthorbitplot',
        'smallangledemo', 'dipperclock', 'heliacalrisingsim', 'transitmovie')
# Lot 2 bis (0.3.1) : les propriétés stellaires
LOT2_BIS = ('stellarlum', 'lightdetector', 'stellarvel', 'spectroparallax', 'hrexplorer')
# Lot 3 (0.4.0) : lumière et spectres, exoplanètes, étoiles doubles et variables, et les autres thèmes
LOT3 = ('meltednail', 'bbexplorer', 'spectrum010', 'emspectrum', 'dopplershift', 'filters', 'hydrogenatom',
        'threeviewsspectra',
        'hammerthrower', 'ca_extrasolarplanets_graph', 'ca_extrasolarplanets_starwobble', 'pulsarPeriodSim',
        'radialvelocitydemo', 'transitsimulator', 'radialvelocitysimulator',
        'eclipsingbinarysim', 'lightcurve', 'centerofmass', 'wagonwheel',
        'solarsystemproperties', 'formationtemps', 'drivingthroughsnow', 'fusion01', 'fusion02',
        'milkywayrotationalvelocity', 'trafficdensity', 'balloon', 'galacticredshift', 'telescope10', 'buckets',
        'snellslaw', 'lookbacktimesim')
# 0.4.2 : la machine d'Anticythère, adaptée d'Anticythere3D (du même auteur) : hors ClassAction
LOT4 = ('antikythera',)
# 0.5.0 : Orion en 3D (propre à Coupole ; thème « Milieu interstellaire et formation des étoiles »)
LOT5 = ('orion3d',)
#: animations qui ne viennent pas de ClassAction : identifiant → (application d'origine, adresse de son dépôt)
HORS_CLASSACTION = {'antikythera': ('Anticythere3D', 'https://github.com/ARP273-ROSE/Anticythere3D'),
                    'orion3d': ('Coupole', 'https://github.com/ARP273-ROSE/coupole/blob/main/NOTICE')}
ORDRE = LOT1 + LOT1_BIS + LOT2 + LOT2_BIS + LOT3 + LOT4 + LOT5


class Entree:
    __slots__ = ('id', 'theme', 'titre', 'fichier', 'classe')

    def __init__(self, ident, theme, titre, fichier, classe):
        self.id, self.theme, self.titre, self.fichier, self.classe = ident, theme, titre, fichier, classe

    @property
    def cle(self) -> str:
        return self.id.lower()

    @property
    def faite(self) -> bool:
        return self.classe is not None

    def charger(self):
        """Classe de l'animation (importée à la demande)."""
        mod, _, nom = self.classe.partition(':')
        return getattr(importlib.import_module('%s.animations.%s' % (__package__, mod)), nom)


ENTREES = tuple(Entree(*a) for a in ANIMATIONS)
PAR_ID = {e.id: e for e in ENTREES}


def faites() -> list:
    return [e for e in ENTREES if e.faite]


def a_venir() -> list:
    return [e for e in ENTREES if not e.faite]
