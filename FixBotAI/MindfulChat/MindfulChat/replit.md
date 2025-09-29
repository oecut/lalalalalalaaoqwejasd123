# Overview

This is a high-performance Telegram bot built with aiogram 3.x called "errorer bot" designed to handle 100k+ users simultaneously. The bot provides AI-powered responses using multiple AI providers through the G4F (GPT4Free) library, with features including personalized response styles, admin controls, group chat support, business message handling, and sophisticated caching for optimal performance.

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
- **Monitoring**: Built-in logging and error tracking for system health monitoring

# External Dependencies

## Core Telegram Bot Framework
- **aiogram**: Version 3.13.1 for Telegram Bot API integration
- **aiosqlite**: Version 0.20.0 for async SQLite database operations

## AI and Machine Learning
- **g4f**: Version >=0.3.5.8 for free access to multiple AI providers (GPT, Claude, etc.)
- **transformers**: Version >=4.40.0 for potential local model support
- **datasets**: Version >=2.18.0 for dataset integration capabilities
- **torch**: Version >=2.0.0 for machine learning model support
- **huggingface-hub**: Version >=0.20.0 for HuggingFace model access

## HTTP and Network
- **aiohttp**: Version 3.10.10 for async HTTP client operations
- **httpx**: Version 0.27.0 for alternative HTTP client with better async support

## Performance and Utilities
- **uvloop**: Version >=0.19.0 for high-performance event loop (Unix only)
- **orjson**: Version >=3.9.0 for fast JSON serialization
- **cachetools**: For in-memory caching with TTL support
- **loguru**: Version >=0.7.0 for advanced logging capabilities

## Image Processing
- **Pillow**: Version >=10.0.0 for image processing capabilities (LLaVA integration)

## Configuration Management
- **python-dateutil**: Version >=2.8.2 for date/time utilities
- **typing-extensions**: Version >=4.9.0 for enhanced type hints

The system is designed to be deployed on Replit with environment variable configuration for the BOT_TOKEN, ensuring secure credential management without hardcoded secrets.