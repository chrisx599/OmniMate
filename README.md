# OmniMate - Real-time Multi-modal Agent Application

OmniMate is a real-time, multi-modal agent application that enhances user productivity by tracking and analyzing screen activity. Using advanced memory storage technology, it captures and persistently records user actions and screen dynamics. Whether it's for video conferencing, document collaboration, tutorial learning, or entertainment interactions, OmniMate provides real-time assistance with intelligent summaries and optimization suggestions based on user preferences.

## Key Features

- **Multi-modal Real-time Perception**: Captures visual, operational, and textual interactions to build dynamic, cross-context behavior models.
- **Persistent Memory Storage**: Utilizes a hierarchical memory storage technique (original details, redundancy-reduced summaries, user preference mapping) for long-term, cross-scenario personalized memory retrieval.
- **User Preference-Driven Graph Storage**: Integrates user preferences with screen actions and operation tracks to create detailed dynamic user profiles.
- **Lightweight Deployment**: Built on vLLM for distributed deployment, optimized for high-concurrency, real-time inference (every 5 seconds).
- **Cross-context Behavior Modeling**: Breaks the limitations of single-context models, offering personalized, multi-scenario task efficiency enhancement.

## Technical Innovations

### 1. Multi-modal Real-time Perception & Memory Storage
OmniMate captures user behavior across various modes (visual, operation track, text interaction) and uses hierarchical memory to store:
- **Original Details**: Raw screenshots and activity.
- **Summary Information**: Redundancy-free semantic vectors using BGE-M3 model.
- **User Preference**: Dynamic user profile constructed with graph structures, capturing frequent actions and relationships.

### 2. Lightweight & Efficient Inference
- **vLLM-based Distributed Deployment**: Optimizes for real-time, high-frequency inference.
- **Task Parallelization**: Uses prompt for generating detailed outputs, summaries, and user preference models in parallel, improving efficiency by 3x over traditional single-task models.

### 3. User Preference-Driven Graph Storage
- **User Preferences**: OmniMate models preferences and behavior by linking screen activities to dynamic, personalized graphs, allowing for context-aware suggestions and improvements.

## Application Areas

### Real-World Problem Solving

OmniMate aims to solve the core pain points:
- **Multimodal Analysis**: Traditional systems focus on single-context interactions, but OmniMate offers dynamic, cross-context behavior modeling, optimizing long-term task efficiency.
- **Cross-Scenario Assistance**: Unlike current tools like screen recorders, OmniMate autonomously provides assistance by monitoring real-time activities and summarizing key information.

### Scenarios
- **Personal Work & Study**: Provides real-time help based on historical memory and user preferences.
- **Video Conferences**: Automatically extracts key discussion points and correlates them with historical content.
- **Tutorial Learning**: Offers on-the-spot answers and generates personalized learning paths for better efficiency.
- **Entertainment**: Suggests strategies or content, enhancing user immersion with personalized content recommendations.
- **Automated Tool Usage**: Enables automated tool activation based on memory-based preference mapping, optimizing task performance.

## Architecture Overview

- **Client-Side**: Built with Cherry Studio for lightweight, CPU-efficient operation (Windows 10 and above).
- **Backend**: Distributed vLLM cluster supporting horizontal scaling for real-time inference, with encrypted data transfer and local storage desensitization.
- **Memory Storage**: Uses a combination of MySQL for timestamp-based storage and BGE-M3 for vector-based memory, optimized for redundancy reduction and efficient retrieval.

### Core Components:
1. **Screenshot Module**: Captures user screen activity every 5 seconds and stores them with timestamped filenames.
2. **Data Transfer Module**: Securely transfers captured screenshots to the server for processing.
3. **Multi-modal Parsing Service**: Uses vLLM models to analyze visual and textual data from screenshots.
4. **Memory Storage**: A hybrid memory structure using raw detail storage, vector-based memory, and user preference graphs.
5. **Decision Logic Layer (MCP)**: Integrates user queries with memory data to provide adaptive, real-time responses based on historical data and context.

## Security & Privacy

- **Data Encryption**: End-to-end encryption (AES-256) for data transmission; sensitive data is desensitized locally.
- **User Privacy**: Supports granular user authorization, allowing users to control specific monitoring contexts.
- **Local Data Processing**: Ensures sensitive data remains local for processing, complying with privacy regulations.

## Deployment & Scalability

- **Client**: A lightweight MCP client with minimal CPU usage, designed for scalability on Windows systems.
- **Server**: Supports GPU-accelerated vLLM models and scalable architecture using Kubernetes for horizontal scaling.
- **Extensibility**: The system supports future enhancements like federated learning for privacy-preserving preference modeling and cross-platform support.

## Market Potential & Business Model

### Revenue Streams:
1. **B2C Subscription**: Free tier (basic functionality) and Pro tier ($9.9/month) with advanced features like cross-device memory synchronization and encrypted enterprise-level storage.
2. **B2B Enterprise Suite**: $15/user/month for team-based memory sharing, integration with tools like Slack/Teams, and audit logging.
3. **Data Services**: Anonymous user behavior analytics with GDPR-compliant data handling.

### Future Plans:
- **Phase 1 (0-3 months)**: MVP development with core functionalities and internal testing.
- **Phase 2 (4-6 months)**: Performance optimization, elastic scaling, and enterprise-level deployment.
- **Phase 3 (7-12 months)**: Full-scale deployment with compliance certifications and cross-cloud support.

## Contribution

Contributions to OmniMate are welcome! If you'd like to report an issue or suggest a feature, feel free to open a pull request or an issue.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For any inquiries or feedback, please contact [email@example.com].
