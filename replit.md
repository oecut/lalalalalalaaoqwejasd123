# Overview

CyberGram is a modified version of Telegram for Android with enhanced privacy features. This is a native Android application built from the official Telegram source code, customized with additional anonymity and security functionality accessible through a "Cyber Sec" menu option in the side drawer.

The project is built using Android Studio and requires valid Telegram API credentials (APP_ID and APP_HASH) to function. It maintains compatibility with the Telegram protocol while adding custom privacy-focused features on top of the standard messaging capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Platform Architecture

**Problem**: Building a secure messaging application for Android with custom privacy features  
**Solution**: Fork and modify the official Telegram Android client to add privacy-focused functionality  
**Rationale**: Leveraging Telegram's mature, battle-tested codebase reduces development time and provides a solid foundation for security features

The application is a native Android app written primarily in Java/C++ with the following layers:

- **Presentation Layer**: Android Activities and Fragments for UI
- **Business Logic**: Custom privacy features integrated into Telegram's messaging core
- **Native Layer**: JNI-based C/C++ libraries for cryptography, media processing, and performance-critical operations
- **Network Layer**: Telegram MTProto protocol implementation

## Build System

**Problem**: Managing complex native dependencies across multiple architectures  
**Solution**: CMake-based build system with pre-configured toolchains for Android ABIs  
**Rationale**: CMake provides cross-platform build support and integrates well with Android NDK

The project uses:
- Gradle for Android application build orchestration
- CMake for native library compilation (BoringSSL, FFmpeg, VoIP components)
- Multiple build variants (standard app, HockeyApp, Huawei, standalone)

## Native Dependencies

All native libraries are built from source using the JNI layer, with separate builds for each Android ABI (armeabi-v7a, arm64-v8a, x86, x86_64).

## Custom Modifications

**Problem**: Adding privacy features without breaking Telegram compatibility  
**Solution**: Inject custom UI elements and functionality into existing Telegram screens  
**Approach**:
- Add "Cyber Sec" menu item to side drawer
- Create dedicated privacy settings screen
- Preserve all standard Telegram functionality

# External Dependencies

## Telegram API Integration

- **Service**: Telegram API (my.telegram.org)
- **Purpose**: Authentication and message routing
- **Configuration**: Requires APP_ID and APP_HASH credentials configured in BuildVars.java
- **Authentication**: Standard Telegram OAuth flow

## Firebase Services

- **Service**: Firebase Cloud Messaging (FCM)
- **Purpose**: Push notifications
- **Configuration**: google-services.json files for different build variants
- **Project ID**: tmessages2

## Huawei Mobile Services (HMS)

- **Service**: Huawei AppGallery Connect
- **Purpose**: Push notifications for Huawei devices without Google Play Services
- **Configuration**: agconnect-services.json
- **App ID**: 101184875

## Native Cryptography Libraries

- **BoringSSL**: TLS/SSL and cryptographic primitives
- **FFmpeg**: Video/audio encoding and decoding
- **libsrtp**: Secure Real-time Transport Protocol for VoIP
- **OpenH264**: H.264 video codec
- **Opus**: Audio codec for voice messages
- **libwebp/mozjpeg**: Image processing

## VoIP Components

- **libtgvoip**: Telegram's VoIP implementation
- **tgcalls**: Group voice/video call support
- **rnnoise**: Noise suppression for audio

## Post-Quantum Cryptography

- **ML-KEM (Kyber)**: Quantum-resistant key encapsulation
- **ML-DSA**: Quantum-resistant digital signatures
- **Purpose**: Future-proofing against quantum computing threats

## Other Media Libraries

- **ExoPlayer/FLAC**: Audio playback
- **libvpx/dav1d**: Video codec support (VP8/VP9/AV1)
- **PFFFT**: Fast Fourier Transform for audio processing