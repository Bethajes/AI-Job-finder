# Ethiopian Jobs — Mobile App

React Native (Expo) client for the Ethiopian Job Platform. Week 9 MVP: app
foundation with authentication.

## Tech Stack

- **Expo SDK 57** (React Native 0.86, TypeScript strict)
- **React Navigation 7** — native stack (auth flow) + bottom tabs (main flow)
- **Zustand** (persisted to AsyncStorage) — auth state
- **TanStack React Query v5** — server state (jobs, profile)
- **Axios** with request/response interceptors and automatic token refresh
- **React Hook Form + Yup** — validated forms
- **expo-secure-store** — JWT storage on iOS/Android (AsyncStorage on web)
- **expo-splash-screen + Inter font** — controlled startup experience

## Getting Started

```bash
cd ethiopian-jobs-mobile
npm install
cp .env.example .env   # point EXPO_PUBLIC_API_URL at your backend
npx expo start
```

Press `i` for the iOS simulator, `a` for the Android emulator, or scan the QR
code with Expo Go.

### Connecting to the backend

- The FastAPI backend defaults to `http://localhost:8000/api/v1`.
- **iOS simulator**: `localhost` works out of the box.
- **Android emulator**: use `http://10.0.2.2:8000/api/v1` in `.env`.
- **Physical device**: use your machine's LAN IP, e.g.
  `http://192.168.1.10:8000/api/v1`, and start the backend with
  `uvicorn app.main:app --reload --host 0.0.0.0`.

## Project Structure

```
ethiopian-jobs-mobile/
├── App.tsx                    # Root: providers + navigation gate
├── index.js                   # Expo entry point
├── app.json                   # Expo config
└── src/
    ├── api/                   # Axios client + auth/jobs endpoints
    ├── components/
    │   ├── common/            # Button, Input, Loading
    │   ├── auth/              # LoginForm, RegisterForm
    │   └── jobs/              # JobCard
    ├── navigation/            # AppNavigator, AuthStack, MainTabs, types
    ├── screens/
    │   ├── SplashScreen.tsx
    │   ├── auth/              # LoginScreen, RegisterScreen
    │   └── main/              # Home, Jobs, Applications, Profile
    ├── store/                 # Zustand authStore (persisted)
    ├── hooks/                 # useAuth, useApi (React Query)
    ├── utils/                 # storage, validators, errors, format
    ├── config/                # Environment variables
    ├── constants/             # Theme tokens
    └── types/                 # Shared TypeScript types
```

## Authentication Flow

1. On launch, the native splash is held while fonts load and
   `restoreSession()` runs.
2. `restoreSession()` reads the stored access token; if present it calls
   `/auth/me`. A valid token → Main tabs. A 401 → one silent refresh attempt,
   then login screen. A network failure falls back to the cached user so the
   app still opens offline.
3. Login/register receive a `TokenResponse`; `/auth/me` then hydrates the user
   (the API returns only tokens from these endpoints).
4. Access/refresh tokens live in `SecureStore` (native). The axios response
   interceptor retries any 401 once through `/auth/refresh`
   (single-flight), and clears the session if refresh fails.
5. Logout calls `/auth/logout`, wipes storage, and the root navigator swaps
   back to the auth stack automatically.

## Scripts

```bash
npm run ios        # run on iOS simulator
npm run android    # run on Android emulator
npm run web        # run in browser
npx tsc --noEmit   # type-check
```
