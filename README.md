# LLM Corpus Builder

Un outil automatisé pour construire un corpus de documentation technique à partir des sources officielles GitHub, optimisé pour l'entraînement et l'alimentation de LLMs (Large Language Models).

## Description

Ce projet télécharge, convertit et organise automatiquement la documentation officielle de plus de 79 technologies majeures pour créer une base de connaissances structurée et indexée.

### Fonctionnalités principales

- **Téléchargement automatique** : Clone ou met à jour les dépôts Git de documentation officielle
- **Conversion universelle** : Convertit tous les formats (`.rst`, `.adoc`, `.html`, `.tex`, `.xml`) en Markdown uniforme
- **Organisation structurée** : Classe par catégorie, technologie et version
- **Indexation** : Génère des fichiers `manifest.jsonl` avec métadonnées pour intégration RAG
- **Support multi-versions** : Gère plusieurs versions d'une même technologie (ex: Symfony 2.0 à 8.1)

## Technologies couvertes

### Langages de programmation
- **PHP**, **Java** (JDK 23-26), **JavaScript** (ES2016-ES2025), **TypeScript**
- **Python** (3.9-3.12), **Go**, **Rust**, **C#**, **Kotlin**, **Swift**, **Ruby**

### Frameworks & Bibliothèques
- **Backend** : Symfony (50+ versions: 2.0 → 8.1)
- **Frontend** : React, Vue, Angular, Svelte, Next.js, Nuxt, Vite
- **CSS** : Tailwind CSS

### Bases de données
- **SQL** : PostgreSQL (60+ versions), MySQL, MariaDB, SQL Server
- **NoSQL** : MongoDB, Redis, Cassandra, CouchDB
- **Recherche** : Elasticsearch, ClickHouse
- **Autre** : SQLite, CockroachDB

### DevOps & Infrastructure
- **Conteneurs** : Docker, Kubernetes, Helm, Containerd
- **CI/CD** : GitHub Actions, GitLab CI, Jenkins, CircleCI, ArgoCD, Flux, Tekton
- **IaC** : Terraform, Ansible

### Observabilité & SRE
- Prometheus, Grafana, OpenTelemetry, Loki

### Runtime & Outils
- Node.js, npm, pnpm, Yarn, Git

### Architecture & Sécurité
- OWASP (CheatSheets, ASVS, Top10)
- Awesome Software Architecture
- Evolutionary Architecture

## Installation

### Prérequis

```bash
# Python 3.9+
python3 --version

# Pandoc (pour la conversion de formats)
sudo apt install pandoc  # Debian/Ubuntu
brew install pandoc      # macOS

# Git
git --version
```

### Dépendances Python

```bash
pip install pyyaml tqdm
```

## Configuration

Le fichier `repos.yaml` contient la configuration :

```yaml
output_root: skills_corpus    # Dossier de sortie
work_root: .work_repos         # Dossier temporaire pour les clones Git

defaults:
  max_header_level: 4          # Niveau de découpage des sections
  min_chunk_chars: 400         # Taille min des chunks
  max_chunk_chars: 12000       # Taille max (RAG-friendly)
  exclude_dirs:                # Dossiers à ignorer
    - node_modules
    - vendor
    - dist
    - build
    # ...

repos:
  - id: php-doc-en
    url: https://github.com/php/doc-en
    category: languages
    tech: php
    versions: ["master"]
    source: official
  # ...
```

## Utilisation

### Exécution complète

```bash
python3 llm_corpus_builder.py
```

Le script va :
1. Cloner/mettre à jour tous les repos configurés
2. Extraire et convertir la documentation
3. Organiser les fichiers par catégorie/tech/version
4. Générer les manifests JSONL

### Structure de sortie

```
skills_corpus/
├── languages/
│   ├── php/master/
│   │   ├── manifest.jsonl
│   │   └── *.md
│   ├── python/3.12/
│   └── javascript/es2024/
├── frameworks/
│   ├── symfony/7.2/
│   ├── react/main/
│   └── vue/main/
├── databases/
│   ├── postgresql/REL_17_STABLE/
│   └── mongodb/main/
├── devops/
├── containers/
└── sre/
```

### Format du manifest

Chaque `manifest.jsonl` contient une ligne JSON par fichier :

```json
{
  "id": "php-doc-en:master:a1b2c3d4e5",
  "file": "language/types/string.md",
  "text": "# String Type\n\nStrings in PHP...",
  "repo": "php-doc-en",
  "tech": "php",
  "version": "master",
  "source": "official",
  "git_sha": "abc123def456...",
  "file_path": "language/types/string.md",
  "original_file": "language/types/string.xml",
  "generated_at": "2026-01-16T14:30:00Z"
}
```

## Optimisations

### Pourquoi c'est lent au démarrage ?

Le script effectue des opérations lourdes :
- Télécharge/met à jour des centaines de repos Git
- Convertit des milliers de fichiers via Pandoc
- Traite plusieurs versions par technologie

### Conseils d'optimisation

1. **Première exécution** : Peut prendre plusieurs heures
2. **Exécutions suivantes** : Plus rapides (git fetch au lieu de clone)
3. **Réduire le scope** : Commentez les repos non nécessaires dans `repos.yaml`
4. **Parallélisation** : À implémenter (multiprocessing)

## Cas d'usage

- **Fine-tuning de LLMs** : Corpus d'entraînement spécialisé en dev
- **RAG (Retrieval-Augmented Generation)** : Base de connaissances pour chatbots techniques
- **Documentation consolidée** : Recherche unifiée dans plusieurs docs
- **Analyse de documentation** : Études comparatives entre versions

## Licence

Ce projet est un outil d'agrégation. Les documentations téléchargées conservent leurs licences respectives.

## Contribution

Pour ajouter une nouvelle technologie :

1. Éditez `repos.yaml`
2. Ajoutez une entrée dans la section appropriée
3. Testez avec `python3 llm_corpus_builder.py`

## Dépannage

### Erreur Pandoc

```bash
# Vérifier l'installation
pandoc --version

# Réinstaller si nécessaire
sudo apt install --reinstall pandoc
```

### Timeout Git

Si un repo est trop gros, augmentez le timeout ou utilisez `--depth=1` (déjà configuré).

### Processus bloqué

```bash
# Trouver le processus
ps aux | grep llm_corpus_builder.py

# Arrêter le processus
kill -9 <PID>
```

## Statistiques

- **79+ repos** configurés
- **200+ versions** de technologies
- **Catégories** : 8 (languages, frameworks, databases, devops, containers, sre, architecture, security)
- **Formats supportés** : `.md`, `.mdx`, `.rst`, `.adoc`, `.xml`, `.tex`, `.html`

## Auteur

DLDVLPR
