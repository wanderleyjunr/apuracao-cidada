from confere.bweb import convert

H = dict(NR_TURNO="1", SG_UF="MG", CD_MUNICIPIO="53112", NR_ZONA="170", NR_SECAO="37", QT_APTOS="280", QT_COMPARECIMENTO="195",
         DT_BU_RECEBIDO="04/10/2026 18:47:10", NR_URNA_EFETIVADA="2250280")


def row(office, number, votes, vtype="1"):
    return {**H, "CD_CARGO_PERGUNTA": office, "NR_VOTAVEL": number, "QT_VOTOS": str(votes), "CD_TIPO_VOTAVEL": vtype}


def test_convert_groups_by_zone_and_office():
    out = convert([row("1", "13", 109), row("1", "22", 63), row("1", "95", 2, "2"), row("1", "96", 4, "3"),
                   row("3", "10", 120), row("7", "1234", 5)], {"1", "3"})
    sec = out[("1", "mg", 53112, 170)]["sections"]["37"]
    assert sec["votes"] == {"1": {"13": 109, "22": 63, "BRAN": 2, "NULO": 4}, "3": {"10": 120}}
    assert sec["apt"] == 280 and sec["comp"] == 195 and sec["urna"] == "2250280"


def test_city_totals_for_deputies():
    from confere.bweb import city_totals
    out = city_totals([row("6", "2222", 10), row("6", "2222", 5), row("7", "13013", 3), row("1", "13", 1)], {"6", "7"})
    assert out[("1", "mg", 53112)] == {"6": {"2222": 15}, "7": {"13013": 3}}
