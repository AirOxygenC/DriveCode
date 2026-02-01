"use client"

import { useState, useEffect } from "react"
import { LoginScreen } from "@/components/voice-loop/login-screen"
import { CallbackScreen } from "@/components/voice-loop/callback-screen"
import { Dashboard } from "@/components/voice-loop/dashboard"
import { VoiceInterface } from "@/components/voice-loop/voice-interface"

type Screen = "login" | "callback" | "dashboard" | "voice"

interface Repo {
  id: number
  name: string
  full_name: string
  private: boolean
  language: string | null
  updated_at: string
}

export default function VoiceLoopApp() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("login")
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  // Check for token on mount (callback handling)
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const tokenParam = searchParams.get("token")
    if (tokenParam) {
      setToken(tokenParam)
      setIsAuthenticated(true)
      setCurrentScreen("dashboard")
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  const handleLogin = () => {
    // Redirect to backend for GitHub OAuth
    window.location.href = "http://localhost:5000/auth/github/login"
  }

  const handleSelectRepo = (repo: Repo) => {
    setSelectedRepo(repo)
  }

  const handleStartCoding = () => {
    if (selectedRepo) {
      setCurrentScreen("voice")
    }
  }

  const handleBack = () => {
    setCurrentScreen("dashboard")
  }

  const handleSignOut = () => {
    setIsAuthenticated(false)
    setSelectedRepo(null)
    setCurrentScreen("login")
  }

  if (currentScreen === "login") {
    return <LoginScreen onLogin={handleLogin} />
  }

  if (currentScreen === "callback") {
    return <CallbackScreen />
  }

  if (currentScreen === "voice" && selectedRepo) {
    return <VoiceInterface selectedRepo={selectedRepo} onBack={handleBack} token={token} />
  }

  return (
    <Dashboard
      onSelectRepo={handleSelectRepo}
      selectedRepo={selectedRepo}
      onStartCoding={handleStartCoding}
      onSignOut={handleSignOut}
      token={token}
    />
  )
}
