"use client"

import { useState } from "react"
import { LoginScreen } from "@/components/voice-loop/login-screen"
import { CallbackScreen } from "@/components/voice-loop/callback-screen"
import { Dashboard } from "@/components/voice-loop/dashboard"
import { VoiceInterface } from "@/components/voice-loop/voice-interface"

type Screen = "login" | "callback" | "dashboard" | "voice"

interface Repo {
  id: number
  name: string
  private: boolean
  language: string | null
  updated_at: string
}

export default function VoiceLoopApp() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("login")
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const handleLogin = () => {
    setCurrentScreen("callback")
    // Simulate authentication
    setTimeout(() => {
      setIsAuthenticated(true)
      setCurrentScreen("dashboard")
    }, 2000)
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
    return <VoiceInterface selectedRepo={selectedRepo} onBack={handleBack} />
  }

  return (
    <Dashboard
      onSelectRepo={handleSelectRepo}
      selectedRepo={selectedRepo}
      onStartCoding={handleStartCoding}
      onSignOut={handleSignOut}
    />
  )
}
