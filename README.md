# Csango Knowledge Assistant

Chatbot local con Python y Ollama centrado en responder preguntas sobre los Csango. La aplicacion usa un modelo local y una base documental editable para generar respuestas sobre historia, cultura, lengua, identidad y contexto.

## Que Incluye

- Interfaz web de chat.
- Backend en Python sin dependencias externas.
- Conexion local con Ollama.
- Memoria de conversacion durante la sesion.
- Base de conocimiento editable en `data/profile.json` y `data/notes.md`.
- Recuperacion simple de fragmentos relevantes antes de generar la respuesta con IA.

## Requisitos

- Python 3.10 o superior.
- Ollama instalado.
- Un modelo descargado en Ollama, por ejemplo:

```powershell
ollama pull llama3.2:3b
```

Si el equipo tiene poca RAM, conviene empezar con modelos pequenos como `llama3.2:3b` o `phi3:mini`.

## Ejecutar

Primero comprueba que Ollama esta disponible:

```powershell
ollama --version
```

Despues ejecuta la app:

```powershell
cd C:\Users\marcp\Desktop\csango-ai-assistant
python server.py
```

Abre en el navegador:

```text
http://127.0.0.1:8000
```

## Configurar El Modelo

Por defecto usa `llama3.2:3b`. Puedes cambiarlo con una variable de entorno:

```powershell
$env:OLLAMA_MODEL="phi3:mini"
python server.py
```

## Personalizar La Base De Conocimiento

Edita:

- `data/profile.json`: datos estructurados sobre el tema.
- `data/notes.md`: textos, fuentes, notas o documentos sobre los Csango.

La aplicacion selecciona fragmentos relevantes de esos archivos y se los pasa al modelo local para generar respuestas.

## Estructura

```text
csango-ai-assistant/
├── app/
│   ├── knowledge.py
│   └── ollama_client.py
├── data/
│   ├── notes.md
│   └── profile.json
├── static/
│   ├── app.js
│   └── styles.css
├── templates/
│   └── index.html
├── server.py
└── README.md
```

## Ideas Para Mejorar

- Guardar conversaciones en SQLite.
- Anadir subida de documentos para ampliar la base de conocimiento.
- Usar embeddings y busqueda vectorial para RAG real.
- Anadir mas fuentes contrastadas sobre los Csango.
- Publicar capturas y explicacion en un portfolio.
