# 🔗 GEHU-P2P
_A Serverless Peer-to-Peer Messaging & File Sharing System for GEHU Lab Sessions_

## 📌 Overview

**GEHU-P2P** is a decentralized, serverless messaging and file-sharing system designed specifically for GEHU lab environments. It enables faculty members to broadcast files and messages directly to students over the same local network without relying on any centralized server, internet, or cloud-based tools.

## 🎯 Objective

To build a fully offline, peer-to-peer system for lab sessions that allows:
- Real-time file sharing and messaging
- Dynamic peer discovery over LAN
- Decentralized and scalable data propagation (BitTorrent-inspired)
- Seamless cross-platform compatibility
- Simple usage with zero setup

## 🧩 Key Features

- 🔁 **Fully Decentralized**: No central server or cloud storage required.
- 🌐 **Auto Discovery**: Students' devices automatically detect the teacher's session.
- ⚡ **Swarm-Based Distribution**: All peers help distribute file chunks.
- 📂 **Broadcast Capability**: Teachers send files/messages to all students at once.
- 🖥️ **Cross-Platform**: Works on Windows, Linux, and macOS.
- 🔐 **Session Authorization**: Only approved teacher devices can start a session.
- 📡 **Offline Mode**: Works entirely over the local network without internet access.

## 🌐 How It Works (BitTorrent-Inspired Workflow)

We follow a custom peer-to-peer chunk-sharing mechanism inspired by BitTorrent:

1. **Session Initialization**
   - The teacher starts a session on their system.
   - Their device acts as the primary seed (initial chunk source).

2. **Peer Discovery**
   - Students on the same local network automatically discover the session using LAN broadcasting (UDP multicast/mDNS/zeroconf).

3. **File Chunking**
   - The file is split into chunks.
   - The teacher's system sends chunks to the first few students.

4. **Swarm Distribution**
   - Students who receive chunks start sharing them with others (acting as secondary seeds).
   - This forms a **data swarm**, drastically speeding up file propagation.

5. **File Reconstruction**
   - Once all chunks are received, each student device reconstructs the complete file.

## 🚫 What We Avoid

- ❌ No centralized servers
- ❌ No internet or cloud dependency
- ❌ No static IPs or manual configurations
- ❌ No use of 3rd party file-sending libraries or cloud APIs

## 📦 Deliverables

- ✅ Working application prototype
- 📘 README with setup and explanation
- 🎥 Demo video walkthrough
- 🔒 Optional: Authentication mechanism for session creation

## 🚀 Impact

- ⏱️ Instant file sharing in labs
- 📡 100% local-first design
- 💡 Resilient, scalable architecture
- 📚 Smooth learning experience for students and teachers

---

> Made with ❤️ for GEHU Labs to speed up practical sessions and remove file-sharing pain.
