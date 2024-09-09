from os import environ
from assistant import get_language, assistant_data


def test_support_french():
    detected_language = get_language(
        "Bonjour, veuillez m'envoyer les recommandations d'agriculture au Kenya"
    )
    assert detected_language == "fr"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-fr"
    assert system_prompt == environ["SYSTEM_PROMPT_fr"]
    assert rag_prompt == environ["RAG_PROMPT_fr"]
    assert ragless_prompt == environ["RAGLESS_PROMPT_fr"]

    detected_language = get_language(
        "Hello, please send me the recommendations of agriculture in Kenya"
    )
    assert detected_language == "en"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-en"
    assert system_prompt == environ["SYSTEM_PROMPT_en"]
    assert rag_prompt == environ["RAG_PROMPT_en"]
    assert ragless_prompt == environ["RAGLESS_PROMPT_en"]

    detected_language = get_language(
        "Hujambo, tafadhali nitumie mapendekezo ya kilimo nchini Kenya"
    )
    assert detected_language == "sw"
    knowledge_base = assistant_data[detected_language]["knowledge_base"]
    system_prompt = assistant_data[detected_language]["system_prompt"]
    rag_prompt = assistant_data[detected_language]["rag_prompt"]
    ragless_prompt = assistant_data[detected_language]["ragless_prompt"]
    assert knowledge_base.name == "EPPO-datasheets-sw"
    assert system_prompt == environ["SYSTEM_PROMPT_sw"]
    assert rag_prompt == environ["RAG_PROMPT_sw"]
    assert ragless_prompt == environ["RAGLESS_PROMPT_sw"]
