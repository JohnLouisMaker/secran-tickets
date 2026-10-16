import json

from config import ARQUIVO_DADOS


def carregar():
    if not ARQUIVO_DADOS.exists():
        return []

    try:
        dados = json.loads(ARQUIVO_DADOS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"O arquivo {ARQUIVO_DADOS} contém JSON inválido. "
            "Faça uma cópia e corrija/recupere o arquivo antes de continuar."
        ) from exc

    if not isinstance(dados, list):
        raise ValueError(f"{ARQUIVO_DADOS} precisa conter uma lista JSON.")

    por_id = {}
    sem_id = []

    for item in dados:
        if not isinstance(item, dict):
            continue
        ticket_id = str(item.get("ticket_id", "")).strip()
        if ticket_id:
            item["ticket_id"] = ticket_id
            por_id[ticket_id] = item
        else:
            sem_id.append(item)

    return list(por_id.values()) + sem_id


def salvar(dados):
    ARQUIVO_DADOS.parent.mkdir(parents=True, exist_ok=True)
    temporario = ARQUIVO_DADOS.with_suffix(".tmp")
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)

    temporario.write_text(conteudo, encoding="utf-8")
    temporario.replace(ARQUIVO_DADOS)
