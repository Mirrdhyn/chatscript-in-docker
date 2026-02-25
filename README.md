# chatscript-in-docker

Minimal [ChatScript 14.1](https://github.com/ChatScript/ChatScript) engine in Docker, bundled with **KubeBot** -- a bilingual (EN/FR) chatbot that combines small talk and a Kubernetes FAQ based on [kubespec.dev](https://kubespec.dev/).

## Quick Start

```bash
git clone https://github.com/Mirrdhyn/chatscript-in-docker.git
cd chatscript-in-docker
docker compose up --build
```

The ChatScript server starts on port **1024**. The first build compiles the engine from source (~10s).

## What's Inside

KubeBot is a single unified bot that handles both casual conversation and Kubernetes questions. Topic routing is automatic -- ask about Pods and you get K8s answers, say hello and you get small talk.

**Small talk topics**: greetings, mood, bot identity, weather, hobbies, thanks, opinions

**Kubernetes FAQ topics** (~150 Q&A, based on kubespec.dev):
- **Workloads**: Pod, Deployment, StatefulSet, DaemonSet, ReplicaSet, Job, CronJob
- **Networking**: Service, Ingress, IngressClass, NetworkPolicy, EndpointSlice
- **Storage**: PersistentVolume, PersistentVolumeClaim, StorageClass, CSIDriver
- **Configuration**: ConfigMap, Secret, HPA, LimitRange, ResourceQuota, PodDisruptionBudget
- **Access Control**: RBAC, ClusterRole, Role, RoleBinding, ServiceAccount
- **Cluster**: Namespace, Node, Event
- **Administration**: ValidatingWebhook, MutatingWebhook, ValidatingAdmissionPolicy, PriorityClass, RuntimeClass

## Build

The Dockerfile uses a multi-stage build: it compiles the ChatScript binary from the C++ source in `engine/SRC/`, then produces a minimal runtime image. No pre-built binary is needed.

```bash
docker build -t chatscript-bot .
```

## Compile the Engine Natively (optional)

If you want to run ChatScript outside Docker (e.g. to rebuild topics or test locally), you need to compile the binary for your platform.

### Prerequisites

- `g++` (or `clang++` on macOS)
- `make`
- `libcurl` dev headers (`libcurl4-openssl-dev` on Debian/Ubuntu, `brew install curl` on macOS)

### Linux

```bash
cd engine/SRC
make clean server
# Binary: ../BINARIES/ChatScript
```

### macOS

```bash
cd engine/SRC
make clean standalone
# Binary: ../BINARIES/ChatScript
# You may need: codesign --sign - ../BINARIES/ChatScript
```

> **Note**: on macOS, compile the `standalone` target (not `server`). The `server` target uses `libev` which may require additional setup on macOS.

### Rebuild Topics

The pre-compiled topics are in `engine/TOPIC/`. If you modify the bot source files in `RAWDATA/BOT/`, you need to rebuild them:

```bash
# From the repo root (not engine/SRC/)
mkdir -p engine/BINARIES engine/LOGS engine/USERS engine/TMP
cd engine/BINARIES
./ChatScript local build0=files0.txt    # Rebuild ontology
./ChatScript local build1=filesBot.txt  # Rebuild bot topics
```

The compiled topics in `engine/TOPIC/BUILD0/` and `BUILD1/` are then ready for Docker.

## Run

### With docker compose

```bash
docker compose up -d
```

User data and logs are persisted in `./data/users/` and `./data/logs/`.

### With docker run

```bash
docker run -d --name kubebot \
  -p 1024:1024 \
  -v $(pwd)/data/users:/opt/ChatScript/USERS \
  -v $(pwd)/data/logs:/opt/ChatScript/LOGS \
  chatscript-bot
```

## Query the Bot via TCP

ChatScript uses a raw TCP protocol on port 1024. The message format is:

```
<username>\0<botname>\0<message>\0
```

where `\0` is a null byte. The server responds with the bot's reply as plain text.

### Using netcat

```bash
printf 'user1\0\0Hello\0' | nc localhost 1024
printf 'user1\0\0What is a Pod?\0' | nc localhost 1024
printf 'user1\0\0Quels sont les types de Service?\0' | nc localhost 1024
```

### Using Python

```python
import socket

def ask_bot(message, user="user1", bot="", host="localhost", port=1024):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        payload = f"{user}\0{bot}\0{message}\0"
        s.sendall(payload.encode("utf-8"))
        return s.recv(4096).decode("utf-8")

print(ask_bot("Hello"))
print(ask_bot("What is a Deployment?"))
print(ask_bot("Comment configurer un Ingress?"))
```

## HTTP API with nginx Reverse Proxy

ChatScript speaks TCP, not HTTP. For frontend integration, this repo includes a production-ready stack: **nginx** (rate limiting + API key) → **Python middleware** (HTTP-to-TCP bridge) → **ChatScript**.

```
Browser/Frontend ──POST /api/chat──▶ nginx:80 ──▶ middleware:8000 ──▶ chatscript:1024
                                     (API key     (HTTP→TCP         (ChatScript
                                      + throttle)  translation)      engine)
```

### Setup

1. Set your API key:

```bash
export VALID_API_KEY="my-secret-key-123"
```

2. Start the production stack:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### Query via HTTP

```bash
# Ask a question
curl -s -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $VALID_API_KEY" \
  -d '{"user": "user1", "message": "What is a Pod?"}' | jq

# Health check (no API key required)
curl -s http://localhost/health | jq

# Missing API key → 401
curl -s -X POST http://localhost/api/chat \
  -d '{"user": "u1", "message": "hi"}' | jq
```

Response format:

```json
{"reply": "A Pod is the smallest deployable unit in Kubernetes..."}
```

### Rate Limiting

nginx enforces **10 requests/second per IP** with a burst of 20. Exceeding the limit returns HTTP 429.

### Frontend Integration (JavaScript)

```javascript
async function askKubeBot(message, user = "anonymous") {
  const res = await fetch("https://your-domain/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "your-api-key",
    },
    body: JSON.stringify({ user, message }),
  });
  const data = await res.json();
  return data.reply;
}
```

### Configuration Files

| File | Purpose |
|------|---------|
| `nginx.conf` | Rate limiting, API key validation, reverse proxy |
| `middleware.py` | HTTP-to-TCP bridge (Python stdlib, no dependencies) |
| `docker-compose.prod.yml` | Full stack: nginx + middleware + ChatScript |

## Project Structure

```
chatscript-in-docker/
├── Dockerfile                 # Multi-stage: compile + runtime
├── docker-compose.yml         # Direct TCP access (dev)
├── docker-compose.prod.yml    # nginx + middleware + ChatScript (prod)
├── nginx.conf                 # Rate limiting + API key validation
├── middleware.py               # HTTP-to-TCP bridge
├── .dockerignore
├── .gitignore
├── LICENSE
├── README.md
├── RAWDATA/                   # Bot source files
│   ├── files0.txt             # Build 0 manifest (ontology + worlddata)
│   ├── filesBot.txt           # Build 1 manifest (bot topics)
│   ├── ONTOLOGY/              # ChatScript ontology data
│   ├── WORLDDATA/             # World knowledge facts
│   ├── QUIBBLE/               # Fallback Eliza-like responses
│   └── BOT/                   # KubeBot source
│       ├── simplecontrol.top  # Main control flow
│       ├── introductions.top  # Welcome messages
│       ├── smalltalk.top      # Casual conversation
│       ├── workloads.top      # K8s workloads FAQ
│       ├── networking.top     # K8s networking FAQ
│       ├── storage.top        # K8s storage FAQ
│       ├── configuration.top  # K8s config FAQ
│       ├── access_control.top # K8s RBAC FAQ
│       ├── cluster.top        # K8s cluster FAQ
│       ├── administration.top # K8s admin FAQ
│       └── keywordless.top    # Fallback responses
└── engine/                    # ChatScript 14.1 engine
    ├── SRC/                   # C++ source (compiled during docker build)
    ├── DICT/ENGLISH/          # English dictionary
    ├── LIVEDATA/              # Runtime language data
    └── TOPIC/                 # Pre-compiled topics
        ├── BUILD0/            # Ontology + worlddata
        └── BUILD1/            # Bot topics
```

## Create Your Own Bot

1. Create a folder under `RAWDATA/` with your `.top` files (use `RAWDATA/BOT/` as reference)
2. Create a `filesMyBot.txt` manifest listing your folders
3. Compile topics locally (see [Rebuild Topics](#rebuild-topics))
4. Rebuild: `docker build -t my-chatscript-bot .`

See the [ChatScript documentation](https://github.com/ChatScript/ChatScript/tree/master/WIKI) for the full scripting reference.

## Conversation Examples

```
user1: > Hello
KubeBot: Hi there!

user1: > What is a Pod?
KubeBot: A Pod is the smallest deployable unit in Kubernetes. It represents
one or more containers that share networking and storage.

user1: > What are the Service types in Kubernetes?
KubeBot: Kubernetes supports four Service types: ClusterIP (default, internal
cluster IP only), NodePort (exposes on each node's IP at a static port),
LoadBalancer (provisions an external load balancer), and ExternalName (maps
to a DNS name via CNAME record).

user1: > Comment fonctionne le RBAC?
KubeBot: Le RBAC (controle d'acces base sur les roles) regule l'acces aux
ressources Kubernetes en fonction des roles des utilisateurs ou des comptes
de service.

user1: > How are you?
KubeBot: I'm doing great, thanks for asking!
```

## License

MIT License - see [LICENSE](LICENSE).
