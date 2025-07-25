# GEHU-P2P: Decentralized P2P Messaging & File Sharing

---

## 🚀 Overview

GEHU P2P is a **fully decentralized, serverless, peer-to-peer (P2P)** system designed to streamline file and message distribution during lab sessions at GEHU. It eliminates the need for central servers, cloud storage, or internet connectivity, allowing teachers to quickly and seamlessly share resources with students directly over the local campus network (Wi-Fi or LAN).

Inspired by the efficiency of BitTorrent protocols, GEHU LabShare ensures that once a teacher initiates a session, files are propagated across all connected student devices, with each student's machine also acting as a relay to help distribute content. This minimizes delays, reduces server load, and provides a robust, offline-capable solution for lab environments.

## ✨ Features

* **Fully Decentralized:** No central server or third-party intermediary. All communication happens directly between peers.
* **Auto-Discovery:** Devices automatically detect and connect to a teacher's session when it starts, similar to how BitTorrent clients discover peers.
* **Broadcast Capability:** Teachers can instantly broadcast files (e.g., starter code, datasets, configurations) or messages to all connected students.
* **Efficient Content Distribution:** Students who receive file chunks also become broadcasters, helping distribute the content to other peers, significantly speeding up transfers in a lab setting.
* **Cross-Platform Support:** Built to work seamlessly across Windows, macOS, and Linux.
* **Offline Usage:** Operates entirely within a local network; no internet access required.
* **Simple User Interface:** Intuitive PyQt5-based UI for minimal setup and an easy learning curve for both teachers and students.
* **Security:** Mechanisms to ensure only authorized teacher systems can initiate sessions and broadcast content (details to be implemented during development).

## 🛠️ Technology Stack

* **Python:** Core programming language.
* **PyQt5:** For building the cross-platform graphical user interface (GUI).
* **Networking Libraries:** (e.g., `socket`, `asyncio`, potentially `multicast`) for P2P communication, auto-discovery, and file transfer.
* **Hashing Libraries:** For file integrity verification and chunk identification.
* **Serialization Libraries:** For structuring messages and file metadata.

## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.8+ installed.
* `pip` (Python package installer).


