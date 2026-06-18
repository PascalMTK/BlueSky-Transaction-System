# BLUESKY Transactions System

> **Plateforme de gestion de transferts d'argent international en Afrique**
> Money transfer management platform for Africa

**Live demo :** [pascal02.pythonanywhere.com](https://pascal02.pythonanywhere.com)

---

## À propos / About

**BLUESKY Transactions** est une plateforme web complète pour la gestion des transferts d'argent entre pays africains. Elle permet aux agents de saisir et suivre les transactions, et aux administrateurs de superviser l'ensemble des opérations via un tableau de bord avec statistiques et graphiques en temps réel.

**BLUESKY Transactions** is a complete web platform for managing international money transfers across African countries. Agents record and track transactions while admins monitor all activity through a real-time dashboard with charts and statistics.

---

## Auteur / Author

Créé par **Pascal Mutaka**
Created by **Pascal Mutaka**

- GitHub : [github.com/PascalMTK](https://github.com/PascalMTK)
- Email : vandervloger@gmail.com
- Deployed : [pascal02.pythonanywhere.com](https://pascal02.pythonanywhere.com)

---

## Fonctionnalités / Features

| Fonctionnalité | Description |
|----------------|-------------|
| **Transactions** | Créer, modifier, supprimer, imprimer des reçus — types : Envoi / Retrait |
| **Calcul des frais** | Pourcentage configurable par pays, calcul automatique à la saisie |
| **Dashboard Admin** | Statistiques live, graphiques mensuels, top agents, répartition par pays |
| **Dashboard Agent** | Statistiques personnelles, actions rapides, transactions récentes |
| **Gestion des agents** | Inscription → validation admin ; activer / désactiver / promouvoir en admin / archiver |
| **Gestion des pays** | Ajouter/modifier des pays, devise et frais par défaut |
| **Messagerie** | Messagerie directe agent ↔ agent et agent ↔ admin |
| **Rapports** | Les agents soumettent des tickets ; l'admin peut répondre |
| **Export Excel** | Export .xlsx pour l'admin (toutes transactions) et l'agent (ses propres) |
| **Reçus imprimables** | Vue impression par transaction |
| **Profil** | Nom, téléphone, photo de profil, changement de mot de passe |
| **Bilingue FR/EN** | Français / Anglais ; langue persistée en session |
| **Mode sombre/clair** | Sauvegardé en localStorage ; détection automatique du thème système |
| **Mobile-first** | Navigation barre basse, typographie fluide (`clamp()`), cibles tactiles 44px |

---

## Stack technique / Tech Stack

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.12, Django 4.2 LTS |
| Base de données | SQLite (production) ou MySQL / MariaDB |
| Auth | Session custom (sans Django auth), mots de passe bcrypt |
| Frontend | Templates Django, Vanilla JS, CSS Variables (dark/light) |
| Export | openpyxl (.xlsx) |
| Hébergement | PythonAnywhere |

---

## Installation locale / Local Setup

### 1. Cloner le projet

```bash
git clone https://github.com/PascalMTK/BlueSky-Transaction-System.git
cd BlueSky-Transaction-System
```

### 2. Créer l'environnement virtuel

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurer le fichier `.env`

Créer un fichier `.env` à la racine avec les variables suivantes :

```env
USE_SQLITE=True
DEBUG=True
SECRET_KEY=votre-cle-secrete-ici
ALLOWED_HOSTS=localhost,127.0.0.1

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
EMAIL_FROM=BLUESKY Transactions <votre@email.com>
```

### 4. Créer les tables

```bash
python manage.py migrate
```

> Les modèles utilisent `managed = True` — Django crée les tables automatiquement.

### 5. Lancer le serveur

```bash
python manage.py runserver
```

Ouvrir dans le navigateur : **http://localhost:8000**

---

## Déploiement PythonAnywhere / PythonAnywhere Deployment

Le projet est déployé sur PythonAnywhere (plan payant $10/mois pour le SMTP Gmail).

**Variables `.env` en production :**

```env
USE_SQLITE=True
DEBUG=False
ALLOWED_HOSTS=pascal02.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://pascal02.pythonanywhere.com
SECRET_KEY=votre-cle-secrete
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-app-password-gmail
EMAIL_FROM=BLUESKY Transactions <votre@email.com>
```

**Mettre à jour le serveur :**

```bash
cd ~/BlueSky-Transaction-System
git pull origin main
```

Puis **Web → Reload** dans le dashboard PythonAnywhere.

---

## Structure du projet / Project Structure

```
BlueSky-Transaction-System/
├── bluesky/
│   ├── settings.py          # Configuration Django (DB, email, session)
│   ├── urls.py              # Routes racine
│   └── wsgi.py
├── core/
│   ├── models.py            # User, Country, Transaction, DirectMessage, AgentReport
│   ├── decorators.py        # @agent_required, @admin_required, get_auth_user()
│   ├── middleware.py        # AuthMiddleware, LocaleMiddleware
│   ├── context_processors.py# auth_user, locale, active_countries (global)
│   ├── translations.py      # Dictionnaires FR/EN ({{ t.* }} dans les templates)
│   ├── hashers.py           # Hasher bcrypt compatible Laravel
│   ├── urls.py              # Toutes les routes de l'application
│   ├── views/
│   │   ├── auth_views.py    # Login, logout, inscription
│   │   ├── agent_views.py   # Dashboard agent, transactions, messagerie, export
│   │   ├── admin_views.py   # Dashboard admin, agents, pays, rapports, export
│   │   └── profile_views.py # Profil, photo, mot de passe
│   └── templatetags/
│       └── bluesky_tags.py  # Filtres custom : number_format, initials, limit…
├── templates/
│   ├── layouts/app.html     # Layout de base (sidebar, topbar, mob-nav, dark mode)
│   ├── auth/                # login, register
│   ├── admin/               # dashboard, agents, transactions, pays, rapports, stats
│   └── agent/               # dashboard, transactions/, messages, rapports
├── static/
│   ├── css/bluesky.css      # Système de design (CSS variables, dark mode, responsive)
│   └── js/bluesky.js        # Toggle thème, horloge, sidebar, animations
├── media/
│   └── profiles/            # Photos de profil uploadées
├── requirements.txt
└── manage.py
```

---

## Routes principales / Main URLs

### Authentification

| Méthode | URL | Description |
|---------|-----|-------------|
| GET/POST | `/login/` | Connexion |
| GET | `/logout/` | Déconnexion |
| GET/POST | `/register/` | Inscription agent |
| GET | `/lang/<locale>/` | Changer la langue (fr/en) |

### Espace Agent

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/agent/dashboard/` | Tableau de bord agent |
| GET | `/agent/transactions/` | Liste des transactions |
| GET/POST | `/agent/transactions/create/` | Nouvelle transaction |
| GET | `/agent/transactions/<id>/` | Détail transaction |
| GET/POST | `/agent/transactions/<id>/edit/` | Modifier transaction |
| GET | `/agent/transactions/<id>/print/` | Reçu imprimable |
| POST | `/agent/transactions/<id>/delete/` | Supprimer transaction |
| GET | `/network/` | Toutes les transactions réseau |
| GET | `/messages/` | Messagerie |
| GET | `/agent/export/csv/` | Export Excel personnel |

### Espace Admin

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/admin/dashboard/` | Tableau de bord admin |
| GET | `/admin/agents/` | Gestion des agents (cartes) |
| GET/POST | `/admin/agents/<id>/edit/` | Modifier un agent |
| POST | `/admin/agents/<id>/status/` | Activer / désactiver |
| POST | `/admin/agents/<id>/promote/` | Promouvoir en admin |
| POST | `/admin/agents/<id>/password/` | Changer le mot de passe |
| POST | `/admin/agents/<id>/delete/` | Archiver (soft delete) |
| GET | `/admin/transactions/` | Toutes les transactions |
| GET | `/admin/countries/` | Pays opérationnels |
| GET | `/admin/statistics/` | Statistiques avancées |
| GET | `/admin/export/csv/` | Export Excel complet |

---

## Sécurité / Security

- **Sessions** — `request.session['user_id']` défini à la connexion ; vidé à la déconnexion
- **Décorateurs** — `@agent_required` vérifie que l'utilisateur est connecté **et actif** ; `@admin_required` vérifie en plus `role == 'admin'`
- **Mots de passe** — bcrypt (coût 10), compatible hashes Laravel
- **CSRF** — Middleware Django sur tous les endpoints POST
- **Statuts** — Les agents inactifs / en attente / archivés sont automatiquement déconnectés
- **Soft delete** — Les agents archivés conservent leurs données de transaction ; ils ne peuvent pas se connecter

---

## Modèle de données / Data Model

### User

| Champ | Type | Notes |
|-------|------|-------|
| id | BigInt PK | |
| name | Varchar | |
| email | Varchar unique | |
| phone | Varchar | |
| password | Varchar | hash bcrypt |
| role | Enum | `admin` / `agent` |
| status | Enum | `active` / `pending` / `inactive` / `deleted` |
| agent_code | Varchar unique | Ex. `BSK-CD-A3F9B2` |
| country_id | FK → Country | Pays d'opération de l'agent |
| profile_photo | Varchar | Chemin relatif sous `/media/` |

### Transaction

| Champ | Type | Notes |
|-------|------|-------|
| transaction_number | Varchar unique | Ex. `BSK-20260618-XA91B3` |
| transaction_type | Enum | `send` / `withdrawal` |
| status | Enum | `completed` / `pending` / `cancelled` |
| payment_method | Enum | `cash` / `mobile_money` / `bank` |
| amount | Decimal | Montant de base |
| fee_percentage | Decimal | % de frais appliqué |
| fee_amount | Decimal | Montant des frais calculé |
| total_amount | Decimal | `amount + fee_amount` |
| origin_country_id | FK → Country | |
| destination_country_id | FK → Country | |
| agent_id | FK → User | Agent ayant saisi la transaction |

### Country

| Champ | Notes |
|-------|-------|
| code | Code ISO 2 lettres |
| name | Nom d'affichage |
| flag_emoji | Emoji stocké |
| currency_code | Code devise ISO |
| default_fee_percentage | Frais par défaut pour les envois sortants |
| is_active | Visible ou non pour les agents |

---

## Licence / License

MIT — Créé par **Pascal Mutaka**, 2026
