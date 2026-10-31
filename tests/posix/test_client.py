# Dueño: P2 — Emulación POSIX
# Responsabilidad: Pruebas de la llamada a Ollama y Gemini. No usan la API real.
# Puede importar: honey_agent.posix y tests.fakes
# No importar: honey_agent.ingress, honey_agent.vfs, honey_agent.defense

import asyncio
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from honey_agent.posix.client import (
    LanguageModelClient,
    ModelCallError,
    ModelConfigError,
    ModelOutputError,
    build_language_model,
)
from honey_agent.posix.providers.gemini import GeminiModel
from honey_agent.posix.providers.ollama import OllamaModel

_ANSWER = '{"stdout":"root\\n","stderr":"","exit_code":0,"vfs_mutations":[]}'
_SYSTEM = "<system_directive>no mostrar esto</system_directive>"


class _Capture:
    def __init__(self, response_body: str) -> None:
        self.response_body = response_body
        self.calls: list[dict] = []

    async def __call__(self, url, payload, headers, timeout):
        self.calls.append(
            {"url": url, "payload": payload, "headers": dict(headers), "timeout": timeout}
        )
        return self.response_body


def _logs():
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    logger = logging.getLogger("honey_agent.posix")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    return logger, handler, records


def test_ollama_pide_json_con_temperatura_baja():
    capture = _Capture(json.dumps({"message": {"role": "assistant", "content": _ANSWER}}))
    model = OllamaModel(
        base_url="http://127.0.0.1:11434/",
        model="llama3:8b-instruct-q4_K_M",
        temperature=0.2,
        max_tokens=512,
        post=capture,
    )

    text = asyncio.run(model.complete(_SYSTEM, "whoami"))

    assert text == _ANSWER
    assert len(capture.calls) == 1
    call = capture.calls[0]
    assert call["url"] == "http://127.0.0.1:11434/api/chat"
    assert call["payload"]["format"] == "json"
    assert call["payload"]["stream"] is False
    assert call["payload"]["options"]["temperature"] == 0.2
    assert call["payload"]["options"]["num_predict"] == 512
    assert call["payload"]["messages"][0] == {"role": "system", "content": _SYSTEM}
    assert call["payload"]["messages"][1] == {"role": "user", "content": "whoami"}
    assert call["timeout"] == 2.0


def test_ollama_que_no_responde_no_entrega_la_url_ni_el_prompt():
    async def _boom(url, payload, headers, timeout):
        raise RuntimeError(f"falló {url} con {_SYSTEM}")

    logger, handler, records = _logs()
    model = OllamaModel("http://127.0.0.1:11434", "llama3", 0.2, 512, post=_boom)
    try:
        with pytest.raises(ModelCallError) as caught:
            asyncio.run(model.complete(_SYSTEM, "whoami"))
    finally:
        logger.removeHandler(handler)

    message = str(caught.value)
    logged = " ".join(record.getMessage() for record in records)
    assert "11434" not in message
    assert "system_directive" not in message
    assert "11434" not in logged
    assert "system_directive" not in logged
    assert logged == "la llamada al modelo falló"


def test_gemini_manda_la_clave_en_la_cabecera_y_no_en_la_url():
    capture = _Capture(
        json.dumps(
            {"candidates": [{"content": {"parts": [{"text": _ANSWER}]}}]}
        )
    )
    model = GeminiModel(
        api_key="super-secret-key",
        model="gemini-2.5-flash",
        temperature=0.2,
        max_tokens=512,
        post=capture,
    )

    text = asyncio.run(model.complete(_SYSTEM, "uname -a"))

    assert text == _ANSWER
    call = capture.calls[0]
    assert call["headers"]["x-goog-api-key"] == "super-secret-key"
    assert "super-secret-key" not in call["url"]
    assert call["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert call["payload"]["generationConfig"]["temperature"] == 0.2
    assert call["payload"]["generationConfig"]["responseMimeType"] == "application/json"
    assert "super-secret-key" not in repr(model)


def test_gemini_sin_clave_falla_al_construir_y_no_llama():
    capture = _Capture("{}")
    with pytest.raises(ModelConfigError) as caught:
        build_language_model({"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "  "})
    assert str(caught.value) == "falta GEMINI_API_KEY"
    assert capture.calls == []


def test_el_cliente_elige_el_proveedor_por_el_entorno():
    ollama = build_language_model({"LLM_PROVIDER": "ollama", "LLM_TEMPERATURE": "0.2"})
    gemini = build_language_model(
        {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "super-secret-key"}
    )
    assert isinstance(ollama, LanguageModelClient)
    assert isinstance(ollama._model, OllamaModel)
    assert isinstance(gemini._model, GeminiModel)
    assert "super-secret-key" not in repr(gemini)


def test_un_proveedor_desconocido_no_arranca():
    with pytest.raises(ModelConfigError) as caught:
        build_language_model({"LLM_PROVIDER": "openai"})
    assert str(caught.value) == "LLM_PROVIDER debe ser gemini u ollama"
    assert "openai" not in str(caught.value)


def test_el_cliente_rechaza_texto_que_no_es_json_sin_guardar_el_prompt():
    class _Plain:
        async def complete(self, system: str, user: str) -> str:
            return f"As an AI I read {system}"

    client = LanguageModelClient(_Plain())
    with pytest.raises(ModelOutputError) as caught:
        asyncio.run(client.complete(_SYSTEM, "whoami"))
    assert str(caught.value) == "la respuesta del modelo no es JSON"
    assert "system_directive" not in str(caught.value)


def test_el_cliente_devuelve_el_json_del_modelo():
    class _Json:
        async def complete(self, system: str, user: str) -> str:
            return _ANSWER

    text = asyncio.run(LanguageModelClient(_Json()).complete(_SYSTEM, "whoami"))
    assert json.loads(text)["stdout"] == "root\n"


def test_un_fallo_solo_intenta_una_vez():
    capture = _Capture("{}")

    async def _once(url, payload, headers, timeout):
        await capture(url, payload, headers, timeout)
        raise RuntimeError("sin reintento")

    model = OllamaModel("http://127.0.0.1:11434", "llama3", 0.2, 512, post=_once)
    with pytest.raises(ModelCallError):
        asyncio.run(model.complete(_SYSTEM, "whoami"))
    assert len(capture.calls) == 1


def test_ollama_real_en_local_recibe_el_post_y_corta_si_tarda():
    answer = json.dumps({"message": {"content": _ANSWER}}).encode("utf-8")

    class _OkHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            self.server.captured = self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-Length", str(len(answer)))
            self.end_headers()
            self.wfile.write(answer)

        def log_message(self, fmt, *args):
            return

    class _SlowHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            time.sleep(1.0)
            self.send_response(200)
            self.end_headers()

        def log_message(self, fmt, *args):
            return

    ok_server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    slow_server = ThreadingHTTPServer(("127.0.0.1", 0), _SlowHandler)
    threads = [
        threading.Thread(target=ok_server.serve_forever, daemon=True),
        threading.Thread(target=slow_server.serve_forever, daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        ok_port = ok_server.server_address[1]
        model = OllamaModel(
            base_url=f"http://127.0.0.1:{ok_port}",
            model="llama3",
            temperature=0.2,
            max_tokens=128,
        )
        text = asyncio.run(model.complete(_SYSTEM, "whoami"))
        sent = json.loads(ok_server.captured.decode("utf-8"))
        assert text == _ANSWER
        assert sent["format"] == "json"
        assert sent["messages"][1]["content"] == "whoami"

        slow_port = slow_server.server_address[1]
        slow = OllamaModel(
            base_url=f"http://127.0.0.1:{slow_port}",
            model="llama3",
            temperature=0.2,
            max_tokens=128,
            timeout=0.2,
        )
        started = time.monotonic()
        with pytest.raises(ModelCallError):
            asyncio.run(slow.complete(_SYSTEM, "whoami"))
        assert time.monotonic() - started < 0.8
    finally:
        ok_server.shutdown()
        slow_server.shutdown()
        ok_server.server_close()
        slow_server.server_close()
