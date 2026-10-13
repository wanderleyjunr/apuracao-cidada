from confere.candidate_pages import age_on, assets_by_candidate, candidate_doc


def test_candidate_doc_drops_personal_data():
    row = {"SQ_CANDIDATO": "1", "NM_URNA_CANDIDATO": "FULANO", "NR_CPF_CANDIDATO": "12345678900", "DS_EMAIL": "a@b.c",
           "NR_TITULO_ELEITORAL_CANDIDATO": "999", "DT_NASCIMENTO": "18/08/1979", "SG_PARTIDO": "XYZ", "NM_FEDERACAO": "#NULO#"}
    doc = candidate_doc(row)
    assert doc == {"name": "FULANO", "party": "XYZ", "sq": "1", "age": 47}
    assert "12345678900" not in str(doc) and "a@b.c" not in str(doc)


def test_age_and_assets():
    assert age_on("05/10/1980") == 45 and age_on("x") is None
    a = assets_by_candidate([{"SQ_CANDIDATO": "1", "VR_BEM_CANDIDATO": "1000,50", "DS_TIPO_BEM_CANDIDATO": "Casa"},
                             {"SQ_CANDIDATO": "1", "VR_BEM_CANDIDATO": "10", "DS_TIPO_BEM_CANDIDATO": "Carro"}])
    assert a["1"]["total"] == 1010.5 and a["1"]["items"][0]["type"] == "Casa"
