"""Table des éclipses 2015-2044 de l'animation « Eclipse Table » de ClassAction (University of Nebraska-Lincoln
Astronomy Education, Apache License 2.0), reprise telle quelle ; coquilles corrigées.

Chaque éclipse : (année, mois, jour, type, saros, grandeur, durée, zones de visibilité en anglais).  Grandeur :
éclipse de Soleil, rapport des diamètres apparents (> 1 : totale) ; éclipse de Lune, grandeur de l'ombre (négative
pour une éclipse par la pénombre seule).  Durée : centralité (Soleil), phase dans l'ombre (totalité) pour la Lune."""

SOLEIL = (
    (2015, 3, 20, 'total', 120, 1.045, '02m47s', 'Iceland, Europe, n Africa, n Asia (Total: n Atlantic, Faeroe Is, Svalbard)'),
    (2015, 9, 13, 'partial', 125, 0.788, '-', 's Africa, s Indian, Antarctica'),
    (2016, 3, 9, 'total', 130, 1.045, '04m09s', 'e Asia, Australia, Pacific (Total: Sumatra, Borneo, Sulawesi, Pacific)'),
    (2016, 9, 1, 'annular', 135, 0.974, '03m06s', 'Africa, Indian Ocean (Annular: Atlantic, c Africa, Madagascar, Indian)'),
    (2017, 2, 26, 'annular', 140, 0.992, '00m44s', 's S. America, Atlantic, Africa, Antarctica (Annular: Pacific, Chile, Argentina, Atlantic, Africa)'),
    (2017, 8, 21, 'total', 145, 1.031, '02m40s', 'N. America, n S. America (Total: n Pacific, U.S., s Atlantic)'),
    (2018, 2, 15, 'partial', 150, 0.599, '-', 'Antarctica, s S. America'),
    (2018, 7, 13, 'partial', 117, 0.336, '-', 's Australia'),
    (2018, 8, 11, 'partial', 155, 0.737, '-', 'n Europe, ne Asia'),
    (2019, 1, 6, 'partial', 122, 0.715, '-', 'ne Asia, n Pacific'),
    (2019, 7, 2, 'total', 127, 1.046, '04m33s', 's Pacific, S. America (Total: s Pacific, Chile, Argentina)'),
    (2019, 12, 26, 'annular', 132, 0.97, '03m39s', 'Asia, Australia (Annular: Saudi Arabia, India, Sumatra, Borneo)'),
    (2020, 6, 21, 'annular', 137, 0.994, '00m38s', 'Africa, se Europe, Asia (Annular: c Africa, s Asia, China, Pacific)'),
    (2020, 12, 14, 'total', 142, 1.025, '02m10s', 'Pacific, s S. America, Antarctica (Total: s Pacific, Chile, Argentina, s Atlantic)'),
    (2021, 6, 10, 'annular', 147, 0.943, '03m51s', 'n N. America, Europe, Asia (Annular: n Canada, Greenland, Russia)'),
    (2021, 12, 4, 'total', 152, 1.037, '01m54s', 'Antarctica, S. Africa, s Atlantic (Total: Antarctica)'),
    (2022, 4, 30, 'partial', 119, 0.64, '-', 'se Pacific, s S. America'),
    (2022, 10, 25, 'partial', 124, 0.862, '-', 'Europe, ne Africa, Mid East, w Asia'),
    (2023, 4, 20, 'hybrid', 129, 1.013, '01m16s', 'se Asia, E. Indies, Australia, Philippines, N.Z. (Hybrid: Indonesia, Australia, Papua New Guinea)'),
    (2023, 10, 14, 'annular', 134, 0.952, '05m17s', 'N. America, C. America, S. America (Annular: w US, C. America, Colombia, Brazil)'),
    (2024, 4, 8, 'total', 139, 1.057, '04m28s', 'N. America, C. America (Total: Mexico, c US, e Canada)'),
    (2024, 10, 2, 'annular', 144, 0.933, '07m25s', 'Pacific, s S. America (Annular: s Chile, s Argentina)'),
    (2025, 3, 29, 'partial', 149, 0.938, '-', 'nw Africa, Europe, n Russia'),
    (2025, 9, 21, 'partial', 154, 0.855, '-', 's Pacific, N.Z., Antarctica'),
    (2026, 2, 17, 'annular', 121, 0.963, '02m20s', 's Argentina & Chile, s Africa, Antarctica (Annular: Antarctica)'),
    (2026, 8, 12, 'total', 126, 1.039, '02m18s', 'n N. America, w Africa, Europe (Total: Arctic, Greenland, Iceland, Spain)'),
    (2027, 2, 6, 'annular', 131, 0.928, '07m51s', 'S. America, Antarctica, w & s Africa (Annular: Chile, Argentina, Atlantic)'),
    (2027, 8, 2, 'total', 136, 1.079, '06m23s', 'Africa, Europe, Mid East, w & s Asia (Total: Morocco, Spain, Algeria, Libya, Egypt, Saudi Arabia, Yemen, Somalia)'),
    (2028, 1, 26, 'annular', 141, 0.921, '10m27s', 'e N. America, C. & S. America, w Europe, nw Africa (Annular: Ecuador, Peru, Brazil, Suriname, Spain, Portugal)'),
    (2028, 7, 22, 'total', 146, 1.056, '05m10s', 'SE Asia, E. Indies, Australia, N.Z. (Total: Australia, N.Z.)'),
    (2029, 1, 14, 'partial', 151, 0.871, '-', 'N. America, C. America'),
    (2029, 6, 12, 'partial', 118, 0.458, '-', 'Arctic, Scandinavia, Alaska, n Asia, n Canada'),
    (2029, 7, 11, 'partial', 156, 0.23, '-', 's Chile, s Argentina'),
    (2029, 12, 5, 'partial', 123, 0.891, '-', 's Argentina, s Chile, Antarctica'),
    (2030, 6, 1, 'annular', 128, 0.944, '05m21s', 'Europe, n Africa, Mid East, Asia, Arctic, Alaska (Annular: Algeria, Tunisia, Greece, Turkey, Russia, n. China, Japan)'),
    (2030, 11, 25, 'total', 133, 1.047, '03m44s', 's Africa, s Indian Oc., E. Indies, Australia, Antarctica (Total: Botswana, S. Africa, Australia)'),
    (2031, 5, 21, 'annular', 138, 0.959, '05m26s', 'Africa, s Asia, E. Indies, Australia (Annular: Angola, Congo, Zambia, Tanzania, s. India, Malaysia, Indonesia)'),
    (2031, 11, 14, 'hybrid', 143, 1.011, '01m08s', 'Pacific, s US, C. America, nw S. America (Hybrid: Pacific, Panama)'),
    (2032, 5, 9, 'annular', 148, 0.996, '00m22s', 's S. America, s Africa (Annular: s Atlantic)'),
    (2032, 11, 3, 'partial', 153, 0.855, '-', 'Asia'),
    (2033, 3, 30, 'total', 120, 1.046, '02m37s', 'N. America (Total: e Russia, Alaska)'),
    (2033, 9, 23, 'partial', 125, 0.689, '-', 's S. America, Antarctica'),
    (2034, 3, 20, 'total', 130, 1.046, '04m09s', 'Africa, Europe, w Asia (Total: Nigeria, Cameroon, Chad, Sudan, Egypt, Saudi Arabia, Iran, Afghanistan, Pakistan, India, China)'),
    (2034, 9, 12, 'annular', 135, 0.974, '02m58s', 'C. America, S. America (Annular: Chile, Bolivia, Argentina, Paraguay, Brazil)'),
    (2035, 3, 9, 'annular', 140, 0.992, '00m48s', 'Australia, New Zealand, s Pacific, Mexico, Antarctica (Annular: New Zealand, Pacific)'),
    (2035, 9, 2, 'total', 145, 1.032, '02m54s', 'e Asia, Pacific (Total: China, Korea, Japan, Pacific)'),
    (2036, 2, 27, 'partial', 150, 0.629, '-', 'Antarctica, s Australia, New Zealand'),
    (2036, 7, 23, 'partial', 117, 0.199, '-', 's Atlantic'),
    (2036, 8, 21, 'partial', 155, 0.862, '-', 'Alaska, Canada, Arctic, w Europe, nw Africa'),
    (2037, 1, 16, 'partial', 122, 0.705, '-', 'n Africa, Europe, Mid East, w Asia'),
    (2037, 7, 13, 'total', 127, 1.041, '03m58s', 'E. Indies, Australia, Pacific (Total: Australia, New Zealand)'),
    (2038, 1, 5, 'annular', 132, 0.973, '03m18s', "e N. America, n S. America, Atlantic, Africa, Europe (Annular: Cuba, Dom. Rep., Cote d'Ivoire, Ghana, Niger, Chad, Egypt)"),
    (2038, 7, 2, 'annular', 137, 0.991, '01m00s', 'N. & C. America, S. America, Africa, Europe, Mid East (Annular: Colombia, Venezuela, Mauritania, Morocco, Mali, Niger, Chad, Sudan, Ethiopia, Kenya)'),
    (2038, 12, 26, 'total', 142, 1.027, '02m18s', 'se Asia, E. Indies, Australia, New Zealand, s Pacific, Antarctica (Total: Australia, New Zealand, s Pacific)'),
    (2039, 6, 21, 'annular', 147, 0.945, '04m05s', 'N. America, w Europe (Annular: Alaska, n Canada, Norway, Sweden, Finland, Estonia, Russia)'),
    (2039, 12, 15, 'total', 152, 1.036, '01m51s', 's S. America, Antarctica (Total: Antarctica)'),
    (2040, 5, 11, 'partial', 119, 0.531, '-', 'Australia, N.Z., Antarctica'),
    (2040, 11, 4, 'partial', 124, 0.807, '-', 'N. & C. America'),
    (2041, 4, 30, 'total', 129, 1.019, '01m51s', 'Brazil, Africa, Mid East (Total: Angola, Congo, Uganda, Kenya, Somalia)'),
    (2041, 10, 25, 'annular', 134, 0.947, '06m07s', 'e Asia, Pacific (Annular: Mongolia, China, Korea, Japan, Pacific)'),
    (2042, 4, 20, 'total', 139, 1.061, '04m51s', 'e Asia, se Asia, Australia, Pacific (Total: Malaysia, Indonesia, Philippines, n Pacific)'),
    (2042, 10, 14, 'annular', 144, 0.93, '07m44s', 'se Asia, E. Indies, Australia, s Pacific, Antarctica (Annular: Thailand, Malaysia, Indonesia, Australia, New Zealand)'),
    (2043, 4, 9, 'total', 149, 1.01, '-', 'n N. America, ne Asia (Total: ne Russia)'),
    (2043, 10, 3, 'annular', 154, 0.95, '-', 'Antarctica, sw Australia, Indian Ocean (Annular: s Indian Ocean)'),
    (2044, 2, 28, 'annular', 121, 0.96, '02m27s', 'Antarctica, S. America (Annular: s Atlantic)'),
    (2044, 8, 23, 'total', 126, 1.036, '02m04s', 'n Asia, w N. America, Greenland (Total: Greenland, n Canada, Montana, N. Dakota)'),
)

LUNE = (
    (2015, 4, 4, 'total', 132, 1.001, '03h29m (00h05m)', 'Asia, Aus., Pacific, Americas'),
    (2015, 9, 28, 'total', 137, 1.276, '03h20m (01h12m)', 'e Pacific, Americas, Europe, Africa, w Asia'),
    (2016, 3, 23, 'penumbral', 142, -0.312, '-', 'Asia, Aus., Pacific, w Americas'),
    (2016, 9, 16, 'penumbral', 147, -0.064, '-', 'Europe, Africa, Asia, Aus., w Pacific'),
    (2017, 2, 11, 'penumbral', 114, -0.035, '-', 'Americas, Europe, Africa, Asia'),
    (2017, 8, 7, 'partial', 119, 0.246, '01h55m', 'Europe, Africa, Asia, Aus.'),
    (2018, 1, 31, 'total', 124, 1.315, '03h23m (01h16m)', 'Asia, Aus., Pacific, w N. America'),
    (2018, 7, 27, 'total', 129, 1.609, '03h55m (01h43m)', 'S. America, Europe, Africa, Asia, Aus.'),
    (2019, 1, 21, 'total', 134, 1.195, '03h17m (01h02m)', 'c Pacific, Americas, Europe, Africa'),
    (2019, 7, 16, 'partial', 139, 0.653, '02h58m', 'S. America, Europe, Africa, Asia, Aus.'),
    (2020, 1, 10, 'penumbral', 144, -0.116, '-', 'Europe, Africa, Asia, Aus.'),
    (2020, 6, 5, 'penumbral', 111, -0.405, '-', 'Europe, Africa, Asia, Aus.'),
    (2020, 7, 5, 'penumbral', 149, -0.644, '-', 'Americas, sw Europe, Africa'),
    (2020, 11, 30, 'penumbral', 116, -0.262, '-', 'Asia, Aus., Pacific, Americas'),
    (2021, 5, 26, 'total', 121, 1.009, '03h07m (00h15m)', 'e Asia, Australia, Pacific, Americas'),
    (2021, 11, 19, 'partial', 126, 0.974, '03h28m', 'Americas, n Europe, e Asia, Australia, Pacific'),
    (2022, 5, 16, 'total', 131, 1.414, '03h27m (01h25m)', 'Americas, Europe, Africa'),
    (2022, 11, 8, 'total', 136, 1.359, '03h40m (01h25m)', 'Asia, Australia, Pacific, Americas'),
    (2023, 5, 5, 'penumbral', 141, -0.046, '-', 'Africa, Asia, Australia'),
    (2023, 10, 28, 'partial', 146, 0.122, '01h17m', 'e Americas, Europe, Africa, Asia, Australia'),
    (2024, 3, 25, 'penumbral', 113, -0.132, '-', 'Americas'),
    (2024, 9, 18, 'partial', 118, 0.085, '01h03m', 'Americas, Europe, Africa'),
    (2025, 3, 14, 'total', 123, 1.178, '03h38m (01h05m)', 'Pacific, Americas, w Europe, w Africa'),
    (2025, 9, 7, 'total', 128, 1.362, '03h29m (01h22m)', 'Europe, Africa, Asia, Australia'),
    (2026, 3, 3, 'total', 133, 1.151, '03h27m (00h58m)', 'e Asia, Australia, Pacific, Americas'),
    (2026, 8, 28, 'partial', 138, 0.93, '03h18m', 'e Pacific, Americas, Europe, Africa'),
    (2027, 2, 20, 'penumbral', 143, -0.057, '-', 'Americas, Europe, Africa, Asia'),
    (2027, 7, 18, 'penumbral', 110, -1.068, '-', 'e Africa, Asia, Australia, Pacific'),
    (2027, 8, 17, 'penumbral', 148, -0.525, '-', 'Pacific, Americas'),
    (2028, 1, 12, 'partial', 115, 0.066, '00h56m', 'Americas, Europe, Africa'),
    (2028, 7, 6, 'partial', 120, 0.389, '02h21m', 'Europe, Africa, Asia, Australia'),
    (2028, 12, 31, 'total', 125, 1.246, '03h29m (01h11m)', 'Europe, Africa, Asia, Australia, Pacific'),
    (2029, 6, 26, 'total', 130, 1.844, '03h40m (01h42m)', 'Americas, Europe, Africa, Mid East'),
    (2029, 12, 20, 'total', 135, 1.117, '03h33m (00h54m)', 'Americas, Europe, Africa, Asia'),
    (2030, 6, 15, 'partial', 140, 0.502, '02h24m', 'Europe, Africa, Asia, Australia'),
    (2030, 12, 9, 'penumbral', 145, -0.163, '-', 'Americas, Europe, Africa, Asia'),
    (2031, 5, 7, 'penumbral', 112, -0.09, '-', 'Americas, Europe, Africa'),
    (2031, 6, 5, 'penumbral', 150, -0.82, '-', 'East Indies, Australia, Pacific'),
    (2031, 10, 30, 'penumbral', 117, -0.32, '-', 'Americas'),
    (2032, 4, 25, 'total', 122, 1.191, '03h31m (01h06m)', 'e Africa, Asia, Australia, Pacific'),
    (2032, 10, 18, 'total', 127, 1.103, '03h16m (00h47m)', 'Africa, Europe, Asia, Australia'),
    (2033, 4, 14, 'total', 132, 1.094, '03h35m (00h49m)', 'Europe, Africa, Asia, Australia'),
    (2033, 10, 8, 'total', 137, 1.35, '03h22m (01h19m)', 'Asia, Australia, Pacific, Americas'),
    (2034, 4, 3, 'penumbral', 142, -0.227, '-', 'Europe, Africa, Asia, Australia'),
    (2034, 9, 28, 'partial', 147, 0.014, '00h27m', 'Americas, Europe, Africa'),
    (2035, 2, 22, 'penumbral', 114, -0.053, '-', 'e Asia, Pacific, Americas'),
    (2035, 8, 19, 'partial', 119, 0.104, '01h17m', 'Americas, Europe, Africa, Mid East'),
    (2036, 2, 11, 'total', 124, 1.299, '03h22m (01h14m)', 'Americas, Europe, Africa, Asia, w Australia'),
    (2036, 8, 7, 'total', 129, 1.454, '03h51m (01h35m)', 'Americas, Europe, Africa, w Asia'),
    (2037, 1, 31, 'total', 134, 1.207, '03h17m (01h04m)', 'e Europe, e Africa, Asia, Australia, Pacific, N.A.'),
    (2037, 7, 27, 'partial', 139, 0.809, '03h12m', 'Americas, Europe, Africa'),
    (2038, 1, 21, 'penumbral', 144, -0.114, '-', 'Americas, Europe, Africa'),
    (2038, 6, 17, 'penumbral', 111, -0.527, '-', 'e N. America, C. & S. America, Africa, w Europe'),
    (2038, 7, 16, 'penumbral', 149, -0.495, '-', 'Australia, e Asia, Pacific, w Americas'),
    (2038, 12, 11, 'penumbral', 116, -0.289, '-', 'Europe, Africa, Asia, Australia'),
    (2039, 6, 6, 'partial', 121, 0.885, '02h59m', 'Europe, Africa, Asia, Australia'),
    (2039, 11, 30, 'partial', 126, 0.943, '03h26m', 'Europe, Africa, Asia, Australia, Pacific'),
    (2040, 5, 26, 'total', 131, 1.535, '03h31m (01h32m)', 'e Asia, Australia, Pacific, w Americas'),
    (2040, 11, 18, 'total', 136, 1.397, '03h40m (01h28m)', 'e Americas, Europe, Africa, Asia, Australia'),
    (2041, 5, 16, 'partial', 141, 0.064, '00h58m', 'e Americas, Europe, Africa, w Asia'),
    (2041, 11, 8, 'partial', 146, 0.17, '01h30m', 'Americas, Europe, Africa'),
    (2042, 4, 5, 'penumbral', 113, -0.218, '-', 'Asia, Australia, Pacific'),
    (2042, 9, 29, 'penumbral', 118, -0.003, '-', 'Asia, Australia, Pacific, Americas'),
    (2043, 3, 25, 'total', 123, 1.114, '03h35m (00h53m)', 'e Africa, e Europe, Asia, Australia, Pacific, w N.A.'),
    (2043, 9, 19, 'total', 128, 1.256, '03h26m (01h12m)', 'Americas, Europe, Africa, w Asia'),
    (2044, 3, 13, 'total', 133, 1.203, '03h29m (01h06m)', 'e S America, Europe, Africa, Asia, Australia'),
    (2044, 9, 7, 'total', 138, 1.046, '03h26m (00h34m)', 'e Asia, Australia, Pacific, Americas'),
)

# Traduction française des zones de visibilité : noms de lieux, puis points cardinaux abrégés (n, s, e, w, c…).
LIEUX_FR = {
    'Afghanistan': 'Afghanistan', 'Africa': 'Afrique', 'Alaska': 'Alaska', 'Algeria': 'Algérie',
    'Americas': 'Amériques', 'Angola': 'Angola', 'Antarctica': 'Antarctique', 'Arctic': 'Arctique',
    'Argentina': 'Argentine', 'Argentina & Chile': 'Argentine et Chili', 'Asia': 'Asie', 'Atlantic': 'Atlantique',
    'Aus.': 'Australie', 'Australia': 'Australie', 'Bolivia': 'Bolivie', 'Borneo': 'Bornéo', 'Botswana': 'Botswana',
    'Brazil': 'Brésil', 'C. & S. America': 'Amériques centrale et du Sud', 'C. America': 'Amérique centrale',
    'Cameroon': 'Cameroun', 'Canada': 'Canada', 'Chad': 'Tchad', 'Chile': 'Chili', 'China': 'Chine',
    'Colombia': 'Colombie', 'Congo': 'Congo', "Cote d'Ivoire": 'Côte d’Ivoire', 'Cuba': 'Cuba',
    'Dom. Rep.': 'Rép. dominicaine', 'E. Indies': 'Insulinde', 'East Indies': 'Insulinde', 'Ecuador': 'Équateur',
    'Egypt': 'Égypte', 'Estonia': 'Estonie', 'Ethiopia': 'Éthiopie', 'Europe': 'Europe', 'Faeroe Is': 'îles Féroé',
    'Finland': 'Finlande', 'Ghana': 'Ghana', 'Greece': 'Grèce', 'Greenland': 'Groenland', 'Iceland': 'Islande',
    'India': 'Inde', 'Indian': 'océan Indien', 'Indian Oc.': 'océan Indien', 'Indian Ocean': 'océan Indien',
    'Indonesia': 'Indonésie', 'Iran': 'Iran', 'Japan': 'Japon', 'Kenya': 'Kenya', 'Korea': 'Corée', 'Libya': 'Libye',
    'Madagascar': 'Madagascar', 'Malaysia': 'Malaisie', 'Mali': 'Mali', 'Mauritania': 'Mauritanie',
    'Mexico': 'Mexique', 'Mid East': 'Moyen-Orient', 'Mongolia': 'Mongolie', 'Montana': 'Montana', 'Morocco': 'Maroc',
    'N. & C. America': 'Amériques du Nord et centrale', 'N. America': 'Amérique du Nord', 'N. Dakota': 'Dakota du Nord',
    'N.A.': 'Amérique du Nord', 'N.Z.': 'Nouvelle-Zélande', 'New Zealand': 'Nouvelle-Zélande', 'Niger': 'Niger',
    'Nigeria': 'Nigeria', 'Norway': 'Norvège', 'Pacific': 'Pacifique', 'Pakistan': 'Pakistan', 'Panama': 'Panama',
    'Papua New Guinea': 'Papouasie-Nouvelle-Guinée', 'Paraguay': 'Paraguay', 'Peru': 'Pérou',
    'Philippines': 'Philippines', 'Portugal': 'Portugal', 'Russia': 'Russie', 'S. Africa': 'Afrique du Sud',
    'S. America': 'Amérique du Sud', 'S America': 'Amérique du Sud', 'Saudi Arabia': 'Arabie saoudite',
    'Scandinavia': 'Scandinavie', 'Somalia': 'Somalie', 'Spain': 'Espagne', 'Sudan': 'Soudan', 'Sulawesi': 'Sulawesi',
    'Sumatra': 'Sumatra', 'Suriname': 'Suriname', 'Svalbard': 'Svalbard', 'Sweden': 'Suède', 'Tanzania': 'Tanzanie',
    'Thailand': 'Thaïlande', 'Tunisia': 'Tunisie', 'Turkey': 'Turquie', 'U.S.': 'États-Unis', 'US': 'États-Unis',
    'Uganda': 'Ouganda', 'Venezuela': 'Venezuela', 'Yemen': 'Yémen', 'Zambia': 'Zambie',
}
DIRECTIONS_FR = {'n': 'N', 's': 'S', 'e': 'E', 'w': 'O', 'c': 'centre', 'ne': 'NE', 'nw': 'NO', 'se': 'SE',
                 'sw': 'SO', 'w & s': 'O et S', 'n.': 'N', 's.': 'S', 'SE': 'SE'}
TYPES_ZONE_FR = {'Total': 'totalité', 'Annular': 'annularité', 'Hybrid': 'hybride'}


def _lieu_fr(x: str) -> str:
    x = x.strip()
    if x in LIEUX_FR:
        return LIEUX_FR[x]
    for d in sorted(DIRECTIONS_FR, key=len, reverse=True):
        if x.startswith(d + ' ') and x[len(d) + 1:] in LIEUX_FR:
            return '%s (%s)' % (LIEUX_FR[x[len(d) + 1:]], DIRECTIONS_FR[d])
    return x


def zones(texte: str, langue: str = 'en') -> str:
    """Zones de visibilité dans la langue demandée (anglais : texte d'origine corrigé)."""
    if langue != 'fr':
        return texte
    principal, _, central = texte.partition('(')
    out = ', '.join(_lieu_fr(x) for x in principal.split(',') if x.strip())
    if central:
        genre, _, lieux = central.rstrip(')').partition(':')
        out += ' (%s : %s)' % (TYPES_ZONE_FR.get(genre.strip(), genre.strip()),
                               ', '.join(_lieu_fr(x) for x in lieux.split(',') if x.strip()))
    return out
