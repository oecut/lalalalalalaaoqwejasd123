# Overview

This is a high-performance Telegram bot called "errorer bot" built with aiogram 3.x designed to handle 100k+ users simultaneously. The bot provides AI-powered responses using multiple AI providers through the G4F (GPT4Free) library, offering free access to various AI models. It features comprehensive user management, custom response styles, demo systems, and administrative controls with full Russian localization.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework and Performance
- **Bot Framework**: Built on aiogram 3.13.1 with async/await patterns for maximum concurrency
- **Performance Optimization**: Designed for 100k+ concurrent users with connection pooling, WAL mode SQLite, and memory-based FSM storage
- **Caching Strategy**: Multi-level caching with TTLCache for throttling and simple memory cache for frequent responses
- **Connection Management**: Persistent database connections with connection pooling to reduce overhead

## Database Architecture
- **Storage**: SQLite with aiosqlite for async operations
- **Performance Tuning**: WAL journal mode, optimized cache size (10000), and memory-based temporary storage
- **Schema Design**: Supports users, groups, request limits, response styles, demo triggers, and comprehensive analytics
- **Data Persistence**: User preferences, daily request limits, custom AI response styles per user/group

## AI Integration and Response Generation
- **AI Provider**: G4F (GPT4Free) library for accessing multiple AI models without API costs
- **Provider Strategy**: Multi-provider fallback system with speed-optimized provider selection (Blackbox, DeepSeek, etc.)
- **Response Processing**: Custom HTML formatting for Telegram with support for markdown-to-HTML conversion
- **Performance**: Ultra-fast response generation with parallel provider testing and automatic failover

## Message Processing Architecture
- **Handler Routing**: Separate routers for private messages, group messages, business messages, admin commands, and user interactions
- **Command Processing**: Supports `.ai` and `.ии` commands in both private and group chats
- **Context Awareness**: Reply-to-message support with quoted context for better AI understanding
- **Rate Limiting**: Throttling middleware with TTL cache to prevent spam and manage resource usage

## User Experience Features
- **Personalization**: Custom response styles per user and per group chat
- **Localization**: Full Russian language support with high-quality localized messages
- **Demo System**: Admin-configurable demo triggers with animated responses for showcasing capabilities
- **Analytics**: Comprehensive user statistics tracking daily/total usage patterns

## Administrative Controls
- **Admin Panel**: Complete admin interface with broadcast capabilities, user management, and system monitoring
- **Broadcasting**: Support for both private message and group chat broadcasting with message formatting preservation
- **Demo Management**: Animated and simple demo trigger systems for user engagement
- **Access Control**: Admin-only functions with proper permission checking

## Scalability and Reliability
- **Async Architecture**: Full async/await implementation for non-blocking operations
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Resource Management**: Optimized thread pool executor (20 workers) for AI generation tasks
- **Memory Efficiency**: MemoryStorage for FSM states and optimized database connection pooling

# External Dependencies

## AI Services
- **G4F (GPT4Free)**: Primary AI provider offering free access to multiple models including GPT, Claude, and other LLMs
- **Transformers**: HuggingFace transformers library for potential local model support
- **Datasets**: HuggingFace datasets library for training data integration

## Telegram Integration
- **aiogram 3.13.1**: Modern async Telegram Bot API framework
- **Business Messages**: Support for Telegram Business account integration

## Database and Storage
- **SQLite with aiosqlite**: Async SQLite operations for high-performance data persistence
- **No external database dependencies**: Self-contained with optimized SQLite configuration

## HTTP and Networking
- **aiohttp**: Async HTTP client for API requests
- **httpx**: Alternative HTTP client for improved performance
- **No external API keys required**: Uses free AI providers through G4F

## Performance Libraries
- **uvloop**: High-performance event loop for Unix systems
- **orjson**: Fast JSON serialization for improved performance
- **cachetools**: TTL cache implementation for rate limiting

## Development and Monitoring
- **loguru**: Advanced logging system for debugging and monitoring
- **python-dateutil**: Date and time utilities for analytics
- **typing-extensions**: Enhanced type hints for better code quality

## Optional Enhancements
- **Pillow**: Image processing capabilities for potential multimodal features
- **torch**: PyTorch for advanced AI model support
- **tokenizers**: Text tokenization for AI model integration